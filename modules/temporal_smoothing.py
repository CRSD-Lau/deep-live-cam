"""Region-limited temporal smoothing helpers."""

from __future__ import annotations

from typing import Iterable, Sequence

import cv2
import numpy as np


def blend_frame_regions(
    previous_frame: np.ndarray | None,
    current_frame: np.ndarray,
    bboxes: Iterable[np.ndarray | list[float] | tuple[float, ...]],
    *,
    current_weight: float,
    expansion_ratio: float = 0.18,
    feather_ratio: float = 0.18,
    masks: Iterable[np.ndarray | None] | None = None,
    mask_strength: float = 0.0,
    local_current_weight_masks: Iterable[np.ndarray | None] | None = None,
    local_current_weight_boost: float = 0.0,
    min_feather: int = 3,
    max_feather: int = 41,
) -> np.ndarray:
    """Blend frame history only inside expanded, feathered bbox regions.

    ``current_weight`` matches ``cv2.addWeighted`` semantics: lower values hold
    more of the previous render, higher values follow the current render faster.
    Pixels outside the selected regions remain exactly ``current_frame``.
    """
    if previous_frame is None:
        return current_frame
    if previous_frame.shape != current_frame.shape:
        return current_frame
    if previous_frame.dtype != current_frame.dtype:
        return current_frame
    if not 0.0 < current_weight < 1.0:
        return current_frame

    regions = [
        region
        for bbox in bboxes
        if (region := _expanded_bbox(bbox, current_frame.shape, expansion_ratio))
        is not None
    ]
    if not regions:
        return current_frame

    output = current_frame.copy()
    previous_weight = 1.0 - current_weight
    mask_list = list(masks) if masks is not None else []
    local_mask_list = (
        list(local_current_weight_masks)
        if local_current_weight_masks is not None
        else []
    )
    local_boost = max(0.0, float(local_current_weight_boost or 0.0))
    for index, (x1, y1, x2, y2) in enumerate(regions):
        current_crop = current_frame[y1:y2, x1:x2]
        previous_crop = previous_frame[y1:y2, x1:x2]
        if current_crop.size == 0 or previous_crop.size == 0:
            continue

        blended_crop = cv2.addWeighted(
            previous_crop,
            previous_weight,
            current_crop,
            current_weight,
            0,
        )
        local_mask = local_mask_list[index] if index < len(local_mask_list) else None
        blended_crop = _apply_local_current_weight_boost(
            previous_crop,
            current_crop,
            blended_crop,
            local_mask,
            (x1, y1, x2, y2),
            base_current_weight=current_weight,
            boost=local_boost,
            dtype=current_frame.dtype,
        )
        mask = _feathered_crop_mask(
            current_crop.shape[:2],
            feather_ratio=feather_ratio,
            min_feather=min_feather,
            max_feather=max_feather,
        )
        face_mask = mask_list[index] if index < len(mask_list) else None
        mask = _combine_temporal_masks(
            mask,
            face_mask,
            (x1, y1, x2, y2),
            mask_strength=mask_strength,
        )
        if mask.max() == 255 and mask.min() == 255:
            output[y1:y2, x1:x2] = blended_crop
            continue

        alpha = (mask.astype(np.float32) / 255.0)[:, :, np.newaxis]
        mixed = (
            blended_crop.astype(np.float32) * alpha
            + current_crop.astype(np.float32) * (1.0 - alpha)
        )
        output[y1:y2, x1:x2] = np.clip(mixed, 0, 255).astype(current_frame.dtype)
    return output


def _apply_local_current_weight_boost(
    previous_crop: np.ndarray,
    current_crop: np.ndarray,
    blended_crop: np.ndarray,
    local_mask: np.ndarray | None,
    region: Sequence[int],
    *,
    base_current_weight: float,
    boost: float,
    dtype: np.dtype,
) -> np.ndarray:
    if boost <= 0.0 or local_mask is None:
        return blended_crop

    local_weight = float(np.clip(base_current_weight + boost, 0.0, 1.0))
    if local_weight <= base_current_weight:
        return blended_crop

    mask_crop = _crop_full_frame_mask(local_mask, region, blended_crop.shape[:2])
    if mask_crop is None or not np.any(mask_crop > 0.0):
        return blended_crop

    responsive_crop = cv2.addWeighted(
        previous_crop,
        1.0 - local_weight,
        current_crop,
        local_weight,
        0,
    )
    alpha = mask_crop[:, :, np.newaxis]
    mixed = (
        responsive_crop.astype(np.float32) * alpha
        + blended_crop.astype(np.float32) * (1.0 - alpha)
    )
    return np.clip(mixed, 0, 255).astype(dtype)


