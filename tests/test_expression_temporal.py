from types import SimpleNamespace

import numpy as np
import pytest

from modules.expression_regions import (
    LEFT_EYE_INDICES,
    MOUTH_OUTER_INDICES,
    RIGHT_EYE_INDICES,
)
from modules.expression_temporal import (
    ExpressionSnapshot,
    collect_expression_snapshots,
    expression_motion,
    expression_snapshot,
    expression_temporal_weight,
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


def _face(
    *,
    mouth_height=12.0,
    left_eye_height=6.0,
    right_eye_height=4.0,
    tracking_id=1,
):
    landmarks = np.zeros((106, 2), dtype=np.float32)
    landmarks[list(MOUTH_OUTER_INDICES)] = _region_points(
        len(MOUTH_OUTER_INDICES),
        center=(60.0, 82.0),
        width=40.0,
        height=mouth_height,
    )
    landmarks[list(RIGHT_EYE_INDICES)] = _region_points(
        len(RIGHT_EYE_INDICES),
        center=(42.0, 45.0),
        width=20.0,
        height=right_eye_height,
    )
    landmarks[list(LEFT_EYE_INDICES)] = _region_points(
        len(LEFT_EYE_INDICES),
        center=(78.0, 45.0),
        width=24.0,
        height=left_eye_height,
    )
    return SimpleNamespace(
        bbox=np.array([20.0, 20.0, 100.0, 120.0], dtype=np.float32),
        landmark_2d_106=landmarks,
        tracking_id=tracking_id,
    )


def test_expression_snapshot_extracts_mouth_and_eye_ratios():
    snapshot = expression_snapshot(_face())

    assert snapshot is not None
    assert snapshot.mouth_open == pytest.approx(0.3)
    assert snapshot.left_eye_open == pytest.approx(0.25)
    assert snapshot.right_eye_open == pytest.approx(0.2)
    assert snapshot.confidence > 0.7
    assert snapshot.mouth_confidence > 0.7
    assert snapshot.left_eye_confidence > 0.7
    assert snapshot.right_eye_confidence > 0.7


def test_expression_motion_detects_mouth_and_blink_changes():
    baseline = expression_snapshot(_face())
    open_mouth = expression_snapshot(_face(mouth_height=30.0))
    blink = expression_snapshot(_face(left_eye_height=1.0))

    assert expression_motion(baseline, open_mouth) > 0.4
    assert expression_motion(baseline, blink) > 0.15


def test_expression_temporal_weight_smooths_stable_and_follows_motion():
    baseline = expression_snapshot(_face())
    open_mouth = expression_snapshot(_face(mouth_height=30.0))
    previous = {"track:1": baseline}

    stable_weight = expression_temporal_weight(
        0.35,
        previous,
        {"track:1": baseline},
        stable_threshold=0.035,
        high_motion_threshold=0.09,
        stable_weight_multiplier=0.86,
        motion_weight_boost=0.22,
    )
    motion_weight = expression_temporal_weight(
        0.35,
        previous,
        {"track:1": open_mouth},
        stable_threshold=0.035,
        high_motion_threshold=0.09,
        stable_weight_multiplier=0.86,
        motion_weight_boost=0.22,
    )

    assert stable_weight == pytest.approx(0.301)
    assert motion_weight == pytest.approx(0.57)


def test_expression_temporal_weight_returns_base_without_matching_history():
    current = expression_snapshot(_face())

    assert expression_temporal_weight(0.35, {}, {"track:1": current}) == pytest.approx(
        0.35
    )


def test_expression_temporal_weight_ignores_low_confidence_snapshots():
    previous = ExpressionSnapshot(0.2, 0.2, 0.2, confidence=0.1)
    current = ExpressionSnapshot(0.8, 0.0, 0.0, confidence=0.1)

    assert expression_temporal_weight(
        0.35, {"track:1": previous}, {"track:1": current}
    ) == pytest.approx(0.35)


def test_expression_temporal_weight_ignores_low_confidence_eye_motion():
    previous = ExpressionSnapshot(
        0.3,
        0.25,
        0.2,
        confidence=0.9,
        mouth_confidence=0.9,
        left_eye_confidence=0.1,
        right_eye_confidence=0.9,
    )
    current = ExpressionSnapshot(
        0.3,
        0.0,
        0.2,
        confidence=0.9,
        mouth_confidence=0.9,
        left_eye_confidence=0.1,
        right_eye_confidence=0.9,
    )

    assert expression_motion(
        previous,
        current,
        min_confidence=0.25,
        eye_min_confidence=0.3,
    ) == pytest.approx(0.0)
    assert expression_temporal_weight(
        0.35,
        {"track:1": previous},
        {"track:1": current},
        stable_threshold=0.035,
        high_motion_threshold=0.09,
        stable_weight_multiplier=0.86,
        motion_weight_boost=0.22,
        eye_min_confidence=0.3,
    ) == pytest.approx(0.301)


def test_expression_temporal_weight_tracks_high_confidence_eye_motion():
    previous = ExpressionSnapshot(
        0.3,
        0.25,
        0.2,
        confidence=0.9,
        mouth_confidence=0.9,
        left_eye_confidence=0.9,
        right_eye_confidence=0.9,
    )
    current = ExpressionSnapshot(
        0.3,
        0.0,
        0.2,
        confidence=0.9,
        mouth_confidence=0.9,
        left_eye_confidence=0.9,
        right_eye_confidence=0.9,
    )

    assert expression_motion(
        previous,
        current,
        min_confidence=0.25,
        eye_min_confidence=0.3,
    ) > 0.2
    assert expression_temporal_weight(
        0.35,
        {"track:1": previous},
        {"track:1": current},
        stable_threshold=0.035,
        high_motion_threshold=0.09,
        stable_weight_multiplier=0.86,
        motion_weight_boost=0.22,
        eye_min_confidence=0.3,
    ) == pytest.approx(0.57)


def test_expression_temporal_weight_can_dampen_unilateral_eye_jitter():
    previous = ExpressionSnapshot(
        0.3,
        0.25,
        0.2,
        confidence=0.9,
        mouth_confidence=0.9,
        left_eye_confidence=0.9,
        right_eye_confidence=0.9,
    )
    current = ExpressionSnapshot(
        0.3,
        0.15,
        0.2,
        confidence=0.9,
        mouth_confidence=0.9,
        left_eye_confidence=0.9,
        right_eye_confidence=0.9,
    )

    assert expression_motion(
        previous,
        current,
        min_confidence=0.25,
        eye_min_confidence=0.3,
        unilateral_eye_motion_scale=0.5,
        unilateral_eye_motion_threshold=0.035,
    ) == pytest.approx(0.05)
    assert expression_temporal_weight(
        0.35,
        {"track:1": previous},
        {"track:1": current},
        stable_threshold=0.035,
        high_motion_threshold=0.09,
        stable_weight_multiplier=0.86,
        motion_weight_boost=0.22,
        eye_min_confidence=0.3,
        unilateral_eye_motion_scale=0.5,
    ) == pytest.approx(0.41)


def test_expression_temporal_weight_keeps_bilateral_blink_response():
    previous = ExpressionSnapshot(
        0.3,
        0.25,
        0.2,
        confidence=0.9,
        mouth_confidence=0.9,
        left_eye_confidence=0.9,
        right_eye_confidence=0.9,
    )
    current = ExpressionSnapshot(
        0.3,
        0.15,
        0.1,
        confidence=0.9,
        mouth_confidence=0.9,
        left_eye_confidence=0.9,
        right_eye_confidence=0.9,
    )

    assert expression_motion(
        previous,
        current,
        min_confidence=0.25,
        eye_min_confidence=0.3,
        unilateral_eye_motion_scale=0.5,
        unilateral_eye_motion_threshold=0.035,
    ) == pytest.approx(0.1)
    assert expression_temporal_weight(
        0.35,
        {"track:1": previous},
        {"track:1": current},
        stable_threshold=0.035,
        high_motion_threshold=0.09,
        stable_weight_multiplier=0.86,
        motion_weight_boost=0.22,
        eye_min_confidence=0.3,
        unilateral_eye_motion_scale=0.5,
    ) == pytest.approx(0.57)


def test_collect_expression_snapshots_uses_tracking_id_and_skips_invalid_faces():
    snapshots = collect_expression_snapshots(
        [_face(tracking_id=42), SimpleNamespace(landmark_2d_106=None)]
    )

    assert list(snapshots) == ["track:42"]
    assert snapshots["track:42"].mouth_open == pytest.approx(0.3)


def test_collect_expression_snapshots_uses_mapping_tracking_id():
    face = _face(tracking_id=99)
    mapping_face = {
        "bbox": face.bbox,
        "landmark_2d_106": face.landmark_2d_106,
        "tracking_id": 99,
    }

    snapshots = collect_expression_snapshots([mapping_face])

    assert list(snapshots) == ["track:99"]
