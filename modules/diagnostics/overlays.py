"""Debug overlays for visual QA and live pipeline diagnostics."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import cv2
import numpy as np

from modules.expression_regions import (
    LEFT_EYE_INDICES,
    MOUTH_OUTER_INDICES,
    RIGHT_EYE_INDICES,
    compute_eye_open_ratios,
    compute_eye_region_confidences,
    compute_mouth_open_ratio,
    compute_mouth_region_confidence,
    compute_region_bbox,
    extract_region_points,
)

AVAILABLE_OVERLAY_LAYERS = (
    "bbox",
    "kps",
    "landmarks",
    "mouth",
    "eyes",
    "mask",
    "profile",
)
DEFAULT_OVERLAY_LAYERS = ("bbox", "kps", "profile")
_LAYER_SET = set(AVAILABLE_OVERLAY_LAYERS)


def parse_overlay_layers(value: str | None) -> list[str]:
    """Parse comma-separated overlay layer names."""
    if value is None:
        return list(DEFAULT_OVERLAY_LAYERS)
    if not value.strip():
        raise ValueError("overlay layers cannot be blank")

    layers: list[str] = []
    for token in value.split(","):
        layer = token.strip().lower()
        if not layer:
            raise ValueError("overlay layers contain a blank entry")
        if layer == "all":
            for available in AVAILABLE_OVERLAY_LAYERS:
                if available not in layers:
                    layers.append(available)
            continue
        if layer not in _LAYER_SET:
            choices = ", ".join(AVAILABLE_OVERLAY_LAYERS)
            raise ValueError(f"unknown overlay layer '{layer}'. Choose from: {choices}")
        if layer not in layers:
            layers.append(layer)
    return layers


def draw_diagnostic_overlay(
    frame: np.ndarray,
    faces: Iterable[Any],
    *,
    layers: Sequence[str] | None = None,
    profile_name: str | None = None,
    masks: Iterable[np.ndarray | None] | None = None,
) -> np.ndarray:
    """Draw selected diagnostic layers on a frame copy."""
    if frame is None or not hasattr(frame, "shape"):
        raise ValueError("expected an image frame")
    selected_layers = set(layers or DEFAULT_OVERLAY_LAYERS)
    output = _as_bgr_uint8(frame)
    face_list = [face for face in faces if face is not None]

    if "mask" in selected_layers and masks is not None:
        for mask in masks:
            _draw_mask(output, mask)

    for index, face in enumerate(face_list):
        color = _face_color(index)
        bbox = _face_array(face, "bbox")
        if "bbox" in selected_layers and bbox is not None:
            _draw_bbox(output, bbox, color, _face_label(face, index))
        if "kps" in selected_layers:
            _draw_points(output, _face_array(face, "kps"), color, radius=3)
        if "landmarks" in selected_layers:
            _draw_points(
                output,
                _face_array(face, "landmark_2d_106"),
                (80, 220, 255),
                radius=1,
            )
        if "mouth" in selected_layers:
            _draw_mouth_overlay(output, face)
        if "eyes" in selected_layers:
            _draw_eyes_overlay(output, face)

    if "profile" in selected_layers:
        _draw_profile_panel(output, profile_name, len(face_list), selected_layers)
    return output


def _as_bgr_uint8(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    if frame.ndim != 3 or frame.shape[2] not in (3, 4):
        raise ValueError(f"expected BGR/BGRA frame, got shape {frame.shape}")
    if frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    if frame.dtype == np.uint8:
        return frame.copy()
    return np.clip(frame, 0, 255).astype(np.uint8)


def _face_array(face: Any, attr: str) -> np.ndarray | None:
    value = getattr(face, attr, None)
    if value is None and isinstance(face, dict):
        value = face.get(attr)
    if value is None:
        return None
    array = np.asarray(value, dtype=np.float32)
    if array.size == 0 or not np.all(np.isfinite(array)):
        return None
    return array


def _draw_bbox(frame: np.ndarray, bbox: np.ndarray, color: tuple[int, int, int], label: str) -> None:
    values = bbox.reshape(-1)
    if values.size != 4:
        return
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = values
    left = int(np.clip(np.floor(min(x1, x2)), 0, width - 1))
    right = int(np.clip(np.ceil(max(x1, x2)), 0, width - 1))
    top = int(np.clip(np.floor(min(y1, y2)), 0, height - 1))
    bottom = int(np.clip(np.ceil(max(y1, y2)), 0, height - 1))
    if right <= left or bottom <= top:
        return
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2, cv2.LINE_AA)
    _draw_label(frame, label, left, max(0, top - 6), color)


def _draw_points(
    frame: np.ndarray,
    points: np.ndarray | None,
    color: tuple[int, int, int],
    *,
    radius: int,
) -> None:
    if points is None:
        return
    points = points.reshape(-1, 2)
    height, width = frame.shape[:2]
    for x, y in points:
        xi, yi = int(round(float(x))), int(round(float(y)))
        if 0 <= xi < width and 0 <= yi < height:
            cv2.circle(frame, (xi, yi), radius, color, -1, cv2.LINE_AA)


def _draw_mask(frame: np.ndarray, mask: np.ndarray | None) -> None:
    if mask is None:
        return
    mask_arr = np.asarray(mask)
    if mask_arr.shape[:2] != frame.shape[:2] or mask_arr.size == 0:
        return
    if mask_arr.ndim == 3:
        mask_arr = mask_arr.mean(axis=2)
    alpha = np.clip(mask_arr.astype(np.float32) / 255.0, 0.0, 1.0) * 0.35
    if float(alpha.max()) <= 0.0:
        return
    tint = np.zeros_like(frame, dtype=np.uint8)
    tint[:, :, 1] = 255
    blended = cv2.addWeighted(frame, 1.0, tint, 0.35, 0)
    alpha_3c = alpha[:, :, None]
    frame[:] = np.clip(
        blended.astype(np.float32) * alpha_3c
        + frame.astype(np.float32) * (1.0 - alpha_3c),
        0,
        255,
    ).astype(np.uint8)


def _draw_mouth_overlay(frame: np.ndarray, face: Any) -> None:
    points = extract_region_points(face, MOUTH_OUTER_INDICES)
    if points.size == 0:
        return
    label = (
        f"mouth open={compute_mouth_open_ratio(face):.2f} "
        f"conf={compute_mouth_region_confidence(face):.2f}"
    )
    _draw_region_overlay(
        frame,
        points,
        color=(80, 170, 255),
        label=label,
        closed=True,
    )


def _draw_eyes_overlay(frame: np.ndarray, face: Any) -> None:
    left_points = extract_region_points(face, LEFT_EYE_INDICES)
    right_points = extract_region_points(face, RIGHT_EYE_INDICES)
    left_open, right_open = compute_eye_open_ratios(face)
    left_confidence, right_confidence = compute_eye_region_confidences(face)
    _draw_region_overlay(
        frame,
        left_points,
        color=(255, 180, 80),
        label=(
            f"L eye open={left_open:.2f} "
            f"conf={left_confidence:.2f}"
        ),
        closed=True,
    )
    _draw_region_overlay(
        frame,
        right_points,
        color=(255, 220, 80),
        label=(
            f"R eye open={right_open:.2f} "
            f"conf={right_confidence:.2f}"
        ),
        closed=True,
    )


def _draw_region_overlay(
    frame: np.ndarray,
    points: np.ndarray,
    *,
    color: tuple[int, int, int],
    label: str,
    closed: bool,
) -> None:
    if points is None or points.size == 0:
        return
    points = points.reshape(-1, 2)
    bbox = compute_region_bbox(points, frame.shape, padding_ratio=0.25)
    if bbox == (0, 0, 0, 0):
        return
    draw_points = np.rint(points).astype(np.int32).reshape(-1, 1, 2)
    cv2.polylines(frame, [draw_points], closed, color, 1, cv2.LINE_AA)
    _draw_points(frame, points, color, radius=2)
    _draw_bbox(frame, np.array(bbox, dtype=np.float32), color, label)


def _draw_profile_panel(
    frame: np.ndarray,
    profile_name: str | None,
    face_count: int,
    layers: set[str],
) -> None:
    text = f"profile={profile_name or 'unknown'} faces={face_count} layers={','.join(sorted(layers))}"
    (text_w, text_h), baseline = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        1,
    )
    cv2.rectangle(frame, (8, 8), (text_w + 18, text_h + baseline + 18), (12, 12, 12), -1)
    cv2.putText(
        frame,
        text,
        (13, text_h + 13),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        (235, 235, 235),
        1,
        cv2.LINE_AA,
    )


def _draw_label(frame: np.ndarray, label: str, x: int, y: int, color: tuple[int, int, int]) -> None:
    (text_w, text_h), baseline = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        1,
    )
    top = max(0, y - text_h - baseline - 4)
    right = min(frame.shape[1] - 1, x + text_w + 8)
    cv2.rectangle(frame, (x, top), (right, y + 2), (10, 10, 10), -1)
    cv2.putText(
        frame,
        label,
        (x + 4, y - baseline - 1),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color,
        1,
        cv2.LINE_AA,
    )


def _face_label(face: Any, index: int) -> str:
    label = f"face {index + 1}"
    tracking_id = _face_value(face, "tracking_id")
    if tracking_id is not None:
        label += f" id={tracking_id}"
    det_score = _face_value(face, "det_score")
    if det_score is not None:
        label += f" score={float(det_score):.2f}"
    missed = _face_value(face, "tracking_missed_frames")
    if missed:
        label += f" missed={missed}"
    smoothing_weight = _face_value(face, "tracking_smoothing_weight")
    if smoothing_weight is not None:
        label += f" smooth={float(smoothing_weight):.2f}"
    ignored_confidence = _face_value(face, "tracking_ignored_detection_confidence")
    if ignored_confidence is not None:
        label += f" ignored={float(ignored_confidence):.2f}"
    return label


def _face_value(face: Any, attr: str) -> Any:
    if isinstance(face, dict):
        return face.get(attr)
    return getattr(face, attr, None)


def _face_color(index: int) -> tuple[int, int, int]:
    palette = (
        (40, 220, 255),
        (80, 255, 120),
        (255, 190, 80),
        (220, 120, 255),
    )
    return palette[index % len(palette)]
