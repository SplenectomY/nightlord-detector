"""Deep of Night Nightlord predictor using nightlord.app tables."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from .paths import resource_path


DATA_PATH = resource_path("data", "nightlord_tables.json")


@lru_cache(maxsize=1)
def load_tables() -> dict[str, Any]:
    with DATA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


@dataclass(frozen=True)
class NightlordGuess:
    key: str
    name: str
    expedition: str
    weakness: str
    pct: float
    regular_pct: float
    everdark_pct: float


@dataclass(frozen=True)
class Prediction:
    night1_key: str | None
    night2_key: str | None
    depth: str
    guesses: tuple[NightlordGuess, ...]
    locked: bool
    message: str


def _weight(mapping: dict[str, float] | None, expedition_key: str) -> float:
    if mapping is None:
        return 1.0
    return float(mapping.get(expedition_key, 0.0))


def _lord_map(section: dict[str, Any], key: str | None) -> dict[str, float] | None:
    if not key:
        return None
    entry = section.get(key)
    if not entry:
        return None
    return {lord: 1.0 for lord in entry["lords"]}


def predict(
    night1_key: str | None,
    night2_key: str | None = None,
    depth: str = "any",
) -> Prediction:
    tables = load_tables()
    if not night1_key:
        return Prediction(None, night2_key, depth, (), False, "Waiting for a Night 1 boss.")

    n1 = tables["night1"].get(night1_key)
    if not n1:
        return Prediction(night1_key, night2_key, depth, (), False, f"Unknown Night 1 key: {night1_key}")

    if night2_key and night2_key not in tables["night2"]:
        return Prediction(night1_key, night2_key, depth, (), False, f"Unknown Night 2 key: {night2_key}")

    n1map = _lord_map(tables["night1"], night1_key)
    n2map = _lord_map(tables["night2"], night2_key)
    priors = tables["priors"].get(depth) or tables["priors"]["any"]

    scores: dict[str, float] = {}
    total = 0.0
    for key in tables["score_keys"]:
        base_key = key.removeprefix("es_")
        score = priors.get(key, 0.0) * _weight(n1map, base_key) * _weight(n2map, base_key)
        scores[key] = score
        total += score

    grouped: dict[str, dict[str, float]] = {}
    for key, score in scores.items():
        if score <= 0:
            continue
        base_key = key.removeprefix("es_")
        bucket = grouped.setdefault(base_key, {"score": 0.0, "regular": 0.0, "everdark": 0.0})
        bucket["score"] += score
        if key.startswith("es_"):
            bucket["everdark"] += score
        else:
            bucket["regular"] += score

    if total <= 0 or not grouped:
        return Prediction(
            night1_key,
            night2_key,
            depth,
            (),
            False,
            "No valid Nightlord shares that Night 1 / Night 2 pair.",
        )

    guesses: list[NightlordGuess] = []
    for base_key, bucket in grouped.items():
        info = tables["expeditions"][base_key]
        guesses.append(
            NightlordGuess(
                key=base_key,
                name=info["name"],
                expedition=info["expedition"],
                weakness=info.get("weakness") or "",
                pct=100.0 * bucket["score"] / total,
                regular_pct=100.0 * bucket["regular"] / total,
                everdark_pct=100.0 * bucket["everdark"] / total,
            )
        )
    guesses.sort(key=lambda g: g.pct, reverse=True)
    locked = len(guesses) == 1 or abs(guesses[0].pct - 100.0) < 0.1
    label_n1 = n1["label"]
    label_n2 = tables["night2"][night2_key]["label"] if night2_key else "not seen yet"
    if locked:
        message = f"Locked: {guesses[0].name}  ({label_n1} / {label_n2})"
    else:
        message = f"{len(guesses)} possible Nightlords from {label_n1} / {label_n2}"
    return Prediction(night1_key, night2_key, depth, tuple(guesses), locked, message)


def format_overlay(prediction: Prediction, max_rows: int = 6) -> str:
    from .i18n import lord_name, t, weakness_name

    if not prediction.night1_key:
        return f"{t('overlay.header')}\n{t('overlay.waiting')}"
    if not prediction.guesses:
        return prediction.message
    lines = [t("overlay.header")]
    for guess in prediction.guesses[:max_rows]:
        name = lord_name(guess.key, guess.name)
        extra = ""
        if guess.weakness:
            extra = f"  [{weakness_name(guess.weakness)}]"
        ed = ""
        if guess.everdark_pct > 0 and guess.regular_pct > 0:
            ed = f"  (ED {guess.everdark_pct:.0f}%)"
        elif guess.everdark_pct > 0 and guess.regular_pct <= 0:
            ed = f"  ({t('overlay.everdark')})"
        lines.append(f"{guess.pct:5.1f}%  {name}{extra}{ed}")
    if prediction.locked:
        lines[0] = t("overlay.nightlord", name=lord_name(prediction.guesses[0].key, prediction.guesses[0].name))
    return "\n".join(lines)
