import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from modules import ui


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("failure", ["constructor", "start_exception", "start_false"])
def test_failed_camera_start_stops_virtual_output(monkeypatch, qapp, failure):
    calls = []
    statuses = []
    queued_close = []

    class VirtualCamera:
        def start(self):
            calls.append("virtual_start")

        def stop(self):
            calls.append("virtual_stop")

    class Capture:
        def __init__(self, _index):
            if failure == "constructor":
                raise ValueError("camera disappeared")

        def start(self, *_args):
            if failure == "start_exception":
                raise RuntimeError("camera failed")
            return False

        def release(self):
            calls.append("capture_release")

    monkeypatch.setattr(ui.modules.globals, "virtual_cam", True)
    monkeypatch.setattr(ui.VirtualCameraSink, "from_globals", lambda **_kwargs: VirtualCamera())
    monkeypatch.setattr(ui, "VideoCapturer", Capture)
    monkeypatch.setattr(ui, "update_status", statuses.append)
    monkeypatch.setattr(ui.QTimer, "singleShot", lambda _delay, callback: queued_close.append(callback))

    window = ui.WebcamPreviewWindow(0)
    try:
        assert calls.count("virtual_start") == 1
        assert calls.count("virtual_stop") == 1
        assert window._virtual_cam is None
        assert window._stop_event.is_set()
        assert not window._workers_running()
        assert any("Failed to start camera" in status for status in statuses)
        assert queued_close
    finally:
        window.close()
