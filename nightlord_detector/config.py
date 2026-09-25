"""Persisted ROI and overlay layout so tuned values can become the defaults."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .paths import user_config_dir


CONFIG_PATH = user_config_dir() / "config.json"


@dataclass
class OverlayLayout:
    x_offset: int = 0
    margin_bottom: int = 10
    width: int = 640
    height: int = 108


@dataclass
class AppConfig:
    roi_left: float = 0.28
    roi_top: float = 0.04
    roi_width: float = 0.44
    roi_height: float = 0.10
    overlay: OverlayLayout | None = None

    def __post_init__(self) -> None:
        if self.overlay is None:
            self.overlay = OverlayLayout()
        elif isinstance(self.overlay, dict):
            self.overlay = OverlayLayout(**self.overlay)


def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        return AppConfig()
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        overlay = raw.pop("overlay", None)
        cfg = AppConfig(**{k: v for k, v in raw.items() if k in AppConfig.__dataclass_fields__})
        if overlay:
            cfg.overlay = OverlayLayout(**overlay)
        return cfg
    except Exception:
        return AppConfig()


def save_config(cfg: AppConfig) -> Path:
    payload = {
        "roi_left": cfg.roi_left,
        "roi_top": cfg.roi_top,
        "roi_width": cfg.roi_width,
        "roi_height": cfg.roi_height,
        "overlay": asdict(cfg.overlay or OverlayLayout()),
    }
    CONFIG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return CONFIG_PATH
