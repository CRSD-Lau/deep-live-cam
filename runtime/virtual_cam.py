"""Nonblocking pyvirtualcam output for the live preview pipeline."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Callable, Optional

import cv2
import numpy as np


StatusCallback = Callable[[str], None]


@dataclass(frozen=True)
class VirtualCameraConfig:
    enabled: bool = False
    name: Optional[str] = None
    width: int = 1280
    height: int = 720
    fps: int = 30


class VirtualCameraSink:
    """Send processed BGR frames to a virtual camera without blocking render."""

    def __init__(
        self,
        config: VirtualCameraConfig,
        *,
        status_callback: StatusCallback | None = None,
    ) -> None:
        self.config = config
        self._status_callback = status_callback
        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=1)
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._failed_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="DeepLiveCamVirtualCamera",
            daemon=True,
        )

    @classmethod
    def from_globals(
        cls,
        *,
        status_callback: StatusCallback | None = None,
    ) -> "VirtualCameraSink":
        import modules.globals

        return cls(
            VirtualCameraConfig(
                enabled=modules.globals.virtual_cam,
                name=modules.globals.virtual_cam_name,
                width=modules.globals.virtual_cam_width,
                height=modules.globals.virtual_cam_height,
                fps=modules.globals.virtual_cam_fps,
            ),
            status_callback=status_callback,
        )

    @property
    def is_failed(self) -> bool:
        return self._failed_event.is_set()

    def start(self) -> None:
        if not self.config.enabled:
            return
        self._thread.start()

    def send(self, frame_bgr: np.ndarray) -> None:
        if (
            not self.config.enabled
            or self._stop_event.is_set()
            or self._failed_event.is_set()
            or frame_bgr is None
        ):
            return

        try:
            self._queue.put_nowait(frame_bgr)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(frame_bgr)
            except queue.Full:
                pass

    def stop(self) -> None:
        if not self.config.enabled:
            return
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        try:
            import pyvirtualcam
        except ImportError:
            self._failed_event.set()
            self._log(
                "Virtual camera output requires pyvirtualcam. "
                "Install it with: pip install pyvirtualcam==0.15.0"
            )
            return

        device = self.config.name or None
        try:
            with pyvirtualcam.Camera(
                width=self.config.width,
                height=self.config.height,
                fps=self.config.fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
                device=device,
            ) as cam:
                self._ready_event.set()
                self._log(
                    "Virtual camera output started: "
                    f"{cam.device} ({cam.width}x{cam.height}@{cam.fps:g}, "
                    f"backend={cam.backend})"
                )
                latest_frame: np.ndarray | None = None
                while not self._stop_event.is_set():
                    latest_frame = self._next_frame(latest_frame)
                    if latest_frame is None:
                        continue

                    cam.send(latest_frame)
                    cam.sleep_until_next_frame()
        except Exception as exc:
            self._failed_event.set()
            self._log(
                "Virtual camera output failed. Make sure OBS or another "
                "supported virtual camera is installed and not already in use. "
                f"Details: {exc}"
            )

    def _next_frame(self, latest_frame: np.ndarray | None) -> np.ndarray | None:
        if latest_frame is None:
            try:
                return self._prepare_frame(self._queue.get(timeout=0.1))
            except queue.Empty:
                return None

        while True:
            try:
                latest_frame = self._prepare_frame(self._queue.get_nowait())
            except queue.Empty:
                return latest_frame

    def _prepare_frame(self, frame: np.ndarray) -> np.ndarray:
        if frame.shape[1] != self.config.width or frame.shape[0] != self.config.height:
            frame = cv2.resize(
                frame,
                (self.config.width, self.config.height),
                interpolation=cv2.INTER_LINEAR,
            )
        if frame.dtype != np.uint8:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        return np.ascontiguousarray(frame)

    def _log(self, message: str) -> None:
        text = f"[virtual-cam] {message}"
        print(text, flush=True)
        if self._status_callback:
            self._status_callback(text)
