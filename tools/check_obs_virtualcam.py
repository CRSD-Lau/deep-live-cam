#!/usr/bin/env python3
"""Test pyvirtualcam output and show likely OBS/DirectShow devices."""

from __future__ import annotations

import argparse
import os
import platform
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def positive_int(value: str) -> int:
    try:
        integer = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value} is not an integer") from exc
    if integer < 1:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return integer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help='virtual camera name, for example "OBS Virtual Camera"')
    parser.add_argument("--width", type=positive_int, default=1280)
    parser.add_argument("--height", type=positive_int, default=720)
    parser.add_argument("--fps", type=positive_int, default=30)
    parser.add_argument("--seconds", type=positive_int, default=3)
    return parser.parse_args()


def list_windows_devices() -> None:
    if platform.system() != "Windows":
        return
    try:
        from pygrabber.dshow_graph import FilterGraph
    except Exception as exc:
        print(f"[check-virtualcam] DirectShow device listing skipped: {exc}")
        return

    try:
        devices = FilterGraph().get_input_devices()
    except Exception as exc:
        print(f"[check-virtualcam] DirectShow device listing failed: {exc}")
        return

    if not devices:
        print("[check-virtualcam] No DirectShow camera devices found.")
        return

    print("[check-virtualcam] DirectShow camera devices:")
    for index, device in enumerate(devices):
        print(f"  {index}: {device}")


def main() -> int:
    args = parse_args()
    list_windows_devices()

    try:
        import numpy as np
        import pyvirtualcam
    except ImportError as exc:
        print(
            "[check-virtualcam] pyvirtualcam or numpy is not installed. "
            "Run: pip install -r requirements.txt"
        )
        print(f"[check-virtualcam] Details: {exc}")
        return 1

    frame = np.zeros((args.height, args.width, 3), dtype=np.uint8)
    device = args.name or None
    try:
        with pyvirtualcam.Camera(
            width=args.width,
            height=args.height,
            fps=args.fps,
            fmt=pyvirtualcam.PixelFormat.BGR,
            device=device,
        ) as cam:
            print(
                "[check-virtualcam] Sending test frames to "
                f"{cam.device} ({cam.width}x{cam.height}@{cam.fps:g}, "
                f"backend={cam.backend})"
            )
            deadline = time.time() + args.seconds
            frames = 0
            while time.time() < deadline:
                frame[:, :, 0] = (frames * 7) % 255
                frame[:, :, 1] = 80
                frame[:, :, 2] = 255 - ((frames * 5) % 255)
                cam.send(frame)
                cam.sleep_until_next_frame()
                frames += 1
            print(f"[check-virtualcam] Sent {frames} test frames.")
    except Exception as exc:
        print(
            "[check-virtualcam] Virtual camera test failed. Install OBS Studio "
            "or another pyvirtualcam-supported camera, close apps already using "
            "that virtual camera, then try again."
        )
        print(f"[check-virtualcam] Details: {exc}")
        print(
            "[check-virtualcam] OBS built-in virtual camera is a single device. "
            "For OBS rebroadcast, use Window Capture or a separate virtual camera "
            "device instead of trying to capture and output OBS Virtual Camera at "
            "the same time."
        )
        return 1

    print("[check-virtualcam] Virtual camera check complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