def _crop_full_frame_mask(
    mask: np.ndarray,
    region: Sequence[int],
    expected_shape: tuple[int, int],
) -> np.ndarray | None:
    try:
        mask_arr = np.asarray(mask)
    except (TypeError, ValueError):
        return None
    if mask_arr.ndim == 3:
        mask_arr = mask_arr.mean(axis=2)
    if mask_arr.ndim != 2:
        return None
    if not np.issubdtype(mask_arr.dtype, np.number):
        return None

    x1, y1, x2, y2 = region
    if y2 > mask_arr.shape[0] or x2 > mask_arr.shape[1] or x1 < 0 or y1 < 0:
        return None
    mask_crop = mask_arr[y1:y2, x1:x2]
    if mask_crop.shape != expected_shape or mask_crop.size == 0:
        return None
    if not np.all(np.isfinite(mask_crop)):
        return None
    return np.clip(mask_crop.astype(np.float32) / 255.0, 0.0, 1.0)


def _combine_temporal_masks(
    region_mask: np.ndarray,
    face_mask: np.ndarray | None,
    region: Sequence[int],
    *,
    mask_strength: float,
) -> np.ndarray:
    strength = float(np.clip(mask_strength, 0.0, 1.0))
    if strength <= 0.0 or face_mask is None:
        return region_mask

    try:
        mask_arr = np.asarray(face_mask)
    except (TypeError, ValueError):
        return region_mask
    if mask_arr.ndim == 3:
        mask_arr = mask_arr.mean(axis=2)
    if mask_arr.ndim != 2:
        return region_mask

    x1, y1, x2, y2 = region
    if y2 > mask_arr.shape[0] or x2 > mask_arr.shape[1] or x1 < 0 or y1 < 0:
        return region_mask

    mask_crop = mask_arr[y1:y2, x1:x2]
    if mask_crop.shape != region_mask.shape or mask_crop.size == 0:
        return region_mask
    if not np.all(np.isfinite(mask_crop)):
        return region_mask

    region_alpha = region_mask.astype(np.float32) / 255.0
    face_alpha = np.clip(mask_crop.astype(np.float32) / 255.0, 0.0, 1.0)
    constrained = region_alpha * ((1.0 - strength) + strength * face_alpha)
    return np.clip(np.rint(constrained * 255.0), 0, 255).astype(np.uint8)


def _expanded_bbox(
    bbox: np.ndarray | list[float] | tuple[float, ...],
    frame_shape: tuple[int, ...],
    expansion_ratio: float,
) -> tuple[int, int, int, int] | None:
    values = np.asarray(bbox, dtype=np.float32).reshape(-1)
    if values.size != 4 or not np.all(np.isfinite(values)):
        return None

    x1, y1, x2, y2 = values.tolist()
    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    width = right - left
    height = bottom - top
    if width <= 1 or height <= 1:
        return None

    expansion = max(0.0, float(expansion_ratio))
    pad_x = width * expansion
    pad_y = height * expansion
    frame_h, frame_w = frame_shape[:2]
    left_i = max(0, int(np.floor(left - pad_x)))
    top_i = max(0, int(np.floor(top - pad_y)))
    right_i = min(frame_w, int(np.ceil(right + pad_x)))
    bottom_i = min(frame_h, int(np.ceil(bottom + pad_y)))
    if right_i <= left_i or bottom_i <= top_i:
        return None
    return left_i, top_i, right_i, bottom_i


def _feathered_crop_mask(
    shape: tuple[int, int],
    *,
    feather_ratio: float,
    min_feather: int,
    max_feather: int,
) -> np.ndarray:
    height, width = shape
    if height <= 0 or width <= 0:
        return np.zeros((max(0, height), max(0, width)), dtype=np.uint8)

    feather = int(round(min(height, width) * max(0.0, feather_ratio)))
    feather = max(int(min_feather), min(int(max_feather), feather))
    if feather <= 0 or min(height, width) <= 2:
        return np.full((height, width), 255, dtype=np.uint8)

    inset = min(feather, max(0, (width - 1) // 2), max(0, (height - 1) // 2))
    if inset <= 0:
        return np.full((height, width), 255, dtype=np.uint8)

    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.rectangle(
        mask,
        (inset, inset),
        (max(inset, width - inset - 1), max(inset, height - inset - 1)),
        255,
        -1,
    )
    kernel = _odd_kernel(min(max_feather, max(3, inset * 2 + 1)))
    return cv2.GaussianBlur(mask, (kernel, kernel), 0)


def _odd_kernel(value: int) -> int:
    kernel = max(3, int(value))
    if kernel % 2 == 0:
        kernel += 1
    return kernel
