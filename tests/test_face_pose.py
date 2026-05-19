from types import SimpleNamespace

import numpy as np

from modules.face_pose import estimate_profile_score


def test_estimate_profile_score_is_low_for_centered_frontal_keypoints():
    face = SimpleNamespace(kps=_kps(nose_x=60.0))

    assert estimate_profile_score(face) < 0.05


def test_estimate_profile_score_increases_when_nose_shifts_sideways():
    frontal = SimpleNamespace(kps=_kps(nose_x=60.0))
    profile = SimpleNamespace(kps=_kps(nose_x=82.0))

    assert estimate_profile_score(profile) > estimate_profile_score(frontal)
    assert estimate_profile_score(profile) > 0.8


def test_estimate_profile_score_accepts_mapping_faces_and_invalid_bypasses():
    assert estimate_profile_score({"kps": _kps(nose_x=78.0)}) > 0.6
    assert estimate_profile_score({"kps": np.zeros((4, 2), dtype=np.float32)}) == 0.0
    assert estimate_profile_score(None) == 0.0


def _kps(nose_x):
    return np.array(
        [
            [40.0, 40.0],
            [80.0, 40.0],
            [nose_x, 60.0],
            [46.0, 84.0],
            [74.0, 84.0],
        ],
        dtype=np.float32,
    )
