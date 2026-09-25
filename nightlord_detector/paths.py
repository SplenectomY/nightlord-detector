"""Resolve data files for source runs and PyInstaller one-file builds."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    return project_root().joinpath(*parts)


def user_config_dir() -> Path:
    local = Path.home() / "AppData" / "Local" / "nightlord-detector"
    local.mkdir(parents=True, exist_ok=True)
    return local
