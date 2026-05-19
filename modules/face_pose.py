"""Lightweight face pose signals for compositing decisions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np


def estimate_profile_score(face: Any | None) -> float:
    """Estimate side-profile severity from InsightFace 5-point keypoints.

    Returns 0.0 for frontal/unknown geometry and approaches 1.0 as the nose
    drifts toward one side of the eye/mouth span.
    """
    kps = _face_array(face, "kps")
    if kps is None or kps.shape[0] < 5 or kps.shape[1] < 2:
        return 0.0

    points = kps[:5, :2].astype(np.float32)
    left_eye, right_eye, nose, left_mouth, right_mouth = points
    eye_width = float(np.linalg.norm(right_eye - left_eye))
    mouth_width = float(np.linalg.norm(right_mouth - left_mouth))
    reference_width = max(eye_width, mouth_width, 1.0)

    eye_center_x = float((left_eye[0] + right_eye[0]) * 0.5)
    mouth_center_x = float((left_mouth[0] + right_mouth[0]) * 0.5)
    center_x = (eye_center_x + mouth_center_x) * 0.5
    offset_score = abs(float(nose[0]) - center_x) / (reference_width * 0.5)

    left_distance = float(np.linalg.norm(nose - left_eye))
    right_distance = float(np.linalg.norm(nose - right_eye))
    asymmetry_score = abs(left_distance - right_distance) / max(
        left_distance + right_distance,
        1.0,
    )

    score = max(offset_score, asymmetry_score * 1.8)
    return float(np.clip(score, 0.0, 1.0))


def _face_array(face: Any | None, attr: str) -> np.ndarray | None:
    if face is None:
        return None
    value = face.get(attr) if isinstance(face, Mapping) else getattr(face, attr, None)
    if value is None:
        return None
    try:
        array = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if array.ndim != 2 or array.shape[1] < 2 or not np.all(np.isfinite(array)):
        return None
    return array[:, :2]
