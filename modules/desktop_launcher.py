"""No-console desktop launcher helpers for Deep Live Cam Studio."""

from __future__ import annotations

import ctypes
from datetime import datetime
import importlib
import os
import sys
import traceback
from pathlib import Path
from typing import TextIO


def project_root() -> Path:
    from modules.paths import install_root
    return install_root()


def desktop_log_path(root: Path | None = None) -> Path:
    from modules.paths import is_frozen, runtime_dir
    if root is not None and not is_frozen():
        return root / "runtime" / "desktop-launch.log"
    return runtime_dir() / "desktop-launch.log"


def prepare_desktop_environment(root: Path | None = None) -> Path:
    root = root or project_root()
    os.chdir(root)
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    os.environ["PATH"] = root_text + os.pathsep + os.environ.get("PATH", "")
    return root


def redirect_desktop_output(log_path: Path) -> TextIO:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stream = log_path.open("a", encoding="utf-8", buffering=1)
    print(
        f"\n--- Deep Live Cam Studio desktop launch "
        f"{datetime.now().isoformat(timespec='seconds')} ---",
        file=stream,
    )
    sys.stdout = stream
    sys.stderr = stream
    return stream


def log_startup_step(message: str) -> None:
    print(
        f"[desktop-launch] {datetime.now().isoformat(timespec='seconds')} {message}",
        flush=True,
    )


def launch() -> None:
    root = prepare_desktop_environment()
    log_path = desktop_log_path(root)
    redirect_desktop_output(log_path)

    try:
        log_startup_step(f"executable={sys.executable}")
        log_startup_step(f"install_root={root}")
        log_startup_step(f"argv={sys.argv}")
        log_startup_step("importing run module")
        run_module = importlib.import_module("run")
        log_startup_step("starting core.run")
        run_module.core.run()
        log_startup_step("core.run returned")
    except Exception as exc:  # pragma: no cover - defensive desktop UX path
        traceback.print_exc()
        _show_error_dialog(log_path, exc)


def _show_error_dialog(log_path: Path, exc: Exception) -> None:
    if sys.platform != "win32":
        return
    message = (
        "Deep Live Cam Studio could not start.\n\n"
        f"{type(exc).__name__}: {exc}\n\n"
        f"Details were written to:\n{log_path}"
    )
    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            message,
            "Deep Live Cam Studio",
            0x10,
        )
    except Exception:
        pass
