import math

import numpy as np
import pytest

import modules.globals
from modules import capturer


class FakeCapture:
    def __init__(self, *, frame_count=5, fps=30.0):
        self.frame_count = frame_count
        self.fps = fps
        self.set_calls = []
        self.released = False

    def get(self, prop):
        if prop == capturer.cv2.CAP_PROP_FRAME_COUNT:
            return self.frame_count
        if prop == capturer.cv2.CAP_PROP_FPS:
            return self.fps
        raise AssertionError(f"Unexpected capture property: {prop}")

    def set(self, prop, value):
        self.set_calls.append((prop, value))
        return True

    def read(self):
        return True, np.zeros((1, 1, 3), dtype=np.uint8)

    def release(self):
        self.released = True


@pytest.mark.parametrize(
    ("requested_frame", "expected_frame"),
    [(-10, 0), (0, 0), (1, 1), (4, 4), (99, 4)],
)
def test_get_video_frame_uses_zero_based_clamped_frame_numbers(
    monkeypatch, requested_frame, expected_frame
):
    fake = FakeCapture(frame_count=5)
    monkeypatch.setattr(capturer.cv2, "VideoCapture", lambda _path: fake)
    monkeypatch.setattr(modules.globals, "color_correction", False)

    frame = capturer.get_video_frame("target.mp4", requested_frame)

    assert frame is not None
    assert (capturer.cv2.CAP_PROP_POS_FRAMES, expected_frame) in fake.set_calls
    assert fake.released


@pytest.mark.parametrize(
    ("reported_fps", "expected_fps"),
    [(29.97, 29.97), (0.0, 30.0), (-1.0, 30.0), (math.nan, 30.0)],
)
def test_get_video_frame_rate_falls_back_for_invalid_metadata(
    monkeypatch, reported_fps, expected_fps
):
    fake = FakeCapture(fps=reported_fps)
    monkeypatch.setattr(capturer.cv2, "VideoCapture", lambda _path: fake)

    fps = capturer.get_video_frame_rate("target.mp4")

    assert fps == expected_fps
    assert fake.released


def test_video_frame_reader_reuses_capture_for_sequential_frames(monkeypatch):
    captures = []

    class SequentialFakeCapture(FakeCapture):
        def __init__(self):
            super().__init__(frame_count=6)
            self.position = 0

        def set(self, prop, value):
            super().set(prop, value)
            if prop == capturer.cv2.CAP_PROP_POS_FRAMES:
                self.position = int(value)
            return True

        def read(self):
            frame_number = self.position
            self.position += 1
            return True, np.full((1, 1, 3), frame_number, dtype=np.uint8)

    def make_capture(_path):
        capture = SequentialFakeCapture()
        captures.append(capture)
        return capture

    monkeypatch.setattr(capturer.cv2, "VideoCapture", make_capture)
    monkeypatch.setattr(modules.globals, "color_correction", False)

    with capturer.VideoFrameReader("target.mp4") as reader:
        first = reader.read(0)
        second = reader.read(1)
        jumped = reader.read(4)

    assert len(captures) == 1
    position_calls = [
        value
        for prop, value in captures[0].set_calls
        if prop == capturer.cv2.CAP_PROP_POS_FRAMES
    ]
    assert position_calls == [0, 4]
    assert int(first[0, 0, 0]) == 0
    assert int(second[0, 0, 0]) == 1
    assert int(jumped[0, 0, 0]) == 4
    assert captures[0].released
