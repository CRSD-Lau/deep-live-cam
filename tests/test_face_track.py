from types import SimpleNamespace

import numpy as np

from modules.tracking.face_track import FaceTracker


def make_face(left=0.0, top=0.0, right=10.0, bottom=10.0, score=0.9):
    return SimpleNamespace(
        bbox=np.array([left, top, right, bottom], dtype=np.float32),
        kps=np.array(
            [
                [left + 3.0, top + 4.0],
                [left + 7.0, top + 4.0],
                [left + 5.0, top + 6.0],
                [left + 4.0, top + 8.0],
                [left + 6.0, top + 8.0],
            ],
            dtype=np.float32,
        ),
        landmark_2d_106=np.full((106, 2), [left + 5.0, top + 5.0], dtype=np.float32),
        det_score=score,
    )


def test_first_detection_starts_track_with_metadata():
    tracker = FaceTracker(current_weight=0.5)

    tracked = tracker.update(make_face(), frame_index=12)

    assert tracked.tracking_id == 1
    assert tracked.tracking_missed_frames == 0
    assert tracked.tracking_source_frame_index == 12
    assert tracked.tracking_detection_confidence == 0.9
    assert tracked.tracking_motion_amount == 0.0
    assert tracked.tracking_smoothing_weight == 1.0
    assert tracked.tracking_ignored_detection_confidence is None
    np.testing.assert_allclose(tracked.bbox, [0.0, 0.0, 10.0, 10.0])


def test_nearby_detection_smooths_bbox_and_keypoints():
    tracker = FaceTracker(current_weight=0.25)
    tracker.update(make_face(), frame_index=1)

    tracked = tracker.update(make_face(left=4.0, right=14.0), frame_index=2)

    assert tracked.tracking_id == 1
    assert tracked.tracking_motion_amount == 0.4
    assert tracked.tracking_smoothing_weight == 0.25
    np.testing.assert_allclose(tracked.bbox, [1.0, 0.0, 11.0, 10.0])
    np.testing.assert_allclose(tracked.kps[0], [4.0, 4.0])
    np.testing.assert_allclose(tracked.landmark_2d_106[0], [6.0, 5.0])


def test_motion_amount_uses_previous_face_scale():
    tracker = FaceTracker(current_weight=1.0, jump_reset_ratio=20.0)
    tracker.update(make_face(), frame_index=1)

    tracked = tracker.update(
        make_face(left=12.0, top=0.0, right=112.0, bottom=100.0),
        frame_index=2,
    )

    assert tracked.tracking_motion_amount == 1.0


def test_low_confidence_detection_reduces_geometry_update_weight():
    high_confidence_tracker = FaceTracker(
        current_weight=0.5,
        jump_reset_ratio=10.0,
        confidence_weight=1.0,
        confidence_reference=1.0,
        confidence_min_weight=0.2,
    )
    low_confidence_tracker = FaceTracker(
        current_weight=0.5,
        jump_reset_ratio=10.0,
        confidence_weight=1.0,
        confidence_reference=1.0,
        confidence_min_weight=0.2,
    )
    high_confidence_tracker.update(make_face(score=1.0), frame_index=1)
    low_confidence_tracker.update(make_face(score=1.0), frame_index=1)

    high = high_confidence_tracker.update(
        make_face(left=10.0, right=20.0, score=1.0),
        frame_index=2,
    )
    low = low_confidence_tracker.update(
        make_face(left=10.0, right=20.0, score=0.25),
        frame_index=2,
    )

    assert high.tracking_smoothing_weight == 0.5
    assert low.tracking_smoothing_weight == 0.125
    np.testing.assert_allclose(high.bbox, [5.0, 0.0, 15.0, 10.0])
    np.testing.assert_allclose(low.bbox, [1.25, 0.0, 11.25, 10.0])


def test_confidence_weighting_disabled_preserves_base_weight():
    tracker = FaceTracker(
        current_weight=0.5,
        jump_reset_ratio=10.0,
        confidence_weight=0.0,
        confidence_reference=1.0,
        confidence_min_weight=0.2,
    )
    tracker.update(make_face(score=1.0), frame_index=1)

    tracked = tracker.update(
        make_face(left=10.0, right=20.0, score=0.1),
        frame_index=2,
    )

    assert tracked.tracking_smoothing_weight == 0.5
    np.testing.assert_allclose(tracked.bbox, [5.0, 0.0, 15.0, 10.0])


def test_weak_detection_holds_previous_track_instead_of_updating_geometry():
    tracker = FaceTracker(
        current_weight=1.0,
        max_missed=2,
        min_detection_confidence=0.5,
    )
    tracker.update(make_face(score=0.9), frame_index=1)

    held = tracker.update(
        make_face(left=10.0, right=20.0, score=0.3),
        frame_index=2,
    )

    assert held is not None
    assert held.tracking_id == 1
    assert held.tracking_missed_frames == 1
    assert held.tracking_smoothing_weight == 0.0
    assert held.tracking_ignored_detection_confidence == 0.3
    np.testing.assert_allclose(held.bbox, [0.0, 0.0, 10.0, 10.0])


