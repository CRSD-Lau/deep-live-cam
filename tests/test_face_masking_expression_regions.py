from types import SimpleNamespace

import numpy as np

from modules.expression_regions import (
    LEFT_EYE_INDICES,
    LEFT_EYEBROW_INDICES,
    RIGHT_EYE_INDICES,
    RIGHT_EYEBROW_INDICES,
)
from modules.processors.frame import face_masking


def _oval_points(count, center, width, height):
    angles = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    return np.column_stack(
        [
            center[0] + np.cos(angles) * width / 2.0,
            center[1] + np.sin(angles) * height / 2.0,
        ]
    ).astype(np.float32)


def _outline_landmarks(count=33):
    return _oval_points(count, center=(50.0, 42.0), width=48.0, height=60.0)


def _valid_expression_landmarks():
    landmarks = np.zeros((106, 2), dtype=np.float32)
    landmarks[0:33] = _outline_landmarks(33)
    landmarks[list(RIGHT_EYE_INDICES)] = _oval_points(
        len(RIGHT_EYE_INDICES), center=(42.0, 42.0), width=20.0, height=8.0
    )
    landmarks[list(LEFT_EYE_INDICES)] = _oval_points(
        len(LEFT_EYE_INDICES), center=(78.0, 42.0), width=20.0, height=8.0
    )
    landmarks[list(RIGHT_EYEBROW_INDICES)] = np.array(
        [
            [31.0, 31.0],
            [34.0, 28.0],
            [38.0, 26.0],
            [42.0, 25.0],
            [46.0, 26.0],
            [50.0, 28.0],
            [53.0, 31.0],
            [55.0, 33.0],
        ],
        dtype=np.float32,
    )
    landmarks[list(LEFT_EYEBROW_INDICES)] = np.array(
        [
            [67.0, 31.0],
            [70.0, 28.0],
            [74.0, 26.0],
            [78.0, 25.0],
            [82.0, 26.0],
            [86.0, 28.0],
            [89.0, 31.0],
            [91.0, 33.0],
        ],
        dtype=np.float32,
    )
    return landmarks


def _blank_frame():
    return np.zeros((96, 128, 3), dtype=np.uint8)


def test_create_face_mask_accepts_outline_only_short_landmarks():
    face = SimpleNamespace(landmark_2d_106=_outline_landmarks(33))

    mask = face_masking.create_face_mask(face, _blank_frame())

    assert mask.shape == (96, 128)
    assert mask.dtype == np.uint8


def test_create_face_mask_opt_in_extended_subject_covers_shoulders_without_far_background(
    monkeypatch,
):
    monkeypatch.setattr(face_masking, "gpu_gaussian_blur", lambda src, *_args: src)
    face = SimpleNamespace(landmark_2d_106=_outline_landmarks(33))

    baseline = face_masking.create_face_mask(face, _blank_frame())
    extended = face_masking.create_face_mask(
        face,
        _blank_frame(),
        extended_subject=True,
    )

    assert baseline[88, 50] == 0
    assert extended[88, 50] == 255
    assert extended[84, 28] == 255
    assert extended[84, 72] == 255
    assert 40 <= extended[88, 8] <= 180
    assert extended[88, 0] == 0
    assert extended[88, 118] == 0


def test_create_eyes_mask_returns_default_for_short_landmarks():
    face = SimpleNamespace(landmark_2d_106=np.zeros((80, 2), dtype=np.float32))

    mask, cutout, box, polygon = face_masking.create_eyes_mask(face, _blank_frame())

    assert mask.shape == (96, 128)
    assert mask.sum() == 0
    assert cutout is None
    assert box == (0, 0, 0, 0)
    assert polygon is None


def test_create_eyes_mask_accepts_valid_landmarks_without_global_size(
    monkeypatch,
):
    monkeypatch.delattr(face_masking.modules.globals, "eyes_mask_size", raising=False)
    monkeypatch.setattr(face_masking, "gpu_gaussian_blur", lambda src, *_args: src)
    face = SimpleNamespace(landmark_2d_106=_valid_expression_landmarks())

    mask, cutout, box, polygon = face_masking.create_eyes_mask(face, _blank_frame())

    assert mask.sum() > 0
    assert cutout is not None and cutout.size > 0
    assert box != (0, 0, 0, 0)
    assert polygon is not None and len(polygon) > 0


def test_create_eyebrows_mask_returns_default_for_short_landmarks():
    face = SimpleNamespace(landmark_2d_106=np.zeros((96, 2), dtype=np.float32))

    mask, cutout, box, polygon = face_masking.create_eyebrows_mask(face, _blank_frame())

    assert mask.shape == (96, 128)
    assert mask.sum() == 0
    assert cutout is None
    assert box == (0, 0, 0, 0)
    assert polygon is None


def test_create_eyebrows_mask_accepts_valid_landmarks_and_fills_mask(
    monkeypatch,
):
    monkeypatch.delattr(
        face_masking.modules.globals, "eyebrows_mask_size", raising=False
    )
    monkeypatch.setattr(face_masking, "gpu_gaussian_blur", lambda src, *_args: src)
    face = SimpleNamespace(landmark_2d_106=_valid_expression_landmarks())

    mask, cutout, box, polygon = face_masking.create_eyebrows_mask(
        face, _blank_frame()
    )

    assert mask.sum() > 0
    assert cutout is not None and cutout.size > 0
    assert box != (0, 0, 0, 0)
    assert polygon is not None and len(polygon) > 0
