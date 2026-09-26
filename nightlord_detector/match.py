"""Fuzzy match OCR text against the nightlord.app Night 1 / Night 2 lists only."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz import fuzz

from .predict import load_tables


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class BossMatch:
    night: int
    key: str
    label: str
    alias: str
    score: float
    raw: str


def _catalog() -> list[tuple[int, str, str, str, str]]:
    tables = load_tables()
    rows: list[tuple[int, str, str, str, str]] = []
    for night, section in ((1, "night1"), (2, "night2")):
        for key, entry in tables[section].items():
            for alias in entry["aliases"]:
                rows.append((night, key, entry["label"], alias, normalize(alias)))
    return rows


def match_boss(raw_text: str, min_score: float = 78.0) -> BossMatch | None:
    cleaned = normalize(raw_text)
    if len(cleaned) < 2:
        return None

    # Disambiguate overlapping nameplates before fuzzy scoring.
    if "draconic" in cleaned:
        return BossMatch(2, "draconic", "Draconic Tree Sentinel & Royal Cavalrymen", "Draconic Tree Sentinel", 100.0, raw_text)
    if "fallingstar" in cleaned or "falling star" in cleaned:
        return BossMatch(2, "fallingstar", "Full-Grown Fallingstar Beast", "Fallingstar Beast", 100.0, raw_text)

    best: BossMatch | None = None
    for night, key, label, alias, alias_norm in _catalog():
        if not alias_norm:
            continue
        if alias_norm in cleaned or cleaned in alias_norm:
            score = 100.0 + min(len(alias_norm), 20) / 100.0
        else:
            score = float(
                max(
                    fuzz.token_set_ratio(cleaned, alias_norm),
                    fuzz.partial_ratio(cleaned, alias_norm),
                )
            )
        if best is None or score > best.score:
            best = BossMatch(night, key, label, alias, min(score, 100.0), raw_text)
    if best is None or best.score < min_score:
        return None
    return best


def rank_bosses(raw_text: str, limit: int = 8) -> list[BossMatch]:
    cleaned = normalize(raw_text)
    ranked: list[BossMatch] = []
    for night, key, label, alias, alias_norm in _catalog():
        score = float(max(fuzz.token_set_ratio(cleaned, alias_norm), fuzz.partial_ratio(cleaned, alias_norm)))
        ranked.append(BossMatch(night, key, label, alias, score, raw_text))
    ranked.sort(key=lambda m: m.score, reverse=True)
    deduped: list[BossMatch] = []
    seen: set[tuple[int, str]] = set()
    for row in ranked:
        ident = (row.night, row.key)
        if ident in seen:
            continue
        seen.add(ident)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    return deduped
