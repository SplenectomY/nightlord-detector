"""Screen capture and OCR. External pixels only — no game process access."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import mss
import numpy as np
from PIL import Image, ImageFilter, ImageOps

log = logging.getLogger("nightlord-detector")


@dataclass
class Roi:
    left: float = 0.28
    top: float = 0.04
    width: float = 0.44
    height: float = 0.10

    def to_pixels(self, monitor: dict) -> dict[str, int]:
        w = int(monitor["width"])
        h = int(monitor["height"])
        left = monitor["left"] + int(w * self.left)
        top = monitor["top"] + int(h * self.top)
        width = max(32, int(w * self.width))
        height = max(16, int(h * self.height))
        return {"left": left, "top": top, "width": width, "height": height}


def grab_roi(roi: Roi, monitor_index: int = 1) -> Image.Image:
    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index >= len(monitors):
            monitor_index = 1
        region = roi.to_pixels(monitors[monitor_index])
        raw = sct.grab(region)
        return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")


def preprocess(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    gray = gray.resize((gray.width * 2, gray.height * 2), Image.Resampling.LANCZOS)
    gray = gray.point(lambda p: 255 if p > 150 else 0)
    return gray.filter(ImageFilter.SHARPEN)


def ocr_image(image: Image.Image) -> tuple[str, str]:
    processed = preprocess(image)
    try:
        import pytesseract

        text = pytesseract.image_to_string(
            processed,
            config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'&- ",
        )
        return "tesseract", " ".join(text.split())
    except Exception as exc:  # noqa: BLE001
        log.debug("Tesseract unavailable: %s", exc)

    try:
        from winocr import recognize_pil_sync

        result = recognize_pil_sync(image)
        text = getattr(result, "text", None) or str(result)
        return "winocr", " ".join(str(text).split())
    except Exception as exc:  # noqa: BLE001
        log.debug("winocr unavailable: %s", exc)

    return "none", ""


def crop_preview_array(image: Image.Image) -> np.ndarray:
    return np.array(image)
