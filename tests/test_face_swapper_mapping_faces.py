import numpy as np

import modules.globals
from modules.processors.frame import face_swapper


def test_process_frame_collects_plain_mapping_bbox_for_post_processing(monkeypatch):
    captured = {}

    monkeypatch.setattr(modules.globals, "many_faces", False)
    monkeypatch.setattr(modules.globals, "opacity", 1.0)
    monkeypatch.setattr(
        face_swapper,
        "swap_face",
        lambda _source, _target, frame: frame.copy(),
    )

    def fake_post_processing(frame, swapped_face_bboxes, swapped_faces):
        captured["bboxes"] = swapped_face_bboxes
        captured["faces"] = swapped_faces
        return frame

    monkeypatch.setattr(face_swapper, "apply_post_processing", fake_post_processing)

    target_face = {
        "bbox": np.array([8.8, 3.2, 14.6, 11.9], dtype=np.float32),
    }
    frame = np.full((20, 20, 3), 100, dtype=np.uint8)

    face_swapper.process_frame({"source": True}, frame, target_face=target_face)

    np.testing.assert_array_equal(captured["bboxes"][0], [8, 3, 14, 11])
    assert captured["faces"][0] is target_face


def test_process_frame_v2_collects_mapping_bbox_from_face_map(monkeypatch):
    captured = {}

    monkeypatch.setattr(modules.globals, "opacity", 1.0)
    monkeypatch.setattr(modules.globals, "many_faces", False)
    monkeypatch.setattr(modules.globals, "target_path", "target.jpg")
    monkeypatch.setattr(
        modules.globals,
        "source_target_map",
        [
            {
                "source": {"face": {"source": True}},
                "target": {
                    "face": {
                        "bbox": np.array([2.0, 4.0, 16.0, 18.0], dtype=np.float32),
                    },
                },
            },
        ],
    )
    monkeypatch.setattr(face_swapper, "is_image", lambda _path: True)
    monkeypatch.setattr(face_swapper, "is_video", lambda _path: False)
    monkeypatch.setattr(
        face_swapper,
        "swap_face",
        lambda _source, _target, frame: frame.copy(),
    )

    def fake_post_processing(frame, swapped_face_bboxes, swapped_faces):
        captured["bboxes"] = swapped_face_bboxes
        captured["faces"] = swapped_faces
        return frame

    monkeypatch.setattr(face_swapper, "apply_post_processing", fake_post_processing)

    frame = np.full((24, 24, 3), 80, dtype=np.uint8)

    face_swapper.process_frame_v2(frame)

    np.testing.assert_array_equal(captured["bboxes"][0], [2, 4, 16, 18])
    assert captured["faces"][0] is modules.globals.source_target_map[0]["target"]["face"]


def test_create_face_mask_reads_mapping_landmarks(monkeypatch):
    monkeypatch.setattr(face_swapper, "gpu_gaussian_blur", lambda mask, *_args: mask)

    face = {
        "landmark_2d_106": _synthetic_landmarks(),
    }
    frame = np.zeros((96, 96, 3), dtype=np.uint8)

    mask = face_swapper.create_face_mask(face, frame)

    assert mask.shape == (96, 96)
    assert mask.dtype == np.uint8
    assert mask.sum() > 0


def _synthetic_landmarks():
    angles = np.linspace(0, 2 * np.pi, 106, endpoint=False)
    return np.column_stack(
        [
            48.0 + np.cos(angles) * 20.0,
            52.0 + np.sin(angles) * 24.0,
        ]
    ).astype(np.float32)
