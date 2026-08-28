import os
import queue
import threading

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import modules.globals
from modules import ui


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


class FakePreviewWorker:
    instances = []

    def __init__(self, *args, **kwargs):
        self.started = False
        self.alive = False
        self.joined = False
        FakePreviewWorker.instances.append(self)

    def start(self):
        self.started = True
        self.alive = True

    def is_alive(self):
        return self.alive

    def join(self):
        self.joined = True
        self.alive = False


def configure_video_preview(monkeypatch):
    monkeypatch.setattr(modules.globals, "source_path", "source.jpg")
    monkeypatch.setattr(modules.globals, "target_path", "target.mp4")
    monkeypatch.setattr(ui, "is_image", lambda _path: False)
    monkeypatch.setattr(ui, "is_video", lambda _path: True)
    monkeypatch.setattr(ui, "get_video_frame_total", lambda _path: 120)
    monkeypatch.setattr(ui, "get_video_frame_rate", lambda _path: 30.0)
    monkeypatch.setattr(ui, "_PreviewWorker", FakePreviewWorker)
    FakePreviewWorker.instances.clear()


def test_video_preview_starts_playing_and_queues_first_frame(monkeypatch, qapp):
    configure_video_preview(monkeypatch)
    monkeypatch.setattr(ui.time, "monotonic", lambda: 100.0)
    window = ui.PreviewWindow()

    try:
        window.init_for_target()

        request = window._request_queue.get_nowait()
        assert request.frame_number == 0
        assert window.is_playing
        assert window._play_button.text() == "Pause"
        assert window._slider.maximum() == 119
        assert window._slider.isVisibleTo(window)
        assert FakePreviewWorker.instances[0].started
    finally:
        window.shutdown(block=True)


def test_autoplay_advances_sequentially_when_processing_is_slow(monkeypatch, qapp):
    configure_video_preview(monkeypatch)
    now = [200.0]
    monkeypatch.setattr(ui.time, "monotonic", lambda: now[0])
    window = ui.PreviewWindow()

    try:
        window.init_for_target()
        initial_request = window._request_queue.get_nowait()
        window._result_queue.put(
            ui._PreviewFrameResult(
                generation=initial_request.generation,
                frame_number=0,
                frame=np.zeros((1, 1, 3), dtype=np.uint8),
            )
        )
        window._tick()
        now[0] = 200.5

        window._tick()

        request = window._request_queue.get_nowait()
        assert request.frame_number == 1
        now[0] = 201.0
        window._tick()
        assert window._request_queue.empty()

        window._result_queue.put(
            ui._PreviewFrameResult(
                generation=request.generation,
                frame_number=request.frame_number,
                frame=np.ones((1, 1, 3), dtype=np.uint8),
            )
        )
        now[0] = 201.5
        window._tick()

        next_request = window._request_queue.get_nowait()
        assert next_request.frame_number == 2
    finally:
        window.shutdown(block=True)


def test_autoplay_waits_for_first_processed_frame_before_advancing(monkeypatch, qapp):
    configure_video_preview(monkeypatch)
    now = [250.0]
    monkeypatch.setattr(ui.time, "monotonic", lambda: now[0])
    window = ui.PreviewWindow()

    try:
        window.init_for_target()
        now[0] = 260.0

        window._tick()

        request = window._request_queue.get_nowait()
        assert request.frame_number == 0
    finally:
        window.shutdown(block=True)


def test_repeated_video_frames_do_not_grow_preview_window(monkeypatch, qapp):
    configure_video_preview(monkeypatch)
    monkeypatch.setattr(ui.time, "monotonic", lambda: 275.0)
    window = ui.PreviewWindow()

    try:
        window.init_for_target()
        window.pause()
        request = window._request_queue.get_nowait()
        window.show()
        qapp.processEvents()
        initial_size = (window.width(), window.height())

        observed_sizes = []
        for _ in range(6):
            window._result_queue.put(
                ui._PreviewFrameResult(
                    generation=request.generation,
                    frame_number=0,
                    frame=np.zeros((360, 640, 3), dtype=np.uint8),
                )
            )
            window._tick()
            qapp.processEvents()
            observed_sizes.append((window.width(), window.height()))

        assert observed_sizes == [initial_size] * 6

        pixmap = window._image_label.pixmap()
        image_bounds = window._image_label.contentsRect().size()
        assert pixmap.height() <= image_bounds.height()
        assert pixmap.width() <= image_bounds.width()
    finally:
        window.close()
        qapp.processEvents()


