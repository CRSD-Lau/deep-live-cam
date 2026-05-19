from types import SimpleNamespace

import numpy as np
import pytest

import modules.globals
from modules.expression_regions import (
    LEFT_EYE_INDICES,
    MOUTH_OUTER_INDICES,
    RIGHT_EYE_INDICES,
)
from modules.processors.frame import face_swapper


def _mouth_points(center, width=40.0, height=12.0):
    angles = np.linspace(0.0, 2.0 * np.pi, len(MOUTH_OUTER_INDICES), endpoint=False)
    points = np.column_stack(
        [
            center[0] + np.cos(angles) * width / 2.0,
            center[1] + np.sin(angles) * height / 2.0,
        ]
    ).astype(np.float32)
    points[0] = [center[0] - width / 2.0, center[1]]
    points[1] = [center[0] + width / 2.0, center[1]]
    points[2] = [center[0], center[1] - height / 2.0]
    points[3] = [center[0], center[1] + height / 2.0]
    return points


def _eye_points(center, width=20.0, height=4.0, count=9):
    angles = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    points = np.column_stack(
        [
            center[0] + np.cos(angles) * width / 2.0,
            center[1] + np.sin(angles) * height / 2.0,
        ]
    ).astype(np.float32)
    points[0] = [center[0] - width / 2.0, center[1]]
    points[1] = [center[0] + width / 2.0, center[1]]
    points[2] = [center[0], center[1] - height / 2.0]
    points[3] = [center[0], center[1] + height / 2.0]
    return points


def _face_with_shifted_mouth():
    landmarks = np.zeros((106, 2), dtype=np.float32)
    landmarks[list(MOUTH_OUTER_INDICES)] = _mouth_points(center=(170.0, 170.0))
    return SimpleNamespace(
        bbox=np.array([20.0, 20.0, 100.0, 120.0], dtype=np.float32),
        landmark_2d_106=landmarks,
    )


def _face_with_eye_band_mouth():
    landmarks = np.zeros((106, 2), dtype=np.float32)
    landmarks[list(MOUTH_OUTER_INDICES)] = _mouth_points(center=(60.0, 45.0))
    return SimpleNamespace(
        bbox=np.array([20.0, 20.0, 100.0, 120.0], dtype=np.float32),
        landmark_2d_106=landmarks,
    )


def _expression_face(
    mouth_height=12.0,
    mouth_center=(60.0, 82.0),
    tracking_id=1,
    tracking_motion_amount=0.0,
    tracking_missed_frames=0,
):
    landmarks = np.zeros((106, 2), dtype=np.float32)
    landmarks[list(MOUTH_OUTER_INDICES)] = _mouth_points(
        center=mouth_center, height=mouth_height
    )
    landmarks[list(RIGHT_EYE_INDICES)] = _eye_points(center=(42.0, 45.0))
    landmarks[list(LEFT_EYE_INDICES)] = _eye_points(
        center=(78.0, 45.0), width=24.0, height=6.0
    )
    return SimpleNamespace(
        bbox=np.array([20.0, 20.0, 100.0, 120.0], dtype=np.float32),
        landmark_2d_106=landmarks,
        tracking_id=tracking_id,
        tracking_motion_amount=tracking_motion_amount,
        tracking_missed_frames=tracking_missed_frames,
    )


def _frame():
    return np.full((240, 240, 3), 80, dtype=np.uint8)


def test_lower_mouth_mask_returns_default_when_confidence_below_threshold(
    monkeypatch,
):
    monkeypatch.setattr(
        modules.globals, "expression_mouth_min_confidence", 0.35, raising=False
    )
    monkeypatch.setattr(face_swapper, "gpu_gaussian_blur", lambda src, *_args: src)

    mask, cutout, box, polygon = face_swapper.create_lower_mouth_mask(
        _face_with_shifted_mouth(), _frame()
    )

    assert mask.sum() == 0
    assert cutout is None
    assert box == (0, 0, 0, 0)
    assert polygon is None


