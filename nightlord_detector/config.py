"""Persisted ROI and overlay layout so tuned values can become the defaults."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .paths import user_config_dir


CONFIG_PATH = user_config_dir() / "config.json"


@dataclass
class OverlayLayout:
    # Bottom-center anchor. x_offset shifts left/right. margin_bottom is the gap
    # from the physical screen edge — keep this tiny so the box sits under the
    # Nightreign boss plate instead of over the class name / party roster.
    x_offset: int = 0
    margin_bottom: int = 8
    width: int = 720
    height: int = 64


@dataclass
class AppConfig:
    roi_left: float = 0.28
    roi_top: float = 0.04
    roi_width: float = 0.44
    roi_height: float = 0.10
    overlay: OverlayLayout | None = None
    language: str = "en"

    def __post_init__(self) -> None:
        if self.overlay is None:
            self.overlay = OverlayLayout()
        elif isinstance(self.overlay, dict):
            self.overlay = OverlayLayout(**self.overlay)


def compute_overlay_rect(
    screen_w: int,
    screen_h: int,
    layout: OverlayLayout,
) -> tuple[int, int, int, int]:
    """Return (x, y, width, height) pinned to the bottom-center strip."""
    width = max(240, int(layout.width))
    height = max(40, int(layout.height))
    x = (screen_w - width) // 2 + int(layout.x_offset)
    y = screen_h - height - max(0, int(layout.margin_bottom))
    x = max(0, min(x, max(0, screen_w - width)))
    y = max(0, min(y, max(0, screen_h - height)))
    return x, y, width, height


def compute_roi_rect(
    screen_w: int,
    screen_h: int,
    left: float,
    top: float,
    width: float,
    height: float,
    monitor_left: int = 0,
    monitor_top: int = 0,
) -> tuple[int, int, int, int]:
    """Return the capture rectangle in pixels. Matches capture.Roi.to_pixels."""
    screen_w = max(1, int(screen_w))
    screen_h = max(1, int(screen_h))
    x = monitor_left + int(screen_w * float(left))
    y = monitor_top + int(screen_h * float(top))
    w = max(32, int(screen_w * float(width)))
    h = max(16, int(screen_h * float(height)))
    x = max(monitor_left, min(x, monitor_left + screen_w - 1))
    y = max(monitor_top, min(y, monitor_top + screen_h - 1))
    w = max(1, min(w, monitor_left + screen_w - x))
    h = max(1, min(h, monitor_top + screen_h - y))
    return x, y, w, h


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
        "language": cfg.language,
    }
    CONFIG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return CONFIG_PATH
