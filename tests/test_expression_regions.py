from types import SimpleNamespace

import numpy as np
import pytest

from modules.expression_regions import (
    LEFT_EYE_INDICES,
    LEFT_EYEBROW_INDICES,
    MOUTH_OUTER_INDICES,
    RIGHT_EYE_INDICES,
    RIGHT_EYEBROW_INDICES,
    compute_eye_region_confidences,
    compute_eye_open_ratios,
    compute_mouth_region_confidence,
    compute_mouth_open_ratio,
    compute_region_bbox,
    compute_region_confidence,
    extract_region_points,
)


def _region_points(count, center, width, height):
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


def _face_with_regions():
    landmarks = np.zeros((106, 2), dtype=np.float32)
    landmarks[list(MOUTH_OUTER_INDICES)] = _region_points(
        len(MOUTH_OUTER_INDICES), center=(60.0, 82.0), width=40.0, height=12.0
    )
    landmarks[list(RIGHT_EYE_INDICES)] = _region_points(
        len(RIGHT_EYE_INDICES), center=(42.0, 45.0), width=20.0, height=4.0
    )
    landmarks[list(LEFT_EYE_INDICES)] = _region_points(
        len(LEFT_EYE_INDICES), center=(78.0, 45.0), width=24.0, height=6.0
    )
    return SimpleNamespace(
        bbox=np.array([20.0, 20.0, 100.0, 120.0], dtype=np.float32),
        landmark_2d_106=landmarks,
    )


def test_extract_region_points_uses_central_106_landmark_indices():
    face = _face_with_regions()

    mouth = extract_region_points(face, MOUTH_OUTER_INDICES)
    right_eye = extract_region_points(face, RIGHT_EYE_INDICES)
    left_eye = extract_region_points(face, LEFT_EYE_INDICES)

    assert mouth.shape == (20, 2)
    assert right_eye.shape == (9, 2)
    assert left_eye.shape == (9, 2)
    np.testing.assert_allclose(mouth, face.landmark_2d_106[52:72])
    np.testing.assert_allclose(right_eye, face.landmark_2d_106[33:42])
    np.testing.assert_allclose(left_eye, face.landmark_2d_106[87:96])


def test_expression_helpers_accept_mapping_faces():
    face = _face_with_regions()
    mapping_face = {
        "bbox": face.bbox,
        "landmark_2d_106": face.landmark_2d_106,
    }

    mouth = extract_region_points(mapping_face, MOUTH_OUTER_INDICES)

    assert mouth.shape == (20, 2)
    assert compute_mouth_region_confidence(mapping_face) > 0.8
    assert compute_mouth_open_ratio(mapping_face) == pytest.approx(0.3)
    assert compute_eye_open_ratios(mapping_face) == pytest.approx((0.25, 0.2))
    left_confidence, right_confidence = compute_eye_region_confidences(mapping_face)
    assert left_confidence > 0.8
    assert right_confidence > 0.8


def test_eyebrow_index_conventions_are_centralized():
    assert RIGHT_EYEBROW_INDICES == tuple(range(43, 51))
    assert LEFT_EYEBROW_INDICES == tuple(range(97, 105))


def test_extract_region_points_returns_empty_for_missing_or_short_landmarks():
    assert extract_region_points(None, MOUTH_OUTER_INDICES).shape == (0, 2)
    assert extract_region_points(SimpleNamespace(), MOUTH_OUTER_INDICES).shape == (0, 2)
    short_face = SimpleNamespace(landmark_2d_106=np.zeros((71, 2), dtype=np.float32))

    assert extract_region_points(short_face, MOUTH_OUTER_INDICES).shape == (0, 2)


def test_region_bbox_clips_to_frame_bounds():
    points = np.array([[-5.0, -4.0], [110.0, 90.0]], dtype=np.float32)

    assert compute_region_bbox(points, frame_shape=(80, 100, 3), padding_ratio=0.0) == (
        0,
        0,
        100,
        80,
    )