def test_lower_mouth_mask_returns_default_for_in_bbox_eye_band_mouth(
    monkeypatch,
):
    monkeypatch.setattr(
        modules.globals, "expression_mouth_min_confidence", 0.35, raising=False
    )
    monkeypatch.setattr(face_swapper, "gpu_gaussian_blur", lambda src, *_args: src)

    mask, cutout, box, polygon = face_swapper.create_lower_mouth_mask(
        _face_with_eye_band_mouth(), _frame()
    )

    assert mask.sum() == 0
    assert cutout is None
    assert box == (0, 0, 0, 0)
    assert polygon is None


def test_lower_mouth_mask_zero_threshold_preserves_existing_mask_behavior(
    monkeypatch,
):
    monkeypatch.setattr(
        modules.globals, "expression_mouth_min_confidence", 0.0, raising=False
    )
    monkeypatch.setattr(face_swapper, "gpu_gaussian_blur", lambda src, *_args: src)

    mask, cutout, box, polygon = face_swapper.create_lower_mouth_mask(
        _face_with_shifted_mouth(), _frame()
    )

    assert mask.sum() > 0
    assert cutout is not None
    assert box != (0, 0, 0, 0)
    assert polygon is not None


def test_lower_mouth_mask_temporally_smooths_tracked_geometry(monkeypatch):
    monkeypatch.setattr(modules.globals, "expression_mouth_min_confidence", 0.0)
    monkeypatch.setattr(modules.globals, "mouth_mask_size", 0.0)
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.5)
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_motion_reduction", 0.0)
    monkeypatch.setattr(face_swapper, "gpu_gaussian_blur", lambda src, *_args: src)
    face_swapper.reset_compositing_temporal_state()

    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.0)
    _mask, _cutout, _box, previous_polygon = face_swapper.create_lower_mouth_mask(
        _expression_face(mouth_center=(60.0, 82.0)),
        _frame(),
    )
    _mask, _cutout, _box, current_polygon = face_swapper.create_lower_mouth_mask(
        _expression_face(mouth_center=(70.0, 82.0)),
        _frame(),
    )
    previous_mean = float(np.mean(previous_polygon[:, 0]))
    current_mean = float(np.mean(current_polygon[:, 0]))
    face_swapper.reset_compositing_temporal_state()
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.5)

    face_swapper.create_lower_mouth_mask(
        _expression_face(mouth_center=(60.0, 82.0)),
        _frame(),
    )
    _mask, _cutout, _box, polygon = face_swapper.create_lower_mouth_mask(
        _expression_face(mouth_center=(70.0, 82.0)),
        _frame(),
    )

    assert polygon is not None
    smoothed_mean = float(np.mean(polygon[:, 0]))
    assert previous_mean < smoothed_mean < current_mean
    assert smoothed_mean == pytest.approx(
        previous_mean * 0.5 + current_mean * 0.5,
        abs=1.0,
    )


def test_lower_mouth_mask_motion_reduces_temporal_smoothing(monkeypatch):
    monkeypatch.setattr(modules.globals, "expression_mouth_min_confidence", 0.0)
    monkeypatch.setattr(modules.globals, "mouth_mask_size", 0.0)
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.5)
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_motion_reduction", 1.0)
    monkeypatch.setattr(face_swapper, "gpu_gaussian_blur", lambda src, *_args: src)
    face_swapper.reset_compositing_temporal_state()

    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.0)
    _mask, _cutout, _box, current_polygon = face_swapper.create_lower_mouth_mask(
        _expression_face(mouth_center=(70.0, 82.0)),
        _frame(),
    )
    current_mean = float(np.mean(current_polygon[:, 0]))
    face_swapper.reset_compositing_temporal_state()
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.5)

    face_swapper.create_lower_mouth_mask(
        _expression_face(mouth_center=(60.0, 82.0)),
        _frame(),
    )
    _mask, _cutout, _box, polygon = face_swapper.create_lower_mouth_mask(
        _expression_face(
            mouth_center=(70.0, 82.0),
            tracking_motion_amount=1.0,
        ),
        _frame(),
    )

    assert polygon is not None
    assert np.mean(polygon[:, 0]) == pytest.approx(current_mean, abs=1.0)


