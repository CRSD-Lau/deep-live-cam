"""Lightweight landmark geometry helpers for mouth and eye regions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Iterable

import numpy as np

MOUTH_OUTER_INDICES = tuple(range(52, 72))
MOUTH_FULL_INDICES = MOUTH_OUTER_INDICES
RIGHT_EYE_INDICES = tuple(range(33, 42))
LEFT_EYE_INDICES = tuple(range(87, 96))
RIGHT_EYEBROW_INDICES = tuple(range(43, 51))
LEFT_EYEBROW_INDICES = tuple(range(97, 105))
MOUTH_EXPECTED_CENTER_X_RANGE = (0.20, 0.80)
MOUTH_EXPECTED_CENTER_Y_RANGE = (0.48, 0.90)

EMPTY_BBOX = (0, 0, 0, 0)
_EMPTY_POINTS = np.empty((0, 2), dtype=np.float32)
_EPSILON = 1e-6


def extract_region_points(face_or_landmarks: Any, indices: Iterable[int]) -> np.ndarray:
    """Return selected 106-landmark points as float32, or an empty array."""
    landmarks = _coerce_landmarks(face_or_landmarks)
    index_array = np.asarray(tuple(indices), dtype=np.intp)
    if landmarks is None or index_array.size == 0:
        return _empty_points()
    if np.any(index_array < 0) or int(np.max(index_array)) >= landmarks.shape[0]:
        return _empty_points()
    return landmarks[index_array, :2].astype(np.float32, copy=True)


def compute_region_bbox(
    points: Any,
    frame_shape: tuple[int, ...],
    padding_ratio: float = 0.0,
) -> tuple[int, int, int, int]:
    """Compute an exclusive clipped bbox for finite region points."""
    finite_points = _finite_points(points)
    if finite_points.size == 0 or len(frame_shape) < 2:
        return EMPTY_BBOX

    frame_h = int(frame_shape[0])
    frame_w = int(frame_shape[1])
    if frame_h <= 0 or frame_w <= 0:
        return EMPTY_BBOX

    min_xy = np.min(finite_points, axis=0)
    max_xy = np.max(finite_points, axis=0)
    spread = np.maximum(max_xy - min_xy, 0.0)
    padding = spread * max(float(padding_ratio), 0.0)

    min_x = int(np.clip(np.floor(min_xy[0] - padding[0]), 0, frame_w))
    min_y = int(np.clip(np.floor(min_xy[1] - padding[1]), 0, frame_h))
    max_x = int(np.clip(np.ceil(max_xy[0] + padding[0]), 0, frame_w))
    max_y = int(np.clip(np.ceil(max_xy[1] + padding[1]), 0, frame_h))

    if max_x <= min_x or max_y <= min_y:
        return EMPTY_BBOX
    return min_x, min_y, max_x, max_y


def compute_region_confidence(
    points: Any,
    face: Any | None = None,
    min_span_ratio: float = 0.015,
    max_span_ratio: float = 0.65,
) -> float:
    """Score finite, plausibly sized region landmarks from 0.0 to 1.0."""
    point_array = _coerce_points(points)
    if point_array.size == 0:
        return 0.0

    finite_mask = np.all(np.isfinite(point_array), axis=1)
    finite_count = int(np.count_nonzero(finite_mask))
    if finite_count == 0:
        return 0.0

    finite_points = point_array[finite_mask]
    region_points, outlier_penalty = _robust_region_points(finite_points)
    if region_points.size == 0:
        return 0.0

    spread = np.ptp(region_points, axis=0)
    width_span = float(spread[0])
    if not np.isfinite(width_span) or width_span <= _EPSILON:
        return 0.0

    region_span = float(np.max(spread))
    if not np.isfinite(region_span) or region_span <= _EPSILON:
        return 0.0

    reference_span = _reference_span(face)
    if reference_span <= _EPSILON:
        reference_span = region_span

    location_penalty = _face_location_penalty(region_points, face, reference_span)
    if location_penalty <= _EPSILON:
        return 0.0

    span_ratio = region_span / reference_span
    if span_ratio <= _EPSILON:
        return 0.0

    min_span_ratio = max(float(min_span_ratio), _EPSILON)
    max_span_ratio = max(float(max_span_ratio), min_span_ratio)
    if span_ratio < min_span_ratio:
        plausibility = span_ratio / min_span_ratio
    elif span_ratio > max_span_ratio:
        plausibility = max_span_ratio / span_ratio
    else:
        plausibility = 1.0

    finite_ratio = finite_count / point_array.shape[0]
    score = finite_ratio * outlier_penalty * location_penalty * plausibility
    return float(np.clip(score, 0.0, 1.0))


def compute_mouth_open_ratio(face_or_landmarks: Any) -> float:
    """Return mouth height/width from 106 landmarks, or 0.0 when invalid."""
    return _open_ratio(extract_region_points(face_or_landmarks, MOUTH_OUTER_INDICES))


def compute_mouth_region_confidence(
    face_or_points: Any,
    face: Any | None = None,
) -> float:
    """Score mouth landmarks, including lower-face anatomical plausibility."""
    if face is None and (
        hasattr(face_or_points, "landmark_2d_106")
        or (
            isinstance(face_or_points, Mapping)
            and "landmark_2d_106" in face_or_points
        )
    ):
        face = face_or_points
        points = extract_region_points(face_or_points, MOUTH_OUTER_INDICES)
    else:
        points = face_or_points

    base_score = compute_region_confidence(points, face=face)
    if base_score <= 0.0:
        return 0.0

    point_array = _coerce_points(points)
    finite_points = _finite_points(point_array)
    if finite_points.size == 0:
        return 0.0

    region_points, _outlier_penalty = _robust_region_points(finite_points)
    if region_points.size == 0:
        return 0.0

    anatomical_penalty = _relative_center_penalty(
        region_points,
        face,
        x_range=MOUTH_EXPECTED_CENTER_X_RANGE,
        y_range=MOUTH_EXPECTED_CENTER_Y_RANGE,
    )
    return float(np.clip(base_score * anatomical_penalty, 0.0, 1.0))


def compute_eye_open_ratios(face_or_landmarks: Any) -> tuple[float, float]:
    """Return left-eye then right-eye height/width ratios."""
    left_ratio = _open_ratio(extract_region_points(face_or_landmarks, LEFT_EYE_INDICES))
    right_ratio = _open_ratio(extract_region_points(face_or_landmarks, RIGHT_EYE_INDICES))
    return left_ratio, right_ratio


def compute_eye_region_confidences(
    face_or_landmarks: Any,
    face: Any | None = None,
) -> tuple[float, float]:
    """Return left-eye then right-eye landmark confidence scores."""
    if face is None and (
        hasattr(face_or_landmarks, "landmark_2d_106")
        or (
            isinstance(face_or_landmarks, Mapping)
            and "landmark_2d_106" in face_or_landmarks
        )
    ):
        face = face_or_landmarks

    left_confidence = compute_region_confidence(
        extract_region_points(face_or_landmarks, LEFT_EYE_INDICES),
        face=face,
        min_span_ratio=0.005,
        max_span_ratio=0.45,
    )
    right_confidence = compute_region_confidence(
        extract_region_points(face_or_landmarks, RIGHT_EYE_INDICES),
        face=face,
        min_span_ratio=0.005,
        max_span_ratio=0.45,
    )
    return left_confidence, right_confidence


def _coerce_landmarks(face_or_landmarks: Any) -> np.ndarray | None:
    if isinstance(face_or_landmarks, Mapping):
        value = face_or_landmarks.get("landmark_2d_106")
    else:
        value = getattr(face_or_landmarks, "landmark_2d_106", face_or_landmarks)
    if value is None:
        return None
    try:
        landmarks = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if landmarks.ndim != 2 or landmarks.shape[1] < 2:
        return None
    return landmarks[:, :2]


def _coerce_points(points: Any) -> np.ndarray:
    try:
        point_array = np.asarray(points, dtype=np.float32)
    except (TypeError, ValueError):
        return _empty_points()
    if point_array.ndim != 2 or point_array.shape[1] < 2 or point_array.shape[0] == 0:
        return _empty_points()
    return point_array[:, :2]


def _finite_points(points: Any) -> np.ndarray:
    point_array = _coerce_points(points)
    if point_array.size == 0:
        return _empty_points()
    finite_mask = np.all(np.isfinite(point_array), axis=1)
    if not np.any(finite_mask):
        return _empty_points()
    return point_array[finite_mask]


def _reference_span(face: Any | None) -> float:
    bbox_span = _bbox_reference_span(face)
    if bbox_span > _EPSILON:
        return bbox_span

    landmarks = _coerce_landmarks(face)
    if landmarks is None:
        return 0.0
    finite_landmarks = _finite_points(landmarks)
    if finite_landmarks.size == 0:
        return 0.0
    spread = np.ptp(finite_landmarks, axis=0)
    span = float(np.max(spread))
    if np.isfinite(span):
        return span
    return 0.0


def _robust_region_points(points: np.ndarray) -> tuple[np.ndarray, float]:
    if points.shape[0] < 4:
        return points, 1.0

    center = np.median(points, axis=0)
    distances = np.linalg.norm(points - center, axis=1)
    median_distance = float(np.median(distances))
    mad = float(np.median(np.abs(distances - median_distance)))
    threshold = median_distance + max(3.0 * mad, 1.5 * median_distance, 1.0)
    inlier_mask = distances <= threshold
    inlier_count = int(np.count_nonzero(inlier_mask))
    if inlier_count < max(3, points.shape[0] // 2):
        return _empty_points(), 0.0
    if inlier_count == points.shape[0]:
        return points, 1.0

    # A single finite point far from the robust cluster can distort the polygon
    # used by mouth paste-back, so treat spatial outliers as a strong gate signal.
    return points[inlier_mask], min(0.25, inlier_count / points.shape[0])


def _face_location_penalty(
    points: np.ndarray,
    face: Any | None,
    reference_span: float,
) -> float:
    bounds = _face_bounds(face)
    if bounds is None or reference_span <= _EPSILON:
        return 1.0

    x1, y1, x2, y2 = bounds
    if x2 <= x1 or y2 <= y1:
        return 1.0

    margin = reference_span * 0.10
    inside_mask = (
        (points[:, 0] >= x1 - margin)
        & (points[:, 0] <= x2 + margin)
        & (points[:, 1] >= y1 - margin)
        & (points[:, 1] <= y2 + margin)
    )
    containment = float(np.count_nonzero(inside_mask) / points.shape[0])
    if containment <= _EPSILON:
        return 0.0

    center = np.mean(points, axis=0)
    dx = max(float(x1 - center[0]), 0.0, float(center[0] - x2))
    dy = max(float(y1 - center[1]), 0.0, float(center[1] - y2))
    distance = float(np.hypot(dx, dy))
    distance_penalty = 1.0
    if distance > 0.0:
        distance_penalty = max(0.0, 1.0 - distance / max(reference_span * 0.35, 1.0))

    return float(np.clip(containment * distance_penalty, 0.0, 1.0))


def _relative_center_penalty(
    points: np.ndarray,
    face: Any | None,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    falloff: float = 0.12,
) -> float:
    bounds = _face_bounds(face)
    if bounds is None:
        return 1.0

    x1, y1, x2, y2 = bounds
    width = x2 - x1
    height = y2 - y1
    if width <= _EPSILON or height <= _EPSILON:
        return 1.0

    center = np.mean(points, axis=0)
    relative_x = float((center[0] - x1) / width)
    relative_y = float((center[1] - y1) / height)
    x_penalty = _range_penalty(relative_x, x_range, falloff)
    y_penalty = _range_penalty(relative_y, y_range, falloff)
    return float(np.clip(x_penalty * y_penalty, 0.0, 1.0))


def _range_penalty(
    value: float,
    allowed_range: tuple[float, float],
    falloff: float,
) -> float:
    lower, upper = allowed_range
    if lower <= value <= upper:
        return 1.0
    distance = lower - value if value < lower else value - upper
    return float(np.clip(1.0 - distance / max(falloff, _EPSILON), 0.0, 1.0))


def _face_bounds(face: Any | None) -> tuple[float, float, float, float] | None:
    bbox = _face_value(face, "bbox")
    if bbox is not None:
        try:
            bbox_array = np.asarray(bbox, dtype=np.float32).reshape(-1)
        except (TypeError, ValueError):
            bbox_array = np.empty(0, dtype=np.float32)
        if bbox_array.size >= 4 and np.all(np.isfinite(bbox_array[:4])):
            x1, y1, x2, y2 = map(float, bbox_array[:4])
            return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)

    landmarks = _coerce_landmarks(face)
    if landmarks is None:
        return None
    finite_landmarks = _finite_points(landmarks)
    if finite_landmarks.size == 0:
        return None
    min_xy = np.min(finite_landmarks, axis=0)
    max_xy = np.max(finite_landmarks, axis=0)
    return float(min_xy[0]), float(min_xy[1]), float(max_xy[0]), float(max_xy[1])


def _bbox_reference_span(face: Any | None) -> float:
    bbox = _face_value(face, "bbox")
    if bbox is None:
        return 0.0
    try:
        bbox_array = np.asarray(bbox, dtype=np.float32).reshape(-1)
    except (TypeError, ValueError):
        return 0.0
    if bbox_array.size < 4 or not np.all(np.isfinite(bbox_array[:4])):
        return 0.0
    width = abs(float(bbox_array[2] - bbox_array[0]))
    height = abs(float(bbox_array[3] - bbox_array[1]))
    span = max(width, height)
    if np.isfinite(span):
        return span
    return 0.0


def _face_value(face: Any | None, attr: str) -> Any:
    if isinstance(face, Mapping):
        return face.get(attr)
    return getattr(face, attr, None)


def _open_ratio(points: Any) -> float:
    finite_points = _finite_points(points)
    if finite_points.shape[0] < 2:
        return 0.0
    min_xy = np.min(finite_points, axis=0)
    max_xy = np.max(finite_points, axis=0)
    width = float(max_xy[0] - min_xy[0])
    height = float(max_xy[1] - min_xy[1])
    if not np.isfinite(width) or not np.isfinite(height) or width <= _EPSILON:
        return 0.0
    return max(height, 0.0) / width


def _empty_points() -> np.ndarray:
    return _EMPTY_POINTS.copy()
