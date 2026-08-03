import queue
import threading

import numpy as np

import modules.globals
import modules.face_analyser
from modules import ui
from modules.processors.frame import core as frame_core


def configure_live_globals(monkeypatch):
    values = {
        "benchmark_pipeline": False,
        "benchmark_output_path": None,
        "execution_providers": ["CUDAExecutionProvider"],
        "face_tracking_enabled": False,
        "fp_ui": {},
        "live_detection_interval_ratio": 0.08,
        "live_mirror": False,
        "live_process_latest_frame": False,
        "many_faces": False,
        "map_faces": False,
        "quality_mode": "balanced",
        "show_fps": False,
        "source_path": "source.jpg",
    }
    for name, value in values.items():
        monkeypatch.setattr(modules.globals, name, value, raising=False)


class FakeVirtualCamera:
    def __init__(self):
        self.frames = []

    def send(self, frame):
        self.frames.append(frame.copy())


def test_processing_worker_preserves_order_and_stops_after_current_frame(monkeypatch):
    configure_live_globals(monkeypatch)
    capture_queue = queue.Queue(maxsize=3)
    processed_queue = queue.Queue(maxsize=3)
    stop_event = threading.Event()
    virtual_cam = FakeVirtualCamera()
    seen = []

    class Processor:
        NAME = "TEST.PROCESSOR"

        @staticmethod
        def process_frame(source, frame):
            assert source == "loaded-source"
            seen.append(int(frame[0, 0, 0]))
            if len(seen) == 2:
                stop_event.set()
            return frame + 1

    resets = []
    monkeypatch.setattr(
        frame_core, "get_frame_processors_modules", lambda _names: [Processor]
    )
    monkeypatch.setattr(
        frame_core,
        "reset_frame_processor_temporal_state",
        lambda processors: resets.append(processors),
    )
    monkeypatch.setattr(ui, "_load_source_face", lambda _path: "loaded-source")
    monkeypatch.setattr(modules.face_analyser, "detect_one_face_fast", lambda _frame: None)
    monkeypatch.setattr(modules.face_analyser, "detect_many_faces_fast", lambda _frame: [])
    monkeypatch.setattr(modules.globals, "frame_processors", ["test"])
    for value in (10, 20, 30):
        capture_queue.put(np.full((1, 1, 3), value, dtype=np.uint8))
    worker = ui._ProcessingWorker(
        capture_queue,
        processed_queue,
        stop_event,
        camera_fps=30.0,
        virtual_cam=virtual_cam,
    )

    worker.run()

    assert seen == [10, 20]
    assert capture_queue.qsize() == 1
    assert [int(processed_queue.get()[0, 0, 0]) for _ in range(2)] == [11, 21]
    assert [int(frame[0, 0, 0]) for frame in virtual_cam.frames] == [11, 21]
    assert len(resets) == 2


def test_processing_worker_sets_stop_event_on_processor_error(monkeypatch):
    configure_live_globals(monkeypatch)
    capture_queue = queue.Queue(maxsize=1)
    processed_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    class BrokenProcessor:
        NAME = "TEST.BROKEN"

        @staticmethod
        def process_frame(_source, _frame):
            raise RuntimeError("processor failed")

    monkeypatch.setattr(
        frame_core, "get_frame_processors_modules", lambda _names: [BrokenProcessor]
    )
    monkeypatch.setattr(
        frame_core, "reset_frame_processor_temporal_state", lambda _processors: None
    )
    monkeypatch.setattr(ui, "_load_source_face", lambda _path: object())
    monkeypatch.setattr(modules.face_analyser, "detect_one_face_fast", lambda _frame: None)
    monkeypatch.setattr(modules.face_analyser, "detect_many_faces_fast", lambda _frame: [])
    monkeypatch.setattr(modules.globals, "frame_processors", ["broken"])
    capture_queue.put(np.zeros((1, 1, 3), dtype=np.uint8))
    worker = ui._ProcessingWorker(
        capture_queue, processed_queue, stop_event, camera_fps=30.0
    )

    worker.run()

    assert stop_event.is_set()
    assert processed_queue.empty()


def test_live_runtime_records_provider_selection_and_queue_configuration(monkeypatch):
    configure_live_globals(monkeypatch)
    monkeypatch.setattr(
        modules.globals,
        "execution_providers",
        ["DmlExecutionProvider", "CPUExecutionProvider"],
    )
    monkeypatch.setattr(
        ui,
        "provider_config_summary",
        lambda providers: {"selected": providers[0]},
    )
    capture_queue = queue.Queue(maxsize=2)
    processed_queue = queue.Queue(maxsize=1)

    runtime = ui._create_live_runtime(
        [], 25.0, capture_queue, processed_queue, None, None
    )

    assert runtime.detection_interval == 2
    assert runtime.metrics_context["execution_providers"] == [
        "DmlExecutionProvider",
        "CPUExecutionProvider",
    ]
    assert runtime.metrics_context["execution_provider_config"] == {
        "selected": "DmlExecutionProvider"
    }
    assert runtime.metrics_context["capture_queue_maxsize"] == 2
    assert runtime.metrics_context["processed_queue_maxsize"] == 1


def test_publish_live_frame_drops_stale_output_when_queue_is_full(monkeypatch):
    configure_live_globals(monkeypatch)
    capture_queue = queue.Queue(maxsize=1)
    processed_queue = queue.Queue(maxsize=1)
    processed_queue.put(np.full((1, 1, 3), 5, dtype=np.uint8))
    runtime = ui._create_live_runtime(
        [], 30.0, capture_queue, processed_queue, None, None
    )
    latest = np.full((1, 1, 3), 9, dtype=np.uint8)

    ui._publish_live_frame(processed_queue, None, latest, runtime)

    np.testing.assert_array_equal(processed_queue.get(), latest)
