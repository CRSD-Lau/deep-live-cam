"""Expression-aware temporal smoothing helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from modules.expression_regions import (
    compute_eye_region_confidences,
    compute_eye_open_ratios,
    compute_mouth_open_ratio,
    compute_mouth_region_confidence,
)


@dataclass(frozen=True)
class ExpressionSnapshot:
    mouth_open: float
    left_eye_open: float
    right_eye_open: float
    confidence: float
    mouth_confidence: float = 0.0
    left_eye_confidence: float = 0.0
    right_eye_confidence: float = 0.0


def collect_expression_snapshots(
    faces: Iterable[Any] | None,
) -> dict[str, ExpressionSnapshot]:
    """Collect keyed expression snapshots for tracked faces."""
    snapshots: dict[str, ExpressionSnapshot] = {}
    for index, face in enumerate(faces or []):
        snapshot = expression_snapshot(face)
        if snapshot is None:
            continue
        snapshots[_face_key(face, index)] = snapshot
    return snapshots


def expression_snapshot(face: Any) -> ExpressionSnapshot | None:
    """Create a compact mouth/eye geometry snapshot from 106-point landmarks."""
    if face is None:
        return None

    mouth_confidence = compute_mouth_region_confidence(face)
    left_eye_confidence, right_eye_confidence = compute_eye_region_confidences(face)
    confidence = max(
        0.0,
        min(
            1.0,
            max(mouth_confidence, (left_eye_confidence + right_eye_confidence) * 0.5),
        ),
    )
    if confidence <= 0.0:
        return None

    left_eye_open, right_eye_open = compute_eye_open_ratios(face)
    return ExpressionSnapshot(
        mouth_open=compute_mouth_open_ratio(face),
        left_eye_open=left_eye_open,
        right_eye_open=right_eye_open,
        confidence=float(confidence),
        mouth_confidence=float(mouth_confidence),
        left_eye_confidence=float(left_eye_confidence),
        right_eye_confidence=float(right_eye_confidence),
    )


def expression_motion(
    previous: ExpressionSnapshot | None,
    current: ExpressionSnapshot | None,
    *,
    min_confidence: float = 0.25,
    mouth_min_confidence: float | None = None,
    eye_min_confidence: float | None = None,
    unilateral_eye_motion_scale: float = 1.0,
    unilateral_eye_motion_threshold: float = 0.035,
) -> float | None:
    """Return expression change magnitude, or None when confidence is too low."""
    if previous is None or current is None:
        return None
    confidence = min(previous.confidence, current.confidence)
    if confidence < min_confidence:
        return None

    mouth_gate = min_confidence if mouth_min_confidence is None else mouth_min_confidence
    eye_gate = min_confidence if eye_min_confidence is None else eye_min_confidence
    motions: list[float] = []
    if _channel_confidence(previous.mouth_confidence, current.mouth_confidence) >= mouth_gate:
        motions.append(abs(current.mouth_open - previous.mouth_open))
    eye_motions: list[float] = []
    if (
        _channel_confidence(previous.left_eye_confidence, current.left_eye_confidence)
        >= eye_gate
    ):
        eye_motions.append(abs(current.left_eye_open - previous.left_eye_open))
    if (
        _channel_confidence(previous.right_eye_confidence, current.right_eye_confidence)
        >= eye_gate
    ):
        eye_motions.append(abs(current.right_eye_open - previous.right_eye_open))
    if eye_motions:
        motions.append(
            _combined_eye_motion(
                eye_motions,
                unilateral_scale=unilateral_eye_motion_scale,
                unilateral_threshold=unilateral_eye_motion_threshold,
            )
        )
    if not motions:
        return None
    return max(motions)


def expression_temporal_weight(
    base_weight: float,
    previous_snapshots: dict[str, ExpressionSnapshot],
    current_snapshots: dict[str, ExpressionSnapshot],
    *,
    stable_threshold: float = 0.035,
    high_motion_threshold: float = 0.09,
    stable_weight_multiplier: float = 0.86,
    motion_weight_boost: float = 0.22,
    min_confidence: float = 0.25,
    mouth_min_confidence: float | None = None,
    eye_min_confidence: float | None = None,
    unilateral_eye_motion_scale: float = 1.0,
    min_weight: float = 0.08,
    max_weight: float = 0.85,
) -> float:
    """Adapt temporal current-frame weight from expression motion.

    Stable expressions can tolerate more history smoothing. Large mouth/eye
    changes should follow the current frame faster to avoid ghosted speech or
    delayed blinks.
    """
    base = _clamp(float(base_weight), min_weight, max_weight)
    motions = [
        motion
        for key, current in current_snapshots.items()
        if (
            motion := expression_motion(
                previous_snapshots.get(key),
                current,
                min_confidence=min_confidence,
                mouth_min_confidence=mouth_min_confidence,
                eye_min_confidence=eye_min_confidence,
                unilateral_eye_motion_scale=unilateral_eye_motion_scale,
                unilateral_eye_motion_threshold=stable_threshold,
            )
        )
        is not None
    ]
    if not motions:
        return base

    motion = max(motions)
    stable_threshold = max(float(stable_threshold), 0.0)
    high_motion_threshold = max(float(high_motion_threshold), stable_threshold)

    if motion <= stable_threshold:
        return _clamp(base * float(stable_weight_multiplier), min_weight, max_weight)

    boosted = base + max(0.0, float(motion_weight_boost))
    if motion >= high_motion_threshold:
        return _clamp(boosted, min_weight, max_weight)

    span = max(high_motion_threshold - stable_threshold, 1e-6)
    amount = (motion - stable_threshold) / span
    return _clamp(base + (boosted - base) * amount, min_weight, max_weight)


def _face_key(face: Any, index: int) -> str:
    if isinstance(face, Mapping):
        tracking_id = face.get("tracking_id")
    else:
        tracking_id = getattr(face, "tracking_id", None)
    if tracking_id is not None:
        return f"track:{tracking_id}"
    return f"index:{index}"


def _channel_confidence(previous: float, current: float) -> float:
    return float(np.clip(min(previous, current), 0.0, 1.0))


def _combined_eye_motion(
    eye_motions: list[float],
    *,
    unilateral_scale: float,
    unilateral_threshold: float,
) -> float:
    if not eye_motions:
        return 0.0
    strongest = max(float(motion) for motion in eye_motions)
    if len(eye_motions) == 1:
        return strongest * _clamp(unilateral_scale, 0.0, 1.0)

    weakest = min(float(motion) for motion in eye_motions)
    threshold = max(0.0, float(unilateral_threshold))
    if weakest <= threshold < strongest:
        return strongest * _clamp(unilateral_scale, 0.0, 1.0)
    return strongest


def _clamp(value: float, lower: float, upper: float) -> float:
    return float(np.clip(value, lower, upper))
