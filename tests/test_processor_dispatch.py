from types import SimpleNamespace

from modules.processors.frame.core import reset_frame_processor_temporal_state
from modules.processors.frame.processor_dispatch import process_frame_with_target


def test_tracked_face_is_sent_to_detected_faces_processors():
    face = SimpleNamespace(tracking_id=7)
    frame = object()

    class EnhancerProcessor:
        def __init__(self):
            self.detected_faces = "not-called"

        def process_frame(self, source_face, temp_frame, detected_faces=None):
            self.detected_faces = detected_faces
            return temp_frame

    processor = EnhancerProcessor()

    result = process_frame_with_target(processor, "source", frame, face)

    assert result is frame
    assert processor.detected_faces == [face]


def test_tracked_face_is_sent_to_target_face_processors():
    face = SimpleNamespace(tracking_id=7)
    frame = object()

    class SwapperProcessor:
        def __init__(self):
            self.target_face = "not-called"

        def process_frame(self, source_face, temp_frame, target_face=None):
            self.target_face = target_face
            return temp_frame

    processor = SwapperProcessor()

    result = process_frame_with_target(processor, "source", frame, face)

    assert result is frame
    assert processor.target_face is face


def test_missing_face_keeps_detected_faces_processors_on_default_path():
    frame = object()

    class EnhancerProcessor:
        def __init__(self):
            self.detected_faces = "not-called"

        def process_frame(self, source_face, temp_frame, detected_faces=None):
            self.detected_faces = detected_faces
            return temp_frame

    processor = EnhancerProcessor()

    process_frame_with_target(processor, "source", frame, None)

    assert processor.detected_faces is None


def test_reset_frame_processor_temporal_state_clears_supported_processors():
    class Processor:
        def __init__(self):
            self.PREVIOUS_FRAME_RESULT = object()
            self.reset_called = False

        def reset_compositing_temporal_state(self):
            self.reset_called = True

    processor = Processor()

    reset_frame_processor_temporal_state([processor])

    assert processor.PREVIOUS_FRAME_RESULT is None
    assert processor.reset_called is True
