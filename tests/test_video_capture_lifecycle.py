from types import SimpleNamespace

import pytest

from modules import video_capture


class FakeCapture:
    def __init__(self, *, fail_release=False):
        self.released = 0
        self.fail_release = fail_release

    def release(self):
        self.released += 1
        if self.fail_release:
            raise RuntimeError("capture release failed")


@pytest.mark.parametrize("running", [False, True])
@pytest.mark.parametrize("fail_release", [False, True])
def test_release_clears_partial_capture_and_is_idempotent(monkeypatch, running, fail_release):
    monkeypatch.setattr(video_capture.platform, "system", lambda: "Linux")
    capturer = video_capture.VideoCapturer(0)
    capture = FakeCapture(fail_release=fail_release)
    capturer.cap = capture
    capturer.is_running = running

    capturer.release()
    capturer.release()

    assert capture.released == 1
    assert capturer.cap is None
    assert capturer.is_running is False
    assert capturer.read() == (False, None)


def test_failed_start_clears_capture_and_running_state(monkeypatch):
    monkeypatch.setattr(video_capture.platform, "system", lambda: "Linux")
    capturer = video_capture.VideoCapturer(0)
    capture = FakeCapture()
    capture.isOpened = lambda: False
    monkeypatch.setattr(video_capture.cv2, "VideoCapture", lambda _index: capture)

    assert capturer.start() is False

    assert capture.released == 1
    assert capturer.cap is None
    assert capturer.is_running is False


def test_windows_releases_failed_backend_before_trying_next(monkeypatch):
    monkeypatch.setattr(video_capture.platform, "system", lambda: "Windows")
    monkeypatch.setattr(video_capture, "FilterGraph", lambda: SimpleNamespace(get_input_devices=lambda: ["camera"]), raising=False)
    captures = [FakeCapture() for _ in range(3)]

    def is_opened():
        raise RuntimeError("backend failed")

    for capture in captures:
        capture.isOpened = is_opened
    pending = iter(captures)
    monkeypatch.setattr(video_capture.cv2, "VideoCapture", lambda *_args: next(pending))
    capturer = video_capture.VideoCapturer(0)

    assert capturer.start() is False

    assert [capture.released for capture in captures] == [1, 1, 1]
    assert capturer.cap is None


def test_start_releases_previous_capture_and_preserves_camera_configuration(monkeypatch):
    monkeypatch.setattr(video_capture.platform, "system", lambda: "Linux")
    capturer = video_capture.VideoCapturer(0)
    previous = FakeCapture()
    capturer.cap = previous
    capturer.is_running = True
    capture = FakeCapture()
    settings = {}
    capture.isOpened = lambda: True
    capture.set = lambda key, value: settings.update({key: value})
    capture.get = lambda key: settings[key]
    monkeypatch.setattr(video_capture.cv2, "VideoCapture", lambda _index: capture)
    monkeypatch.setattr(capturer, "_measure_fps", lambda **_kwargs: 29.9)

    assert capturer.start(1280, 720, 30) is True

    assert previous.released == 1
    assert capture.released == 0
    assert capturer.is_running is True
    assert (capturer.actual_width, capturer.actual_height, capturer.actual_fps) == (1280, 720, 29.9)
    assert settings[video_capture.cv2.CAP_PROP_FPS] == 30
    capturer.release()