def test_lower_mouth_mask_resets_temporal_state_on_missed_track(monkeypatch):
    monkeypatch.setattr(modules.globals, "expression_mouth_min_confidence", 0.0)
    monkeypatch.setattr(modules.globals, "mouth_mask_size", 0.0)
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.5)
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_motion_reduction", 0.0)
    monkeypatch.setattr(face_swapper, "gpu_gaussian_blur", lambda src, *_args: src)
    face_swapper.reset_compositing_temporal_state()

    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.0)
    _mask, _cutout, _box, current_polygon = face_swapper.create_lower_mouth_mask(
        _expression_face(mouth_center=(70.0, 82.0)),
        _frame(),
    )
    current_mean = float(np.mean(current_polygon[:, 0]))
    face_swapper.reset_compositing_temporal_state()
    monkeypatch.setattr(modules.globals, "mouth_mask_temporal_smoothing", 0.5)

    face_swapper.create_lower_mouth_mask(
        _expression_face(mouth_center=(60.0, 82.0)),
        _frame(),
    )
    _mask, _cutout, _box, polygon = face_swapper.create_lower_mouth_mask(
        _expression_face(
            mouth_center=(70.0, 82.0),
            tracking_missed_frames=1,
        ),
        _frame(),
    )

    assert polygon is not None
    assert np.mean(polygon[:, 0]) == pytest.approx(current_mean, abs=1.0)
    assert face_swapper.MOUTH_MASK_GEOMETRY["landmarks"] == {}


def test_expression_adjusted_interpolation_weight_tracks_stability_and_motion(
    monkeypatch,
):
    monkeypatch.setattr(modules.globals, "expression_temporal_smoothing", True)
    monkeypatch.setattr(
        modules.globals, "expression_temporal_stable_weight_multiplier", 0.86
    )
    monkeypatch.setattr(modules.globals, "expression_temporal_motion_threshold", 0.035)
    monkeypatch.setattr(
        modules.globals, "expression_temporal_high_motion_threshold", 0.09
    )
    monkeypatch.setattr(modules.globals, "expression_temporal_motion_weight_boost", 0.22)
    face_swapper.PREVIOUS_EXPRESSION_SNAPSHOTS = {}

    first = face_swapper._expression_adjusted_interpolation_weight(
        0.35, [_expression_face()]
    )
    stable = face_swapper._expression_adjusted_interpolation_weight(
        0.35, [_expression_face()]
    )
    moving = face_swapper._expression_adjusted_interpolation_weight(
        0.35, [_expression_face(mouth_height=30.0)]
    )

    assert first == 0.35
    assert stable < 0.35
    assert moving > 0.35


def test_expression_adjusted_interpolation_weight_passes_region_confidence_gates(
    monkeypatch,
):
    captured = {}

    def fake_expression_temporal_weight(*_args, **kwargs):
        captured.update(kwargs)
        return 0.31

    monkeypatch.setattr(modules.globals, "expression_temporal_smoothing", True)
    monkeypatch.setattr(modules.globals, "expression_mouth_min_confidence", 0.42)
    monkeypatch.setattr(modules.globals, "expression_eye_min_confidence", 0.37)
    monkeypatch.setattr(
        face_swapper,
        "expression_temporal_weight",
        fake_expression_temporal_weight,
    )
    face_swapper.PREVIOUS_EXPRESSION_SNAPSHOTS = {}

    result = face_swapper._expression_adjusted_interpolation_weight(
        0.35, [_expression_face()]
    )

    assert result == 0.31
    assert captured["mouth_min_confidence"] == 0.42
    assert captured["eye_min_confidence"] == 0.37


