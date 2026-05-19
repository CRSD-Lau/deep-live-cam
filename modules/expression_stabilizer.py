"""Temporal stabilization helpers for mouth and eye landmarks."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from modules.expression_regions import (
    LEFT_EYE_INDICES,
    LEFT_EYEBROW_INDICES,
    MOUTH_OUTER_INDICES,
    RIGHT_EYE_INDICES,
    RIGHT_EYEBROW_INDICES,
)

EXPRESSION_REGION_INDICES = tuple(
    sorted(
        set(
            MOUTH_OUTER_INDICES
            + LEFT_EYE_INDICES
            + RIGHT_EYE_INDICES
            + LEFT_EYEBROW_INDICES
            + RIGHT_EYEBROW_INDICES
        )
    )
)


def blend_expression_region_landmarks(
    previous_landmarks: np.ndarray | None,
    current_landmarks: np.ndarray,
    *,
    history_weight: float,
    indices: Iterable[int] = EXPRESSION_REGION_INDICES,
) -> np.ndarray:
    """Blend expression-critical landmark points while leaving the face outline current."""
    current = _coerce_landmarks(current_landmarks)
    if current is None:
        try:
            return np.asarray(current_landmarks, dtype=np.float32).copy()
        except (TypeError, ValueError):
            return np.empty((0, 2), dtype=np.float32)

    weight = float(np.clip(history_weight or 0.0, 0.0, 1.0))
    previous = _coerce_landmarks(previous_landmarks)
    if (
        weight <= 0.0
        or previous is None
        or previous.shape != current.shape
    ):
        return current.copy()

    index_array = _valid_indices(indices, current.shape[0])
    if index_array.size == 0:
        return current.copy()

    blended = current.copy()
    blended[index_array, :2] = (
        previous[index_array, :2] * weight
        + current[index_array, :2] * (1.0 - weight)
    )
    return blended


def _coerce_landmarks(value: np.ndarray | None) -> np.ndarray | None:
    if value is None:
        return None
    try:
        landmarks = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if landmarks.ndim != 2 or landmarks.shape[1] < 2:
        return None
    if not np.all(np.isfinite(landmarks[:, :2])):
        return None
    return landmarks[:, :2]


def _valid_indices(indices: Iterable[int], landmark_count: int) -> np.ndarray:
    index_array = np.asarray(tuple(indices), dtype=np.intp)
    if index_array.size == 0:
        return np.empty(0, dtype=np.intp)
    mask = (index_array >= 0) & (index_array < int(landmark_count))
    return index_array[mask]