def test_play_button_pauses_without_leaving_future_requests(monkeypatch, qapp):
    configure_video_preview(monkeypatch)
    monkeypatch.setattr(ui.time, "monotonic", lambda: 300.0)
    window = ui.PreviewWindow()

    try:
        window.init_for_target()
        window._play_button.click()

        assert not window.is_playing
        assert window._play_button.text() == "Play"
        remaining_requests = []
        while not window._request_queue.empty():
            remaining_requests.append(window._request_queue.get_nowait().frame_number)
        assert remaining_requests == [0]
    finally:
        window.shutdown(block=True)


def test_still_image_preview_keeps_playback_controls_hidden(monkeypatch, qapp):
    monkeypatch.setattr(modules.globals, "source_path", "source.jpg")
    monkeypatch.setattr(modules.globals, "target_path", "target.png")
    monkeypatch.setattr(ui, "is_image", lambda _path: True)
    monkeypatch.setattr(ui, "is_video", lambda _path: False)
    monkeypatch.setattr(ui, "_PreviewWorker", FakePreviewWorker)
    FakePreviewWorker.instances.clear()
    window = ui.PreviewWindow()

    try:
        window.init_for_target()

        request = window._request_queue.get_nowait()
        assert request.frame_number == 0
        assert not window.is_playing
        assert window._controls_widget.isHidden()
    finally:
        window.shutdown(block=True)


def test_preview_shutdown_stops_timer_and_joins_worker(monkeypatch, qapp):
    configure_video_preview(monkeypatch)
    monkeypatch.setattr(ui.time, "monotonic", lambda: 350.0)
    window = ui.PreviewWindow()
    window.init_for_target()
    worker = FakePreviewWorker.instances[0]
    stop_event = window._stop_event

    window.shutdown(block=True)

    assert stop_event.is_set()
    assert worker.joined
    assert not window._timer.isActive()
    assert window._request_queue is None
    assert window._result_queue is None


def test_preview_worker_processes_requested_frame(monkeypatch):
    request_queue = queue.Queue(maxsize=1)
    result_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()
    processed = []

    class Processor:
        @staticmethod
        def process_frame(source_face, frame):
            assert source_face == "source-face"
            processed.append(int(frame[0, 0, 0]))
            stop_event.set()
            return frame + 1

    monkeypatch.setattr(ui, "_load_source_face", lambda _path: "source-face")
    class FakeVideoFrameReader:
        def __init__(self, _path):
            self.closed = False

        def read(self, number):
            return np.full((1, 1, 3), number, dtype=np.uint8)

        def close(self):
            self.closed = True

    monkeypatch.setattr(ui, "VideoFrameReader", FakeVideoFrameReader)
    monkeypatch.setattr(ui, "check_and_ignore_nsfw", lambda _frame: False)
    monkeypatch.setattr(modules.globals, "frame_processors", ["test"])
    monkeypatch.setattr(modules.globals, "nsfw_filter", False)
    request_queue.put(ui._PreviewFrameRequest(generation=7, frame_number=4))

    from modules.processors.frame import core as frame_core

    monkeypatch.setattr(
        frame_core, "get_frame_processors_modules", lambda _names: [Processor]
    )
    monkeypatch.setattr(
        frame_core, "reset_frame_processor_temporal_state", lambda _processors: None
    )
    worker = ui._PreviewWorker(
        "source.jpg", "target.mp4", request_queue, result_queue, stop_event
    )

    worker.run()

    result = result_queue.get_nowait()
    assert processed == [4]
    assert result.generation == 7
    assert result.frame_number == 4
    assert result.error is None
    np.testing.assert_array_equal(result.frame, np.full((1, 1, 3), 5, dtype=np.uint8))
