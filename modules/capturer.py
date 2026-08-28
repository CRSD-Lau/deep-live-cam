import math
from typing import Any, Optional

import cv2
import modules.globals  # Import the globals to check the color correction toggle
from modules.gpu_processing import gpu_cvt_color


class VideoFrameReader:
    """Read requested frames while keeping one video capture open."""

    def __init__(self, video_path: str) -> None:
        self._capture = cv2.VideoCapture(video_path)
        self._capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        if modules.globals.color_correction:
            self._capture.set(cv2.CAP_PROP_CONVERT_RGB, 1)

        frame_total = max(0, int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        self._last_frame = max(0, frame_total - 1)
        self._next_frame_number: Optional[int] = None

    def read(self, frame_number: int = 0) -> Any:
        requested_frame = min(self._last_frame, max(0, int(frame_number)))
        if requested_frame != self._next_frame_number:
            self._capture.set(cv2.CAP_PROP_POS_FRAMES, requested_frame)

        has_frame, frame = self._capture.read()
        self._next_frame_number = requested_frame + 1 if has_frame else None

        if has_frame and modules.globals.color_correction:
            frame = gpu_cvt_color(frame, cv2.COLOR_BGR2RGB)
        return frame if has_frame else None

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def __enter__(self) -> "VideoFrameReader":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def get_video_frame(video_path: str, frame_number: int = 0) -> Any:
    with VideoFrameReader(video_path) as reader:
        return reader.read(frame_number)


def get_video_frame_total(video_path: str) -> int:
    capture = cv2.VideoCapture(video_path)
    video_frame_total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()
    return video_frame_total


def get_video_frame_rate(video_path: str, fallback: float = 30.0) -> float:
    capture = cv2.VideoCapture(video_path)
    try:
        frame_rate = float(capture.get(cv2.CAP_PROP_FPS))
    finally:
        capture.release()
    if not math.isfinite(frame_rate) or frame_rate <= 0:
        return fallback
    return frame_rate
