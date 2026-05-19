"""Small helpers for low-latency live camera queues."""

from __future__ import annotations

import queue
from typing import Any


def put_latest(frame_queue: queue.Queue, frame: Any) -> int:
    """Put a frame into a bounded queue, dropping the oldest frame on overflow."""
    try:
        frame_queue.put_nowait(frame)
        return 0
    except queue.Full:
        dropped = _discard_one(frame_queue)

    try:
        frame_queue.put_nowait(frame)
    except queue.Full:
        return max(dropped, 1)
    return dropped


def get_latest(frame_queue: queue.Queue, *, timeout: float) -> tuple[Any, int]:
    """Return the freshest queued frame and count older frames skipped."""
    frame = frame_queue.get(timeout=timeout)
    skipped = 0
    while True:
        try:
            frame = frame_queue.get_nowait()
            skipped += 1
        except queue.Empty:
            return frame, skipped


def _discard_one(frame_queue: queue.Queue) -> int:
    try:
        frame_queue.get_nowait()
    except queue.Empty:
        return 0
    return 1
