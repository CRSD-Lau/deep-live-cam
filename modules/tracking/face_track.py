from __future__ import annotations

import copy
import math
from collections.abc import Mapping, MutableMapping
from typing import Any

import numpy as np


_SMOOTHED_ATTRIBUTES = ("bbox", "kps", "landmark_2d_106")


class FaceTracker:
    """Maintain one persistent face track and smooth detector geometry."""

    def __init__(
        self,
        current_weight: float = 0.7,
        jump_reset_ratio: float = 1.2,
        max_missed: int = 1,
        confidence_weight: float = 0.0,
        confidence_reference: float = 0.75,
        confidence_min_weight: float = 0.35,
        min_detection_confidence: float = 0.0,
        prediction_strength: float = 0.0,
        prediction_decay: float = 0.5,
    ) -> None:
        self.current_weight = min(1.0, max(0.0, float(current_weight)))
        self.jump_reset_ratio = max(0.0, float(jump_reset_ratio))
        self.max_missed = max(0, int(max_missed))
        self.confidence_weight = min(1.0, max(0.0, float(confidence_weight)))
        self.confidence_reference = max(1e-6, float(confidence_reference))
        self.confidence_min_weight = min(
            1.0,
            max(0.0, float(confidence_min_weight)),
        )
        self.min_detection_confidence = max(0.0, float(min_detection_confidence))
        self.prediction_strength = min(1.0, max(0.0, float(prediction_strength)))
        self.prediction_decay = min(1.0, max(0.0, float(prediction_decay)))
        self._next_tracking_id = 1
        self._tracked_face: Any | None = None

    def reset(self) -> None:
        self._tracked_face = None

    def update(self, face: Any | None, frame_index: int) -> Any | None:
        if face is None or self._array(face, "bbox") is None:
            return self._update_missing()
        if self._is_weak_detection(face):
            return self._update_missing(ignored_confidence=self._confidence(face))

        if self._tracked_face is None or self._is_large_jump(face):
            return self._start_track(face, frame_index)

        motion_amount = self._motion_amount(self._tracked_face, face)
        current_weight = self._effective_current_weight(face)
        previous_center = self._bbox_center(self._array(self._tracked_face, "bbox"))
        tracked = self._clone_face(face)
        for attr in _SMOOTHED_ATTRIBUTES:
            current_value = self._array(self._tracked_face, attr)
            new_value = self._array(face, attr)
            if current_value is None and new_value is None:
                continue
            if current_value is None:
                smoothed_value = new_value
            elif new_value is None or current_value.shape != new_value.shape:
                smoothed_value = current_value
            else:
                smoothed_value = (
                    current_value * (1.0 - current_weight)
                    + new_value * current_weight
                )
            self._set_value(
                tracked,
                attr,
                smoothed_value.astype(np.float32, copy=True),
            )

        smoothed_bbox = self._array(tracked, "bbox")
        smoothed_center = (
            self._bbox_center(smoothed_bbox) if smoothed_bbox is not None else previous_center
        )
        velocity = np.asarray(
            [
                smoothed_center[0] - previous_center[0],
                smoothed_center[1] - previous_center[1],
            ],
            dtype=np.float32,
        )

        self._attach_metadata(
            tracked,
            tracking_id=self._tracking_id(self._tracked_face),
            missed_frames=0,
            source_frame_index=frame_index,
            detection_confidence=self._confidence(face),
            motion_amount=motion_amount,
            smoothing_weight=current_weight,
            ignored_confidence=None,
            velocity=velocity,
            prediction_active=False,
            prediction_offset=np.zeros(2, dtype=np.float32),
        )
        self._tracked_face = self._clone_face(tracked)
        return tracked

    def _start_track(self, face: Any, frame_index: int) -> Any:
        tracked = self._clone_face(face)
        self._attach_metadata(
            tracked,
            tracking_id=self._next_tracking_id,
            missed_frames=0,
            source_frame_index=frame_index,
            detection_confidence=self._confidence(face),
            motion_amount=0.0,
            smoothing_weight=1.0,
            ignored_confidence=None,
            velocity=np.zeros(2, dtype=np.float32),
            prediction_active=False,
            prediction_offset=np.zeros(2, dtype=np.float32),
        )
        self._next_tracking_id += 1
        self._tracked_face = self._clone_face(tracked)
        return tracked

    def _update_missing(
        self,
        *,
        ignored_confidence: float | None = None,
    ) -> Any | None:
        if self._tracked_face is None:
            return None

        missed_frames = self._missed_frames(self._tracked_face) + 1
        if missed_frames > self.max_missed:
            self._tracked_face = None
            return None

        tracked = self._clone_face(self._tracked_face)
        velocity = self._tracking_velocity(self._tracked_face)
        prediction_offset = self._prediction_offset(velocity, missed_frames)
        prediction_active = prediction_offset is not None
        if prediction_offset is None:
            prediction_offset = np.zeros(2, dtype=np.float32)
        else:
            self._shift_geometry(tracked, prediction_offset)

        predicted_motion = self._offset_motion_amount(self._tracked_face, prediction_offset)
        self._attach_metadata(
            tracked,
            tracking_id=self._tracking_id(self._tracked_face),
            missed_frames=missed_frames,
            source_frame_index=self._get_value(
                self._tracked_face,
                "tracking_source_frame_index",
                None,
            ),
            detection_confidence=self._get_value(
                self._tracked_face, "tracking_detection_confidence", None
            ),
            motion_amount=predicted_motion,
            smoothing_weight=0.0,
            ignored_confidence=ignored_confidence,
            velocity=velocity,
            prediction_active=prediction_active,
            prediction_offset=prediction_offset,
        )
        self._tracked_face = self._clone_face(tracked)
        return tracked

    def _is_large_jump(self, face: Any) -> bool:
        current_bbox = self._array(self._tracked_face, "bbox")
        new_bbox = self._array(face, "bbox")
        if current_bbox is None or new_bbox is None:
            return False

        current_center = self._bbox_center(current_bbox)
        new_center = self._bbox_center(new_bbox)
        distance = math.dist(current_center, new_center)
        threshold = max(
            self._bbox_scale(current_bbox),
            self._bbox_scale(new_bbox),
            1.0,
        ) * self.jump_reset_ratio
        return distance > threshold

    @staticmethod
    def _clone_face(face: Any) -> Any:
        if isinstance(face, Mapping):
            try:
                cloned = type(face)(**dict(face))
            except TypeError:
                cloned = dict(face)
        else:
            cloned = copy.copy(face)
        for attr in _SMOOTHED_ATTRIBUTES:
            value = FaceTracker._get_value(face, attr, None)
            if value is not None:
                FaceTracker._set_value(
                    cloned,
                    attr,
                    np.asarray(value, dtype=np.float32).copy(),
                )
        return cloned

    @staticmethod
    def _attach_metadata(
        face: Any,
        tracking_id: int,
        missed_frames: int,
        source_frame_index: int | None,
        detection_confidence: float | None,
        motion_amount: float,
        smoothing_weight: float,
        ignored_confidence: float | None,
        velocity: np.ndarray,
        prediction_active: bool,
        prediction_offset: np.ndarray,
    ) -> None:
        FaceTracker._set_value(face, "tracking_id", tracking_id)
        FaceTracker._set_value(face, "tracking_missed_frames", missed_frames)
        FaceTracker._set_value(
            face,
            "tracking_source_frame_index",
            source_frame_index,
        )
        FaceTracker._set_value(
            face,
            "tracking_detection_confidence",
            detection_confidence,
        )
        FaceTracker._set_value(face, "tracking_motion_amount", motion_amount)
        FaceTracker._set_value(face, "tracking_smoothing_weight", smoothing_weight)
        FaceTracker._set_value(
            face,
            "tracking_ignored_detection_confidence",
            ignored_confidence,
        )
        FaceTracker._set_value(
            face,
            "tracking_velocity",
            np.asarray(velocity, dtype=np.float32).copy(),
        )
        FaceTracker._set_value(
            face,
            "tracking_prediction_active",
            bool(prediction_active),
        )
        FaceTracker._set_value(
            face,
            "tracking_prediction_offset",
            np.asarray(prediction_offset, dtype=np.float32).copy(),
        )

    def _is_weak_detection(self, face: Any) -> bool:
        if self.min_detection_confidence <= 0.0:
            return False
        confidence = self._confidence(face)
        if confidence is None:
            return False
        return confidence < self.min_detection_confidence

    def _effective_current_weight(self, face: Any) -> float:
        if self.confidence_weight <= 0.0:
            return self.current_weight

        confidence = self._confidence(face)
        if confidence is None:
            return self.current_weight

        confidence_scale = min(
            1.0,
            max(self.confidence_min_weight, float(confidence) / self.confidence_reference),
        )
        factor = (1.0 - self.confidence_weight) + (
            self.confidence_weight * confidence_scale
        )
        return float(min(1.0, max(0.0, self.current_weight * factor)))

    @staticmethod
    def _array(face: Any | None, attr: str) -> np.ndarray | None:
        if face is None:
            return None
        value = FaceTracker._get_value(face, attr, None)
        if value is None:
            return None
        return np.asarray(value, dtype=np.float32)

    @staticmethod
    def _confidence(face: Any) -> float | None:
        confidence = FaceTracker._get_value(face, "det_score", None)
        if confidence is None:
            confidence = FaceTracker._get_value(face, "score", None)
        if confidence is None:
            return None
        return float(confidence)

    @staticmethod
    def _tracking_id(face: Any) -> int:
        return int(FaceTracker._get_value(face, "tracking_id"))

    @staticmethod
    def _missed_frames(face: Any) -> int:
        return int(FaceTracker._get_value(face, "tracking_missed_frames", 0))

    @staticmethod
    def _get_value(face: Any, attr: str, default: Any = None) -> Any:
        if isinstance(face, Mapping) and attr in face:
            return face[attr]
        return getattr(face, attr, default)

    @staticmethod
    def _set_value(face: Any, attr: str, value: Any) -> None:
        if isinstance(face, MutableMapping):
            face[attr] = value
            return
        setattr(face, attr, value)

    @staticmethod
    def _bbox_center(bbox: np.ndarray) -> tuple[float, float]:
        return (
            float((bbox[0] + bbox[2]) * 0.5),
            float((bbox[1] + bbox[3]) * 0.5),
        )

    @staticmethod
    def _bbox_scale(bbox: np.ndarray) -> float:
        width = float(abs(bbox[2] - bbox[0]))
        height = float(abs(bbox[3] - bbox[1]))
        return max(width, height)

    def _prediction_offset(
        self,
        velocity: np.ndarray,
        missed_frames: int,
    ) -> np.ndarray | None:
        if self.prediction_strength <= 0.0:
            return None
        if velocity.shape != (2,) or not np.all(np.isfinite(velocity)):
            return None
        decay = self.prediction_decay ** max(0, missed_frames - 1)
        return (velocity * self.prediction_strength * decay).astype(np.float32)

    @classmethod
    def _shift_geometry(cls, face: Any, offset: np.ndarray) -> None:
        dx, dy = float(offset[0]), float(offset[1])
        for attr in _SMOOTHED_ATTRIBUTES:
            value = cls._array(face, attr)
            if value is None:
                continue
            shifted = value.astype(np.float32, copy=True)
            if attr == "bbox" and shifted.shape == (4,):
                shifted[[0, 2]] += dx
                shifted[[1, 3]] += dy
            elif shifted.ndim >= 2 and shifted.shape[-1] >= 2:
                shifted[..., 0] += dx
                shifted[..., 1] += dy
            else:
                continue
            cls._set_value(face, attr, shifted)

    @classmethod
    def _tracking_velocity(cls, face: Any) -> np.ndarray:
        raw_velocity = cls._get_value(face, "tracking_velocity", None)
        if raw_velocity is None:
            return np.zeros(2, dtype=np.float32)
        velocity = np.asarray(raw_velocity, dtype=np.float32)
        if velocity.shape != (2,) or not np.all(np.isfinite(velocity)):
            return np.zeros(2, dtype=np.float32)
        return velocity

    @classmethod
    def _offset_motion_amount(cls, face: Any, offset: np.ndarray) -> float:
        bbox = cls._array(face, "bbox")
        reference_scale = cls._bbox_scale(bbox) if bbox is not None else 1.0
        distance = float(math.dist((0.0, 0.0), (float(offset[0]), float(offset[1]))))
        return float(min(1.0, max(0.0, distance / max(reference_scale, 1.0))))

    @classmethod
    def _motion_amount(cls, previous_face: Any, current_face: Any) -> float:
        previous_bbox = cls._array(previous_face, "bbox")
        current_bbox = cls._array(current_face, "bbox")
        if previous_bbox is None or current_bbox is None:
            return 0.0
        previous_center = cls._bbox_center(previous_bbox)
        current_center = cls._bbox_center(current_bbox)
        distance = math.dist(previous_center, current_center)
        reference_scale = max(cls._bbox_scale(previous_bbox), 1.0)
        return float(min(1.0, max(0.0, distance / reference_scale)))