def test_expression_adjusted_interpolation_weight_resets_when_disabled(monkeypatch):
    face_swapper.PREVIOUS_EXPRESSION_SNAPSHOTS = {"track:1": object()}
    monkeypatch.setattr(modules.globals, "expression_temporal_smoothing", False)

    assert face_swapper._expression_adjusted_interpolation_weight(
        0.35, [_expression_face()]
    ) == 0.35
    assert face_swapper.PREVIOUS_EXPRESSION_SNAPSHOTS == {}


def test_stabilized_expression_faces_smooths_only_expression_landmarks(
    monkeypatch,
):
    monkeypatch.setattr(modules.globals, "expression_region_temporal_smoothing", 0.5)
    monkeypatch.setattr(
        modules.globals,
        "expression_region_temporal_motion_reduction",
        0.0,
    )
    face_swapper.reset_compositing_temporal_state()
    first = _expression_face(mouth_center=(60.0, 82.0))
    second = _expression_face(mouth_center=(70.0, 82.0))
    first.landmark_2d_106[0] = [5.0, 5.0]
    second.landmark_2d_106[0] = [50.0, 50.0]

    face_swapper._stabilized_expression_faces([first])
    stabilized = face_swapper._stabilized_expression_faces([second])[0]

    first_mean = float(np.mean(first.landmark_2d_106[list(MOUTH_OUTER_INDICES), 0]))
    second_mean = float(np.mean(second.landmark_2d_106[list(MOUTH_OUTER_INDICES), 0]))
    mouth_x = float(np.mean(stabilized.landmark_2d_106[list(MOUTH_OUTER_INDICES), 0]))
    assert mouth_x == pytest.approx(first_mean * 0.5 + second_mean * 0.5, abs=0.25)
    np.testing.assert_allclose(stabilized.landmark_2d_106[0], [50.0, 50.0])
    np.testing.assert_allclose(second.landmark_2d_106[0], [50.0, 50.0])


def test_stabilized_expression_faces_motion_reduces_history(monkeypatch):
    monkeypatch.setattr(modules.globals, "expression_region_temporal_smoothing", 0.5)
    monkeypatch.setattr(
        modules.globals,
        "expression_region_temporal_motion_reduction",
        1.0,
    )
    face_swapper.reset_compositing_temporal_state()

    face_swapper._stabilized_expression_faces(
        [_expression_face(mouth_center=(60.0, 82.0))]
    )
    stabilized = face_swapper._stabilized_expression_faces(
        [current_face := _expression_face(mouth_center=(70.0, 82.0), tracking_motion_amount=1.0)]
    )[0]

    current_mean = float(np.mean(current_face.landmark_2d_106[list(MOUTH_OUTER_INDICES), 0]))
    mouth_x = float(np.mean(stabilized.landmark_2d_106[list(MOUTH_OUTER_INDICES), 0]))
    assert mouth_x == pytest.approx(current_mean, abs=0.25)


def test_stabilized_expression_faces_resets_on_missed_track(monkeypatch):
    monkeypatch.setattr(modules.globals, "expression_region_temporal_smoothing", 0.5)
    monkeypatch.setattr(
        modules.globals,
        "expression_region_temporal_motion_reduction",
        0.0,
    )
    face_swapper.reset_compositing_temporal_state()

    face_swapper._stabilized_expression_faces(
        [_expression_face(mouth_center=(60.0, 82.0))]
    )
    stabilized = face_swapper._stabilized_expression_faces(
        [current_face := _expression_face(mouth_center=(70.0, 82.0), tracking_missed_frames=1)]
    )[0]

    current_mean = float(np.mean(current_face.landmark_2d_106[list(MOUTH_OUTER_INDICES), 0]))
    mouth_x = float(np.mean(stabilized.landmark_2d_106[list(MOUTH_OUTER_INDICES), 0]))
    assert mouth_x == pytest.approx(current_mean, abs=0.25)
    assert face_swapper.EXPRESSION_REGION_GEOMETRY["landmarks"] == {}
