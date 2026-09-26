"""UI and overlay strings. Locale JSON lives under locales/."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from .paths import resource_path

# Nightreign-supported languages, native labels for the picker.
LOCALES: tuple[tuple[str, str], ...] = (
    ("en", "English"),
    ("ja", "日本語"),
    ("zh-Hans", "简体中文"),
    ("zh-Hant", "繁體中文"),
    ("ko", "한국어"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("es", "Español"),
    ("it", "Italiano"),
    ("pt-BR", "Português (Brasil)"),
    ("pl", "Polski"),
    ("ru", "Русский"),
)

TESS_LANG = {
    "en": "eng",
    "ja": "jpn",
    "zh-Hans": "chi_sim",
    "zh-Hant": "chi_tra",
    "ko": "kor",
    "fr": "fra",
    "de": "deu",
    "es": "spa",
    "it": "ita",
    "pt-BR": "por",
    "pl": "pol",
    "ru": "rus",
}

LATIN_LOCALES = {"en", "fr", "de", "es", "it", "pt-BR", "pl"}

_current = "en"
_bundle: dict[str, str] = {}


def locale_label(code: str) -> str:
    for item_code, label in LOCALES:
        if item_code == code:
            return label
    return code


def tess_lang(code: str | None = None) -> str:
    return TESS_LANG.get(code or _current, "eng")


def uses_latin_ocr(code: str | None = None) -> bool:
    return (code or _current) in LATIN_LOCALES


@lru_cache(maxsize=16)
def _load(code: str) -> dict[str, str]:
    path = resource_path("locales", f"{code}.json")
    if not path.is_file():
        if code != "en":
            return _load("en")
        return {}
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in raw.items()}


def set_locale(code: str) -> str:
    global _current, _bundle
    valid = {item[0] for item in LOCALES}
    _current = code if code in valid else "en"
    _bundle = _load(_current)
    return _current


def current_locale() -> str:
    return _current


def t(key: str, **kwargs: object) -> str:
    text = _bundle.get(key)
    if text is None:
        text = _load("en").get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def lord_name(key: str, fallback: str) -> str:
    return t(f"lord.{key}") if t(f"lord.{key}") != f"lord.{key}" else fallback


def expedition_name(key: str, fallback: str) -> str:
    return t(f"expedition.{key}") if t(f"expedition.{key}") != f"expedition.{key}" else fallback


def weakness_name(value: str) -> str:
    if not value:
        return ""
    mapped = t(f"weak.{value.lower()}")
    return mapped if mapped != f"weak.{value.lower()}" else value
