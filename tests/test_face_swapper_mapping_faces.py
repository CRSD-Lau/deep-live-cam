import numpy as np

import modules.globals
from modules.processors.frame import face_swapper


class EmbeddedFace:
    def __init__(self, value, bbox=None):
        self.normed_embedding = np.asarray(value, dtype=np.float32) if value is not None else None
        self.bbox = bbox


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


def test_process_frame_v2_preserves_video_mapping_order(monkeypatch):
    source_a = {"source": "a"}
    source_b = {"source": "b"}
    target_a = {"target": "a"}
    target_b = {"target": "b"}
    target_other_frame = {"target": "other"}
    monkeypatch.setattr(modules.globals, "opacity", 1.0)
    monkeypatch.setattr(modules.globals, "many_faces", False)
    monkeypatch.setattr(modules.globals, "target_path", "target.mp4")
    monkeypatch.setattr(
        modules.globals,
        "source_target_map",
        [
            {
                "source": {"face": source_a},
                "target_faces_in_frame": [
                    {"location": "frame-1.png", "faces": [target_a]},
                    {"location": "frame-2.png", "faces": [target_other_frame]},
                ],
            },
            {
                "source": {"face": source_b},
                "target_faces_in_frame": [
                    {"location": "frame-1.png", "faces": [target_b]},
                ],
            },
        ],
    )
    monkeypatch.setattr(face_swapper, "is_image", lambda _path: False)
    monkeypatch.setattr(face_swapper, "is_video", lambda _path: True)
    swaps = []

    def fake_swap(source, target, frame):
        swaps.append((source, target))
        return frame

    monkeypatch.setattr(face_swapper, "swap_face", fake_swap)
    monkeypatch.setattr(
        face_swapper,
        "apply_post_processing",
        lambda frame, _bboxes, _faces: frame,
    )

    face_swapper.process_frame_v2(
        np.zeros((4, 4, 3), dtype=np.uint8), "frame-1.png"
    )

    assert swaps == [(source_a, target_a), (source_b, target_b)]


def test_process_frame_v2_live_simple_map_matches_each_detected_face(monkeypatch):
    source_a = {"source": "a"}
    source_b = {"source": "b"}
    detected_a = EmbeddedFace([0.9, 0.1])
    detected_b = EmbeddedFace([0.1, 0.9])
    monkeypatch.setattr(modules.globals, "opacity", 1.0)
    monkeypatch.setattr(modules.globals, "many_faces", False)
    monkeypatch.setattr(modules.globals, "target_path", None)
    monkeypatch.setattr(
        modules.globals,
        "simple_map",
        {
            "source_faces": [source_a, source_b],
            "target_embeddings": [
                np.array([1.0, 0.0]),
                np.array([0.0, 1.0]),
            ],
        },
    )
    monkeypatch.setattr(
        face_swapper, "get_many_faces", lambda _frame: [detected_a, detected_b]
    )
    monkeypatch.setattr(
        face_swapper,
        "find_closest_centroid",
        lambda centroids, embedding: (
            int(np.argmax(embedding)),
            0.0,
        ),
    )
    swaps = []
    monkeypatch.setattr(
        face_swapper,
        "swap_face",
        lambda source, target, frame: swaps.append((source, target)) or frame,
    )
    monkeypatch.setattr(
        face_swapper,
        "apply_post_processing",
        lambda frame, _bboxes, _faces: frame,
    )

    face_swapper.process_frame_v2(np.zeros((4, 4, 3), dtype=np.uint8))

    assert swaps == [(source_a, detected_a), (source_b, detected_b)]


def test_process_frame_v2_preserves_no_embedding_early_return(monkeypatch):
    detected_faces = [EmbeddedFace(None), EmbeddedFace(None)]
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    monkeypatch.setattr(modules.globals, "opacity", 1.0)
    monkeypatch.setattr(modules.globals, "many_faces", False)
    monkeypatch.setattr(modules.globals, "target_path", None)
    monkeypatch.setattr(
        modules.globals,
        "simple_map",
        {
            "source_faces": [{"source": "only"}],
            "target_embeddings": [np.array([1.0, 0.0])],
        },
    )
    monkeypatch.setattr(face_swapper, "get_many_faces", lambda _frame: detected_faces)
    monkeypatch.setattr(
        face_swapper,
        "apply_post_processing",
        lambda *_args: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    result = face_swapper.process_frame_v2(frame)

    assert result is frame


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