def test_region_bbox_ignores_non_finite_points_and_pads():
    points = np.array(
        [[10.0, 20.0], [30.0, 50.0], [np.nan, 999.0]], dtype=np.float32
    )

    assert compute_region_bbox(points, frame_shape=(80, 100), padding_ratio=0.1) == (
        8,
        17,
        32,
        53,
    )


def test_region_confidence_degrades_for_non_finite_collapsed_and_implausible_regions():
    face = _face_with_regions()
    mouth = extract_region_points(face, MOUTH_OUTER_INDICES)

    assert compute_region_confidence(mouth, face=face) > 0.8

    with_nan = mouth.copy()
    with_nan[0] = [np.nan, np.nan]
    assert compute_region_confidence(with_nan, face=face) < compute_region_confidence(
        mouth, face=face
    )

    collapsed = np.full_like(mouth, [60.0, 82.0])
    assert compute_region_confidence(collapsed, face=face) == 0.0

    vertically_collapsed = np.column_stack(
        [
            np.full(len(MOUTH_OUTER_INDICES), 60.0),
            np.linspace(62.0, 102.0, len(MOUTH_OUTER_INDICES)),
        ]
    ).astype(np.float32)
    assert compute_region_confidence(vertically_collapsed, face=face) == 0.0

    implausibly_large = mouth * 20.0
    assert compute_region_confidence(implausibly_large, face=face) < 0.2


def test_region_confidence_penalizes_shifted_mouth_outside_face_bbox():
    face = _face_with_regions()
    shifted_mouth = _region_points(
        len(MOUTH_OUTER_INDICES), center=(170.0, 170.0), width=40.0, height=12.0
    )

    assert compute_region_confidence(shifted_mouth, face=face) < 0.35


def test_region_confidence_penalizes_single_zero_filled_mouth_outlier():
    face = _face_with_regions()
    mouth = extract_region_points(face, MOUTH_OUTER_INDICES)
    mouth[0] = [0.0, 0.0]

    assert compute_region_confidence(mouth, face=face) < 0.35


def test_mouth_region_confidence_penalizes_in_bbox_eye_band_shift():
    face = _face_with_regions()
    shifted_mouth = _region_points(
        len(MOUTH_OUTER_INDICES), center=(60.0, 45.0), width=40.0, height=12.0
    )

    assert compute_region_confidence(shifted_mouth, face=face) > 0.8
    assert compute_mouth_region_confidence(shifted_mouth, face=face) < 0.35


def test_region_confidence_is_zero_when_all_points_are_non_finite():
    face = _face_with_regions()
    invalid = np.full((len(MOUTH_OUTER_INDICES), 2), np.nan, dtype=np.float32)

    assert compute_region_confidence(invalid, face=face) == 0.0


def test_mouth_open_ratio_uses_mouth_region_spread():
    face = _face_with_regions()

    assert compute_mouth_open_ratio(face.landmark_2d_106) == pytest.approx(0.3)


def test_eye_open_ratios_return_left_then_right():
    face = _face_with_regions()

    left_ratio, right_ratio = compute_eye_open_ratios(face.landmark_2d_106)

    assert left_ratio == pytest.approx(0.25)
    assert right_ratio == pytest.approx(0.2)


def test_eye_region_confidences_return_left_then_right_and_gate_outliers():
    face = _face_with_regions()

    left_confidence, right_confidence = compute_eye_region_confidences(face)

    assert left_confidence > 0.8
    assert right_confidence > 0.8

    noisy_landmarks = face.landmark_2d_106.copy()
    noisy_landmarks[list(LEFT_EYE_INDICES)[0]] = [0.0, 0.0]
    noisy_face = SimpleNamespace(bbox=face.bbox, landmark_2d_106=noisy_landmarks)

    noisy_left_confidence, noisy_right_confidence = compute_eye_region_confidences(
        noisy_face
    )

    assert noisy_left_confidence < 0.35
    assert noisy_right_confidence == pytest.approx(right_confidence)


def test_open_ratios_return_zero_for_invalid_landmarks():
    short_landmarks = np.zeros((12, 2), dtype=np.float32)

    assert compute_mouth_open_ratio(short_landmarks) == 0.0
    assert compute_eye_open_ratios(short_landmarks) == (0.0, 0.0)
