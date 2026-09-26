"""Screen capture and OCR. External pixels only — no game process access."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import mss
from PIL import Image, ImageFilter, ImageOps

from .paths import resource_path

log = logging.getLogger("nightlord-detector")


def configure_tesseract() -> Path | None:
    """Prefer a Tesseract shipped next to the EXE, then a system install."""
    exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else None
    candidates = [
        resource_path("resources", "Tesseract-OCR", "tesseract.exe"),
        *(
            [
                exe_dir / "Tesseract-OCR" / "tesseract.exe",
                exe_dir / "tesseract.exe",
            ]
            if exe_dir
            else []
        ),
        Path(os.environ.get("TESSERACT_PATH", "")),
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    try:
        import pytesseract
    except Exception:
        return None

    for path in candidates:
        if path and path.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(path)
            tessdata = path.parent / "tessdata"
            if tessdata.is_dir():
                os.environ.setdefault("TESSDATA_PREFIX", str(tessdata))
            return path
    return None


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


def ocr_image(image: Image.Image, lang: str | None = None) -> tuple[str, str]:
    from .i18n import tess_lang, uses_latin_ocr

    processed = preprocess(image)
    configure_tesseract()
    tess = lang or tess_lang()
    try:
        import pytesseract

        last_exc: Exception | None = None
        for candidate in (tess, "eng"):
            try:
                if uses_latin_ocr() and candidate == "eng":
                    config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'&- "
                else:
                    config = "--psm 7"
                text = pytesseract.image_to_string(processed, lang=candidate, config=config)
                return "tesseract", " ".join(text.split())
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
        log.debug("Tesseract unavailable: %s", last_exc)
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
