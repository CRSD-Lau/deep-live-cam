"""Shared path helpers for development and packaged builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "DeepLiveCamStudio"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def install_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return resource_root()


def user_data_dir() -> Path:
    override = os.environ.get("DLC_APP_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / APP_DIR_NAME


def models_dir() -> Path:
    override = os.environ.get("DLC_MODELS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if is_frozen():
        return user_data_dir() / "models"
    return resource_root() / "models"


def runtime_dir() -> Path:
    if is_frozen():
        return user_data_dir() / "logs"
    return resource_root() / "runtime"


ROOT_DIR = str(resource_root())
INSTALL_ROOT = str(install_root())
USER_DATA_DIR = str(user_data_dir())
MODELS_DIR = str(models_dir())
RUNTIME_DIR = str(runtime_dir())