def test_weak_first_detection_does_not_start_track():
    tracker = FaceTracker(min_detection_confidence=0.5)

    tracked = tracker.update(make_face(score=0.3), frame_index=1)

    assert tracked is None


def test_min_detection_confidence_disabled_accepts_weak_detection():
    tracker = FaceTracker(
        current_weight=1.0,
        min_detection_confidence=0.0,
    )

    tracked = tracker.update(make_face(score=0.1), frame_index=1)

    assert tracked is not None
    assert tracked.tracking_detection_confidence == 0.1


def test_large_jump_resets_to_new_track():
    tracker = FaceTracker(current_weight=0.25, jump_reset_ratio=0.4)
    tracker.update(make_face(), frame_index=1)

    tracked = tracker.update(make_face(left=100.0, right=110.0), frame_index=2)

    assert tracked.tracking_id == 2
    assert tracked.tracking_motion_amount == 0.0
    np.testing.assert_allclose(tracked.bbox, [100.0, 0.0, 110.0, 10.0])


def test_missing_detection_reuses_recent_track_then_expires():
    tracker = FaceTracker(max_missed=1)
    tracker.update(make_face(), frame_index=1)

    held = tracker.update(None, frame_index=2)
    expired = tracker.update(None, frame_index=3)

    assert held is not None
    assert held.tracking_missed_frames == 1
    assert held.tracking_motion_amount == 0.0
    assert held.tracking_smoothing_weight == 0.0
    assert held.tracking_ignored_detection_confidence is None
    assert held.tracking_prediction_active is False
    assert expired is None


def test_missing_detection_predicts_short_track_motion_with_decay():
    tracker = FaceTracker(
        current_weight=1.0,
        jump_reset_ratio=10.0,
        max_missed=2,
        prediction_strength=1.0,
        prediction_decay=0.5,
    )
    tracker.update(make_face(), frame_index=1)
    tracked = tracker.update(make_face(left=4.0, right=14.0), frame_index=2)

    first_hold = tracker.update(None, frame_index=3)
    second_hold = tracker.update(None, frame_index=4)

    np.testing.assert_allclose(tracked.tracking_velocity, [4.0, 0.0])
    assert first_hold.tracking_prediction_active is True
    assert first_hold.tracking_missed_frames == 1
    assert first_hold.tracking_motion_amount == 0.4
    np.testing.assert_allclose(first_hold.tracking_prediction_offset, [4.0, 0.0])
    np.testing.assert_allclose(first_hold.bbox, [8.0, 0.0, 18.0, 10.0])
    assert second_hold.tracking_prediction_active is True
    assert second_hold.tracking_missed_frames == 2
    assert second_hold.tracking_motion_amount == 0.2
    np.testing.assert_allclose(second_hold.tracking_prediction_offset, [2.0, 0.0])
    np.testing.assert_allclose(second_hold.bbox, [10.0, 0.0, 20.0, 10.0])


def test_weak_detection_can_use_prediction_without_accepting_geometry():
    tracker = FaceTracker(
        current_weight=1.0,
        jump_reset_ratio=10.0,
        max_missed=1,
        min_detection_confidence=0.5,
        prediction_strength=0.5,
        prediction_decay=0.5,
    )
    tracker.update(make_face(), frame_index=1)
    tracker.update(make_face(left=4.0, right=14.0), frame_index=2)

    held = tracker.update(make_face(left=100.0, right=110.0, score=0.2), frame_index=3)

    assert held.tracking_prediction_active is True
    assert held.tracking_ignored_detection_confidence == 0.2
    np.testing.assert_allclose(held.tracking_prediction_offset, [2.0, 0.0])
    np.testing.assert_allclose(held.bbox, [6.0, 0.0, 16.0, 10.0])


class DictBackedFace(dict):
    __setstate__ = None

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


def test_tracker_supports_dict_backed_face_objects():
    tracker = FaceTracker()
    face = DictBackedFace(
        bbox=np.array([0.0, 0.0, 10.0, 10.0], dtype=np.float32),
        kps=np.zeros((5, 2), dtype=np.float32),
        det_score=0.8,
    )

    tracked = tracker.update(face, frame_index=1)

    assert tracked.tracking_id == 1
    np.testing.assert_allclose(tracked.bbox, [0.0, 0.0, 10.0, 10.0])


def test_tracker_supports_plain_mapping_face_objects():
    tracker = FaceTracker(current_weight=1.0)
    face = {
        "bbox": np.array([0.0, 0.0, 10.0, 10.0], dtype=np.float32),
        "kps": np.zeros((5, 2), dtype=np.float32),
        "det_score": 0.8,
    }

    first = tracker.update(face, frame_index=1)
    second = tracker.update(
        {
            "bbox": np.array([3.0, 0.0, 13.0, 10.0], dtype=np.float32),
            "kps": np.zeros((5, 2), dtype=np.float32),
            "det_score": 0.7,
        },
        frame_index=2,
    )

    assert first["tracking_id"] == 1
    assert first["tracking_motion_amount"] == 0.0
    assert second["tracking_id"] == 1
    assert second["tracking_detection_confidence"] == 0.7
    assert second["tracking_motion_amount"] == 0.3
    np.testing.assert_allclose(second["bbox"], [3.0, 0.0, 13.0, 10.0])
