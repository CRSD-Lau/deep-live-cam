import queue

import pytest

from modules.live_queue import get_latest, put_latest


def test_put_latest_drops_oldest_when_queue_is_full():
    frame_queue = queue.Queue(maxsize=2)
    frame_queue.put_nowait("oldest")
    frame_queue.put_nowait("middle")

    dropped = put_latest(frame_queue, "latest")

    assert dropped == 1
    assert frame_queue.get_nowait() == "middle"
    assert frame_queue.get_nowait() == "latest"


def test_put_latest_keeps_existing_frame_when_space_is_available():
    frame_queue = queue.Queue(maxsize=2)
    frame_queue.put_nowait("oldest")

    dropped = put_latest(frame_queue, "latest")

    assert dropped == 0
    assert frame_queue.get_nowait() == "oldest"
    assert frame_queue.get_nowait() == "latest"


def test_get_latest_drains_stale_frames_and_returns_freshest():
    frame_queue = queue.Queue(maxsize=4)
    frame_queue.put_nowait("oldest")
    frame_queue.put_nowait("middle")
    frame_queue.put_nowait("latest")

    frame, skipped = get_latest(frame_queue, timeout=0.01)

    assert frame == "latest"
    assert skipped == 2
    assert frame_queue.empty()


def test_get_latest_preserves_queue_empty_behavior():
    frame_queue = queue.Queue(maxsize=1)

    with pytest.raises(queue.Empty):
        get_latest(frame_queue, timeout=0.001)
