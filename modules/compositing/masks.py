"""Mask construction helpers for face compositing."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from modules.expression_regions import (
    LEFT_EYE_INDICES,
    LEFT_EYEBROW_INDICES,
    MOUTH_OUTER_INDICES,
    RIGHT_EYE_INDICES,
    RIGHT_EYEBROW_INDICES,
    compute_eye_region_confidences,
    compute_mouth_region_confidence,
    extract_region_points,
)


@dataclass(frozen=True)
class FeatherSettings:
    erode_ratio: float
    blur_ratio: float

    def cache_key(self, size: int) -> tuple[int, float, float]:
        return (int(size), round(self.erode_ratio, 3), round(self.blur_ratio, 3))


def estimate_edge_contrast(bgr_crop: np.ndarray) -> float:
    """Return a normalized edge-energy score for the target crop."""
    if bgr_crop is None or bgr_crop.size == 0:
        return 0.0
    if bgr_crop.ndim == 2:
        gray = bgr_crop
    elif bgr_crop.ndim == 3 and bgr_crop.shape[2] in (3, 4):
        gray = cv2.cvtColor(bgr_crop[:, :, :3], cv2.COLOR_BGR2GRAY)
    else:
        return 0.0

    gray_f32 = gray.astype(np.float32)
    diffs: list[np.ndarray] = []
    if gray_f32.shape[1] > 1:
        diffs.append(np.abs(np.diff(gray_f32, axis=1)))
    if gray_f32.shape[0] > 1:
        diffs.append(np.abs(np.diff(gray_f32, axis=0)))
    if not diffs:
        return 0.0

    edge_energy = float(np.mean([np.percentile(diff, 75) for diff in diffs]))
    return float(np.clip(edge_energy / 128.0, 0.0, 1.0))


def estimate_blur_amount(bgr_crop: np.ndarray) -> float:
    """Return a normalized softness score for locally blurred target crops."""
    gray = _to_gray_u8(bgr_crop)
    if gray is None or min(gray.shape[:2]) < 4:
        return 0.0

    gray_f32 = gray.astype(np.float32)
    try:
        grad_x = cv2.Sobel(gray_f32, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray_f32, cv2.CV_32F, 0, 1, ksize=3)
        gradient = cv2.magnitude(grad_x, grad_y)
        laplacian_variance = float(cv2.Laplacian(gray_f32, cv2.CV_32F).var())
    except cv2.error:
        return 0.0

    gradient_peak = float(np.percentile(gradient, 98))
    if gradient_peak <= 8.0:
        return 0.0

    gradient_spread = float(
        np.clip(
            np.percentile(gradient, 90) / max(gradient_peak, 1e-6),
            0.0,
            1.0,
        )
    )
    edge_confidence = float(np.clip(gradient_peak / 32.0, 0.0, 1.0))
    sharpness = float(np.clip(laplacian_variance / 256.0, 0.0, 1.0))
    return float(np.clip(gradient_spread * edge_confidence * (1.0 - sharpness), 0.0, 1.0))


def get_adaptive_feather_settings(
    *,
    face_size: int,
    crop_shape: tuple[int, int] | tuple[int, int, int],
    frame_shape: tuple[int, int] | tuple[int, int, int],
    edge_contrast: float = 0.0,
    blur_amount: float = 0.0,
    motion_amount: float = 0.0,
    profile_amount: float = 0.0,
    base_erode_ratio: float = 0.10,
    base_blur_ratio: float = 0.05,
    scale_strength: float = 0.35,
    edge_strength: float = 0.35,
    blur_strength: float = 0.0,
    motion_strength: float = 0.25,
    profile_strength: float = 0.0,
) -> FeatherSettings:
    """Choose conservative feather settings from face scale and scene texture."""
    crop_h, crop_w = crop_shape[:2]
    frame_h, frame_w = frame_shape[:2]
    crop_diag = float(np.hypot(max(1, crop_w), max(1, crop_h)))
    frame_diag = float(np.hypot(max(1, frame_w), max(1, frame_h)))
    face_scale = float(np.clip(crop_diag / max(frame_diag, 1.0), 0.0, 1.0))

    # Tiny faces lose detail quickly, while large close-ups expose harder seams.
    scale_factor = 1.0 + (face_scale - 0.18) * float(scale_strength)
    contrast_factor = 1.0 + float(np.clip(edge_contrast, 0.0, 1.0)) * float(edge_strength)
    blur_factor = 1.0 + float(np.clip(blur_amount, 0.0, 1.0)) * float(blur_strength)
    motion_factor = 1.0 + float(np.clip(motion_amount, 0.0, 1.0)) * float(motion_strength)
    profile_factor = 1.0 + float(np.clip(profile_amount, 0.0, 1.0)) * float(profile_strength)

    erode_ratio = np.clip(base_erode_ratio * scale_factor, 0.035, 0.18)
    blur_ratio = np.clip(
        base_blur_ratio
        * scale_factor
        * contrast_factor
        * blur_factor
        * motion_factor
        * profile_factor,
        0.02,
        0.16,
    )

    # Quantize to keep the aligned-mask cache hot during live/video runs.
    return FeatherSettings(
        erode_ratio=round(float(erode_ratio), 3),
        blur_ratio=round(float(blur_ratio), 3),
    )


def create_aligned_face_alpha(size: int, settings: FeatherSettings) -> np.ndarray:
    """Create a square uint8 alpha mask in aligned face space."""
    if size <= 0:
        raise ValueError("size must be greater than zero")

    erode_px = int(round(size * max(0.0, settings.erode_ratio)))
    blur_px = int(round(size * max(0.0, settings.blur_ratio)))
    erode_px = min(max(0, erode_px), max(0, (size - 1) // 2))

    alpha = np.zeros((size, size), dtype=np.uint8)
    cv2.rectangle(
        alpha,
        (erode_px, erode_px),
        (size - erode_px - 1, size - erode_px - 1),
        255,
        -1,
    )
    if blur_px <= 0:
        return alpha

    kernel = _odd_kernel(blur_px * 2 + 1)
    return cv2.GaussianBlur(alpha, (kernel, kernel), 0)


def create_landmark_face_mask(
    face: object,
    frame_shape: tuple[int, int] | tuple[int, int, int],
    *,
    dilation_ratio: float = 0.025,
    feather_ratio: float = 0.018,
    forehead_ratio: float = 0.18,
    profile_amount: float = 0.0,
    profile_taper_ratio: float = 0.0,
    extended_subject: bool = False,
    hairline_ratio: float = 0.32,
    side_ratio: float = 0.24,
    shoulder_ratio: float = 0.48,
    chest_ratio: float = 0.58,
) -> np.ndarray | None:
    """Create a soft full-frame face mask from 106-point landmarks."""
    landmarks = _face_array(face, "landmark_2d_106")
    if landmarks is None or landmarks.shape[0] < 3:
        return None

    frame_h, frame_w = frame_shape[:2]
    if frame_h <= 0 or frame_w <= 0:
        return None

    points = landmarks.reshape(-1, 2).astype(np.float32)
    points = points[np.all(np.isfinite(points), axis=1)]
    if points.shape[0] < 3:
        return None

    bbox = _bbox_from_face_or_points(face, points)
    if bbox is not None and forehead_ratio > 0.0:
        left, top, right, bottom = bbox
        width = max(1.0, right - left)
        height = max(1.0, bottom - top)
        forehead_y = max(0.0, top - height * float(forehead_ratio))
        forehead_points = np.array(
            [
                [left + width * 0.18, forehead_y],
                [left + width * 0.50, forehead_y],
                [left + width * 0.82, forehead_y],
            ],
            dtype=np.float32,
        )
        points = np.vstack([points, forehead_points])

    points[:, 0] = np.clip(points[:, 0], 0, frame_w - 1)
    points[:, 1] = np.clip(points[:, 1], 0, frame_h - 1)
    hull = cv2.convexHull(points.astype(np.int32))
    if hull is None or len(hull) < 3:
        return None

    mask = np.zeros((frame_h, frame_w), dtype=np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)

    if extended_subject:
        mask, points = create_extended_subject_mask(
            points,
            bbox=bbox,
            frame_shape=frame_shape,
            base_mask=mask,
            hairline_ratio=hairline_ratio,
            side_ratio=side_ratio,
            shoulder_ratio=shoulder_ratio,
            chest_ratio=chest_ratio,
        )

    face_span = _face_span(points)
    dilation_px = int(round(face_span * max(0.0, float(dilation_ratio))))
    if dilation_px > 0:
        kernel_size = _odd_kernel(dilation_px * 2 + 1)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (kernel_size, kernel_size),
        )
        mask = cv2.dilate(mask, kernel, iterations=1)

    blur_px = int(round(face_span * max(0.0, float(feather_ratio))))
    if blur_px > 0:
        kernel_size = _odd_kernel(blur_px * 2 + 1)
        mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)
    mask = _apply_profile_taper(
        mask,
        face,
        points,
        profile_amount=profile_amount,
        taper_ratio=profile_taper_ratio,
    )
    return mask


def refine_alpha_with_landmark_mask(
    alpha_crop: np.ndarray,
    face: object | None,
    frame_shape: tuple[int, int] | tuple[int, int, int],
    crop_bounds: tuple[int, int, int, int],
    *,
    strength: float,
    dilation_ratio: float = 0.025,
    feather_ratio: float = 0.018,
    profile_amount: float = 0.0,
    profile_taper_ratio: float = 0.0,
    extended_subject: bool = False,
    hairline_ratio: float = 0.32,
    side_ratio: float = 0.24,
    shoulder_ratio: float = 0.48,
    chest_ratio: float = 0.58,
) -> np.ndarray:
    """Constrain a paste-back alpha crop with a landmark-derived face mask."""
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0 or face is None:
        return alpha_crop

    landmark_mask = create_landmark_face_mask(
        face,
        frame_shape,
        dilation_ratio=dilation_ratio,
        feather_ratio=feather_ratio,
        profile_amount=profile_amount,
        profile_taper_ratio=profile_taper_ratio,
        extended_subject=extended_subject,
        hairline_ratio=hairline_ratio,
        side_ratio=side_ratio,
        shoulder_ratio=shoulder_ratio,
        chest_ratio=chest_ratio,
    )
    if landmark_mask is None:
        return alpha_crop

    x1, y1, x2, y2 = crop_bounds
    mask_crop = landmark_mask[y1:y2, x1:x2]
    if mask_crop.shape[:2] != alpha_crop.shape[:2]:
        return alpha_crop

    mask_crop = mask_crop.astype(np.uint8)
    refined_target = mask_crop if extended_subject else np.minimum(alpha_crop, mask_crop)
    if strength >= 1.0:
        return refined_target
    return cv2.addWeighted(alpha_crop, 1.0 - strength, refined_target, strength, 0)


def extend_subject_mask_points(
    points: np.ndarray,
    *,
    bbox: tuple[float, float, float, float] | None,
    frame_shape: tuple[int, int] | tuple[int, int, int],
    hairline_ratio: float = 0.32,
    side_ratio: float = 0.24,
    shoulder_ratio: float = 0.48,
    chest_ratio: float = 0.58,
) -> np.ndarray:
    """Add conservative upper-subject support points around face landmarks."""
    point_array = np.asarray(points, dtype=np.float32)
    if point_array.ndim != 2 or point_array.shape[1] < 2 or point_array.shape[0] < 3:
        return point_array

    if bbox is None:
        left, top = point_array[:, :2].min(axis=0)
        right, bottom = point_array[:, :2].max(axis=0)
        bbox = (float(left), float(top), float(right), float(bottom))

    frame_h, frame_w = frame_shape[:2]
    if frame_h <= 0 or frame_w <= 0:
        return point_array

    left, top, right, bottom = bbox
    width = max(float(right - left), 1.0)
    height = max(float(bottom - top), 1.0)
    center_x = (float(left) + float(right)) * 0.5

    hair = float(np.clip(hairline_ratio, 0.0, 0.60))
    side = float(np.clip(side_ratio, 0.0, 0.45))
    shoulder = float(np.clip(shoulder_ratio, 0.0, 0.65))
    chest = float(np.clip(chest_ratio, 0.0, 0.75))

    extra = np.array(
        [
            [left - width * side, top + height * 0.20],
            [left + width * 0.12, top - height * hair],
            [center_x, top - height * (hair * 1.12)],
            [right - width * 0.12, top - height * hair],
            [right + width * side, top + height * 0.20],
            [left - width * side, top + height * 0.52],
            [right + width * side, top + height * 0.52],
            [left + width * 0.32, bottom + height * 0.20],
            [right - width * 0.32, bottom + height * 0.20],
            [left - width * shoulder, bottom + height * (chest * 0.55)],
            [right + width * shoulder, bottom + height * (chest * 0.55)],
            [left - width * (shoulder * 0.70), bottom + height * chest],
            [center_x, bottom + height * chest],
            [right + width * (shoulder * 0.70), bottom + height * chest],
        ],
        dtype=np.float32,
    )
    extra[:, 0] = np.clip(extra[:, 0], 0, frame_w - 1)
    extra[:, 1] = np.clip(extra[:, 1], 0, frame_h - 1)
    return np.vstack([point_array[:, :2], extra])


def create_extended_subject_mask(
    points: np.ndarray,
    *,
    bbox: tuple[float, float, float, float] | None,
    frame_shape: tuple[int, int] | tuple[int, int, int],
    base_mask: np.ndarray | None = None,
    hairline_ratio: float = 0.32,
    side_ratio: float = 0.24,
    shoulder_ratio: float = 0.48,
    chest_ratio: float = 0.58,
) -> tuple[np.ndarray, np.ndarray]:
    """Build a layered upper-subject matte with soft support-region falloff."""
    point_array = np.asarray(points, dtype=np.float32)
    frame_h, frame_w = frame_shape[:2]
    if base_mask is None or base_mask.shape[:2] != (frame_h, frame_w):
        base_mask = np.zeros((frame_h, frame_w), dtype=np.uint8)
        if point_array.ndim == 2 and point_array.shape[0] >= 3:
            hull = cv2.convexHull(point_array[:, :2].astype(np.int32))
            if hull is not None and len(hull) >= 3:
                cv2.fillConvexPoly(base_mask, hull, 255)

    extended_points = extend_subject_mask_points(
        point_array,
        bbox=bbox,
        frame_shape=frame_shape,
        hairline_ratio=hairline_ratio,
        side_ratio=side_ratio,
        shoulder_ratio=shoulder_ratio,
        chest_ratio=chest_ratio,
    )
    if bbox is None:
        left, top = point_array[:, :2].min(axis=0)
        right, bottom = point_array[:, :2].max(axis=0)
    else:
        left, top, right, bottom = bbox
    width = max(float(right - left), 1.0)
    height = max(float(bottom - top), 1.0)
    center_x = (float(left) + float(right)) * 0.5

    hair = float(np.clip(hairline_ratio, 0.0, 0.60))
    side = float(np.clip(side_ratio, 0.0, 0.45))
    shoulder = float(np.clip(shoulder_ratio, 0.0, 0.65))
    chest = float(np.clip(chest_ratio, 0.0, 0.75))

    support = np.zeros((frame_h, frame_w), dtype=np.uint8)
    core = np.zeros((frame_h, frame_w), dtype=np.uint8)
    hair_poly = np.array(
        [
            [left - width * (side * 1.25), top + height * 0.26],
            [left + width * 0.04, top - height * hair],
            [center_x, top - height * (hair * 1.18)],
            [right - width * 0.04, top - height * hair],
            [right + width * (side * 1.25), top + height * 0.26],
            [right + width * (side * 0.55), top + height * 0.52],
            [left - width * (side * 0.55), top + height * 0.52],
        ],
        dtype=np.float32,
    )
    neck_shoulders_poly = np.array(
        [
            [left + width * 0.28, bottom - height * 0.06],
            [right - width * 0.28, bottom - height * 0.06],
            [right + width * shoulder, bottom + height * (chest * 0.52)],
            [right + width * (shoulder * 0.64), bottom + height * chest],
            [center_x, bottom + height * (chest * 1.04)],
            [left - width * (shoulder * 0.64), bottom + height * chest],
            [left - width * shoulder, bottom + height * (chest * 0.52)],
        ],
        dtype=np.float32,
    )
    for polygon in (hair_poly, neck_shoulders_poly):
        polygon[:, 0] = np.clip(polygon[:, 0], 0, frame_w - 1)
        polygon[:, 1] = np.clip(polygon[:, 1], 0, frame_h - 1)
        cv2.fillPoly(support, [polygon.astype(np.int32)], 255)

    neck_chest_core = np.array(
        [
            [left + width * 0.34, bottom - height * 0.04],
            [right - width * 0.34, bottom - height * 0.04],
            [right - width * 0.18, bottom + height * (chest * 0.82)],
            [center_x, bottom + height * (chest * 0.96)],
            [left + width * 0.18, bottom + height * (chest * 0.82)],
        ],
        dtype=np.float32,
    )
    neck_chest_core[:, 0] = np.clip(neck_chest_core[:, 0], 0, frame_w - 1)
    neck_chest_core[:, 1] = np.clip(neck_chest_core[:, 1], 0, frame_h - 1)
    cv2.fillPoly(core, [neck_chest_core.astype(np.int32)], 255)

    falloff_px = max(3.0, max(width, height) * 0.16)
    support_alpha = _interior_falloff_mask(support, falloff_px=falloff_px)
    combined = np.maximum(np.maximum(base_mask.astype(np.uint8), support_alpha), core)
    return combined, extended_points


def refine_alpha_with_skin_chroma_mask(
    alpha_crop: np.ndarray,
    target_crop: np.ndarray,
    *,
    strength: float,
    chroma_threshold: float = 1.8,
    max_reduction: float = 0.45,
    blur_ratio: float = 0.015,
    luma_threshold: float = 0.0,
    luma_max_reduction: float = 0.0,
) -> np.ndarray:
    """Reduce alpha on target-crop skin/luma outliers using an adaptive face matte."""
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0 or alpha_crop is None or target_crop is None:
        return alpha_crop
    if alpha_crop.ndim != 2 or alpha_crop.size == 0:
        return alpha_crop
    if target_crop.shape[:2] != alpha_crop.shape[:2]:
        return alpha_crop
    if not np.issubdtype(alpha_crop.dtype, np.number):
        return alpha_crop

    target_u8 = _to_uint8_image(target_crop)
    if target_u8 is None or target_u8.ndim != 3 or target_u8.shape[2] < 3:
        return alpha_crop

    alpha_norm = _alpha_to_unit_float(alpha_crop)
    sample_mask = alpha_norm >= 0.70
    if int(np.count_nonzero(sample_mask)) < max(16, alpha_crop.size // 40):
        sample_mask = alpha_norm >= 0.45
    if int(np.count_nonzero(sample_mask)) < 16:
        return alpha_crop

    try:
        lab = cv2.cvtColor(target_u8[:, :, :3], cv2.COLOR_BGR2LAB).astype(np.float32)
    except cv2.error:
        return alpha_crop

    chroma = lab[:, :, 1:3]
    sample_chroma = chroma[sample_mask]
    if sample_chroma.size == 0:
        return alpha_crop

    median = np.median(sample_chroma, axis=0)
    distances = np.linalg.norm(chroma - median.reshape(1, 1, 2), axis=2)
    sample_distances = np.linalg.norm(sample_chroma - median.reshape(1, 2), axis=1)
    chroma_score = _soft_outlier_score(
        distances,
        sample_distances,
        threshold=chroma_threshold,
        min_soft_threshold=4.0,
    )

    max_reduction = float(np.clip(max_reduction, 0.0, 1.0))
    reduction_score = chroma_score * max_reduction

    luma_max_reduction = float(np.clip(luma_max_reduction, 0.0, 1.0))
    if luma_max_reduction > 0.0 and luma_threshold > 0.0:
        luma = lab[:, :, 0]
        sample_luma = luma[sample_mask]
        if sample_luma.size > 0:
            luma_median = float(np.median(sample_luma))
            luma_distances = np.abs(luma - luma_median)
            sample_luma_distances = np.abs(sample_luma - luma_median)
            luma_score = _soft_outlier_score(
                luma_distances,
                sample_luma_distances,
                threshold=luma_threshold,
                min_soft_threshold=4.0,
            )
            reduction_score = np.maximum(
                reduction_score,
                luma_score * luma_max_reduction,
            )

    if not np.any(reduction_score > 0.0):
        return alpha_crop

    soften_px = int(round(min(alpha_crop.shape[:2]) * max(0.0, float(blur_ratio))))
    if soften_px > 0:
        kernel_size = _odd_kernel(soften_px * 2 + 1)
        reduction_score = cv2.GaussianBlur(reduction_score, (kernel_size, kernel_size), 0)
        reduction_score = np.clip(reduction_score, 0.0, 1.0)

    reduction = strength * reduction_score
    refined = alpha_crop.astype(np.float32) * (1.0 - reduction)
    return _restore_alpha_dtype(refined, alpha_crop)


def refine_alpha_with_boundary_color_mismatch(
    alpha_crop: np.ndarray,
    source_crop: np.ndarray,
    target_crop: np.ndarray,
    *,
    strength: float,
    color_threshold: float = 0.18,
    max_reduction: float = 0.45,
    band_ratio: float = 0.035,
    blur_ratio: float = 0.012,
) -> np.ndarray:
    """Reduce alpha near boundaries where source and target color still diverge."""
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0 or alpha_crop is None:
        return alpha_crop
    if alpha_crop.ndim != 2 or alpha_crop.size == 0:
        return alpha_crop
    if source_crop is None or target_crop is None:
        return alpha_crop
    if source_crop.shape[:2] != alpha_crop.shape[:2]:
        return alpha_crop
    if target_crop.shape[:2] != alpha_crop.shape[:2]:
        return alpha_crop

    source_u8 = _to_uint8_image(source_crop)
    target_u8 = _to_uint8_image(target_crop)
    if source_u8 is None or target_u8 is None:
        return alpha_crop
    if source_u8.ndim != 3 or target_u8.ndim != 3:
        return alpha_crop
    if source_u8.shape[2] < 3 or target_u8.shape[2] < 3:
        return alpha_crop

    boundary_band = _alpha_boundary_band(alpha_crop, band_ratio=band_ratio)
    if boundary_band is None or not np.any(boundary_band > 0.0):
        return alpha_crop

    try:
        source_lab = cv2.cvtColor(source_u8[:, :, :3], cv2.COLOR_BGR2LAB).astype(np.float32)
        target_lab = cv2.cvtColor(target_u8[:, :, :3], cv2.COLOR_BGR2LAB).astype(np.float32)
    except cv2.error:
        return alpha_crop

    delta = np.linalg.norm(source_lab - target_lab, axis=2)
    mismatch = np.clip(delta / 96.0, 0.0, 1.0)
    threshold = float(np.clip(color_threshold, 0.0, 1.0))
    mismatch = np.clip(
        (mismatch - threshold) / max(1.0 - threshold, 1e-6),
        0.0,
        1.0,
    )
    mismatch *= boundary_band
    if not np.any(mismatch > 0.0):
        return alpha_crop

    soften_px = int(round(min(alpha_crop.shape[:2]) * max(0.0, float(blur_ratio))))
    if soften_px > 0:
        kernel_size = _odd_kernel(soften_px * 2 + 1)
        mismatch = cv2.GaussianBlur(mismatch, (kernel_size, kernel_size), 0)
        mismatch = np.clip(mismatch, 0.0, 1.0)

    reduction = strength * float(np.clip(max_reduction, 0.0, 1.0)) * mismatch
    refined = alpha_crop.astype(np.float32) * (1.0 - reduction)
    return _restore_alpha_dtype(refined, alpha_crop)


def create_expression_occlusion_mask(
    face: object | None,
    frame_shape: tuple[int, int] | tuple[int, int, int],
    crop_bounds: tuple[int, int, int, int],
    *,
    mouth_strength: float = 0.0,
    eye_strength: float = 0.0,
    feather_ratio: float = 0.018,
    padding_ratio: float = 0.55,
    mouth_min_confidence: float = 0.0,
    eye_min_confidence: float = 0.0,
) -> np.ndarray | None:
    """Create a crop-local priority mask for expression-region occluder edges."""
    if face is None or len(frame_shape) < 2:
        return None

    mouth_strength = float(np.clip(mouth_strength, 0.0, 1.0))
    eye_strength = float(np.clip(eye_strength, 0.0, 1.0))
    if mouth_strength <= 0.0 and eye_strength <= 0.0:
        return None

    x1, y1, x2, y2 = map(int, crop_bounds)
    frame_h, frame_w = frame_shape[:2]
    x1 = int(np.clip(x1, 0, frame_w))
    x2 = int(np.clip(x2, 0, frame_w))
    y1 = int(np.clip(y1, 0, frame_h))
    y2 = int(np.clip(y2, 0, frame_h))
    if x2 <= x1 or y2 <= y1:
        return None

    mask = np.zeros((y2 - y1, x2 - x1), dtype=np.float32)
    painted = False

    if mouth_strength > 0.0:
        mouth_confidence = compute_mouth_region_confidence(face)
        if mouth_confidence >= max(0.0, float(mouth_min_confidence)):
            painted |= _paint_expression_region(
                mask,
                extract_region_points(face, MOUTH_OUTER_INDICES),
                (x1, y1),
                strength=mouth_strength,
                padding_ratio=padding_ratio,
                min_axis_px=3.0,
            )

    if eye_strength > 0.0:
        left_confidence, right_confidence = compute_eye_region_confidences(face)
        eye_gate = max(0.0, float(eye_min_confidence))
        if left_confidence >= eye_gate:
            painted |= _paint_expression_region(
                mask,
                extract_region_points(face, LEFT_EYE_INDICES + LEFT_EYEBROW_INDICES),
                (x1, y1),
                strength=eye_strength,
                padding_ratio=padding_ratio,
                min_axis_px=2.0,
            )
        if right_confidence >= eye_gate:
            painted |= _paint_expression_region(
                mask,
                extract_region_points(face, RIGHT_EYE_INDICES + RIGHT_EYEBROW_INDICES),
                (x1, y1),
                strength=eye_strength,
                padding_ratio=padding_ratio,
                min_axis_px=2.0,
            )

    if not painted or not np.any(mask > 0.0):
        return None

    soften_px = int(round(min(mask.shape[:2]) * max(0.0, float(feather_ratio))))
    if soften_px > 0:
        kernel_size = _odd_kernel(soften_px * 2 + 1)
        mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)
        mask = np.clip(mask, 0.0, 1.0)

    return np.clip(mask * 255.0, 0, 255).astype(np.uint8)


def preserve_target_edges_in_alpha(
    alpha_crop: np.ndarray,
    target_crop: np.ndarray,
    *,
    strength: float,
    edge_threshold: float = 0.35,
    max_reduction: float = 0.55,
    blur_ratio: float = 0.015,
    min_contrast: float = 24.0,
    priority_mask: np.ndarray | None = None,
    priority_strength: float = 0.0,
    detail_strength: float = 0.0,
    detail_threshold: float = 0.12,
) -> np.ndarray:
    """Lower paste-back alpha on strong target edges that may be occluders."""
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0 or alpha_crop is None or target_crop is None:
        return alpha_crop
    if alpha_crop.ndim != 2 or alpha_crop.size == 0:
        return alpha_crop
    if not np.issubdtype(alpha_crop.dtype, np.number):
        return alpha_crop
    if target_crop.shape[:2] != alpha_crop.shape[:2]:
        return alpha_crop
    if not np.issubdtype(target_crop.dtype, np.number):
        return alpha_crop
    if np.issubdtype(target_crop.dtype, np.floating) and not np.all(
        np.isfinite(target_crop)
    ):
        return alpha_crop

    target_u8 = _to_uint8_image(target_crop)
    if target_u8 is None:
        return alpha_crop

    try:
        if target_u8.ndim == 2:
            gray = target_u8
        elif target_u8.ndim == 3 and target_u8.shape[2] in (3, 4):
            gray = cv2.cvtColor(target_u8[:, :, :3], cv2.COLOR_BGR2GRAY)
        else:
            return alpha_crop
    except cv2.error:
        return alpha_crop
    if min(gray.shape[:2]) < 2:
        return alpha_crop

    try:
        gray_f32 = gray.astype(np.float32)
        grad_x = cv2.Sobel(gray_f32, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray_f32, cv2.CV_32F, 0, 1, ksize=3)
        edge_magnitude = cv2.magnitude(grad_x, grad_y)
    except cv2.error:
        return alpha_crop

    absolute_edge_floor = max(0.0, float(min_contrast))
    edge_scale = float(np.percentile(edge_magnitude, 95))
    if edge_scale <= absolute_edge_floor:
        return alpha_crop

    relative_score = np.clip(edge_magnitude / edge_scale, 0.0, 1.0)
    absolute_score = np.clip(
        (edge_magnitude - absolute_edge_floor)
        / max(edge_scale - absolute_edge_floor, 1e-6),
        0.0,
        1.0,
    )
    edge_score = relative_score * absolute_score
    edge_scale = float(np.percentile(edge_score, 95))
    if edge_scale <= 1e-6:
        return alpha_crop

    edge_score = np.clip(edge_score / edge_scale, 0.0, 1.0)
    priority_score = _priority_mask_to_unit(priority_mask, alpha_crop.shape)
    priority_strength = float(np.clip(priority_strength, 0.0, 1.0))
    if priority_strength <= 0.0:
        priority_score = None
    detail_score = _fine_detail_score(
        gray,
        threshold=detail_threshold,
        radius_ratio=max(float(blur_ratio) * 2.0, 0.06),
    )
    detail_strength = float(np.clip(detail_strength, 0.0, 1.0))

    threshold = float(np.clip(edge_threshold, 0.0, 1.0))
    if threshold > 0.0:
        if priority_score is None:
            edge_score = np.clip(
                (edge_score - threshold) / max(1.0 - threshold, 1e-6),
                0.0,
                1.0,
            )
        else:
            threshold_map = threshold * (1.0 - 0.65 * priority_strength * priority_score)
            edge_score = np.clip(
                (edge_score - threshold_map) / np.maximum(1.0 - threshold_map, 1e-6),
                0.0,
                1.0,
            )
    if not np.any(edge_score > 0.0):
        edge_score = np.zeros_like(edge_score, dtype=np.float32)

    if priority_score is not None:
        edge_score = np.clip(
            edge_score * (1.0 + priority_strength * priority_score),
            0.0,
            1.0,
        )
        if detail_score is not None:
            detail_score = np.clip(
                detail_score * (1.0 + 0.5 * priority_strength * priority_score),
                0.0,
                1.0,
            )

    if detail_strength > 0.0 and detail_score is not None:
        edge_score = np.maximum(edge_score, detail_score * detail_strength)

    if not np.any(edge_score > 0.0):
        return alpha_crop

    soften_px = int(round(min(alpha_crop.shape[:2]) * max(0.0, float(blur_ratio))))
    if soften_px > 0:
        kernel_size = _odd_kernel(soften_px * 2 + 1)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (kernel_size, kernel_size),
        )
        edge_score = cv2.dilate(edge_score, kernel, iterations=1)
        edge_score = cv2.GaussianBlur(edge_score, (kernel_size, kernel_size), 0)
        edge_score = np.clip(edge_score, 0.0, 1.0)

    reduction = strength * float(np.clip(max_reduction, 0.0, 1.0)) * edge_score
    refined = alpha_crop.astype(np.float32) * (1.0 - reduction)
    return _restore_alpha_dtype(refined, alpha_crop)


def _paint_expression_region(
    mask: np.ndarray,
    points: np.ndarray,
    crop_origin: tuple[int, int],
    *,
    strength: float,
    padding_ratio: float,
    min_axis_px: float,
) -> bool:
    try:
        point_array = np.asarray(points, dtype=np.float32)
    except (TypeError, ValueError):
        return False
    if point_array.ndim != 2 or point_array.shape[1] < 2 or point_array.shape[0] == 0:
        return False

    point_array = point_array[:, :2]
    finite_points = point_array[np.all(np.isfinite(point_array), axis=1)]
    if finite_points.shape[0] < 3:
        return False

    min_xy = finite_points.min(axis=0)
    max_xy = finite_points.max(axis=0)
    spread = np.maximum(max_xy - min_xy, 1.0)
    padding = np.maximum(spread * max(0.0, float(padding_ratio)), min_axis_px)
    min_xy -= padding
    max_xy += padding

    origin = np.asarray(crop_origin, dtype=np.float32)
    min_xy -= origin
    max_xy -= origin
    min_xy[0] = np.clip(min_xy[0], 0, mask.shape[1] - 1)
    max_xy[0] = np.clip(max_xy[0], 0, mask.shape[1] - 1)
    min_xy[1] = np.clip(min_xy[1], 0, mask.shape[0] - 1)
    max_xy[1] = np.clip(max_xy[1], 0, mask.shape[0] - 1)
    if max_xy[0] <= min_xy[0] or max_xy[1] <= min_xy[1]:
        return False

    center = ((min_xy + max_xy) * 0.5).round().astype(np.int32)
    axes = np.maximum(((max_xy - min_xy) * 0.5).round().astype(np.int32), 1)
    cv2.ellipse(
        mask,
        (int(center[0]), int(center[1])),
        (int(axes[0]), int(axes[1])),
        0.0,
        0.0,
        360.0,
        float(np.clip(strength, 0.0, 1.0)),
        -1,
    )
    return True


def _priority_mask_to_unit(
    priority_mask: np.ndarray | None,
    expected_shape: tuple[int, int],
) -> np.ndarray | None:
    if priority_mask is None:
        return None
    try:
        priority = np.asarray(priority_mask)
    except (TypeError, ValueError):
        return None
    if priority.ndim == 3:
        priority = priority[:, :, 0]
    if priority.shape[:2] != expected_shape:
        return None
    if not np.issubdtype(priority.dtype, np.number):
        return None
    if np.issubdtype(priority.dtype, np.floating) and not np.all(np.isfinite(priority)):
        return None
    return _alpha_to_unit_float(priority)


def _interior_falloff_mask(mask: np.ndarray, *, falloff_px: float) -> np.ndarray:
    if mask is None or mask.ndim != 2 or mask.size == 0:
        return np.zeros((0, 0), dtype=np.uint8)
    binary = (mask > 0).astype(np.uint8)
    if not np.any(binary):
        return np.zeros_like(mask, dtype=np.uint8)
    try:
        distance = cv2.distanceTransform(binary, cv2.DIST_L2, 3)
    except cv2.error:
        return mask.astype(np.uint8, copy=False)
    alpha = np.clip(distance / max(float(falloff_px), 1.0), 0.0, 1.0) * 255.0
    return alpha.astype(np.uint8)


def _alpha_boundary_band(
    alpha: np.ndarray,
    *,
    band_ratio: float,
) -> np.ndarray | None:
    if alpha.ndim != 2 or alpha.size == 0:
        return None
    alpha_unit = _alpha_to_unit_float(alpha).astype(np.float32)
    if not np.any(alpha_unit > 0.0):
        return None

    soft_band = np.clip(alpha_unit * (1.0 - alpha_unit) * 4.0, 0.0, 1.0)
    radius_px = int(round(min(alpha_unit.shape[:2]) * max(0.0, float(band_ratio))))
    if radius_px <= 0:
        return soft_band

    kernel_size = _odd_kernel(radius_px * 2 + 1)
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )
    try:
        dilated = cv2.dilate(alpha_unit, kernel, iterations=1)
        eroded = cv2.erode(alpha_unit, kernel, iterations=1)
    except cv2.error:
        return soft_band
    gradient_band = np.clip(dilated - eroded, 0.0, 1.0)
    return gradient_band


def _fine_detail_score(
    gray: np.ndarray,
    *,
    threshold: float,
    radius_ratio: float,
) -> np.ndarray | None:
    if gray is None or gray.ndim != 2 or min(gray.shape[:2]) < 3:
        return None
    gray_f32 = gray.astype(np.float32)
    radius_px = int(round(min(gray.shape[:2]) * max(0.0, float(radius_ratio))))
    kernel_size = _odd_kernel(radius_px * 2 + 1)
    try:
        local_mean = cv2.GaussianBlur(gray_f32, (kernel_size, kernel_size), 0)
    except cv2.error:
        return None

    deviation = np.abs(gray_f32 - local_mean) / 255.0
    scale = float(np.percentile(deviation, 95))
    threshold = float(np.clip(threshold, 0.0, 1.0))
    if scale <= max(threshold, 1e-6):
        return None
    detail_score = np.clip(
        (deviation - threshold) / max(scale - threshold, 1e-6),
        0.0,
        1.0,
    )
    return detail_score.astype(np.float32, copy=False)


def _soft_outlier_score(
    distances: np.ndarray,
    sample_distances: np.ndarray,
    *,
    threshold: float,
    min_soft_threshold: float,
) -> np.ndarray:
    sample_scale = float(np.percentile(sample_distances, 65))
    soft_threshold = max(
        float(min_soft_threshold),
        sample_scale * max(0.1, float(threshold)),
    )
    hard_threshold = max(soft_threshold + float(min_soft_threshold), soft_threshold * 1.9)
    return np.clip(
        (distances - soft_threshold) / max(hard_threshold - soft_threshold, 1e-6),
        0.0,
        1.0,
    )


def _to_uint8_image(image: np.ndarray) -> np.ndarray | None:
    if image.size == 0 or not np.issubdtype(image.dtype, np.number):
        return None
    if image.dtype == np.uint8:
        return image
    if np.issubdtype(image.dtype, np.floating):
        if not np.all(np.isfinite(image)):
            return None
        max_value = float(np.max(image))
        min_value = float(np.min(image))
        scale = 255.0 if 0.0 <= min_value and max_value <= 1.5 else 1.0
        return np.clip(image * scale, 0, 255).astype(np.uint8)
    return np.clip(image, 0, 255).astype(np.uint8)


def _to_gray_u8(image: np.ndarray) -> np.ndarray | None:
    target_u8 = _to_uint8_image(image)
    if target_u8 is None:
        return None
    try:
        if target_u8.ndim == 2:
            return target_u8
        if target_u8.ndim == 3 and target_u8.shape[2] in (3, 4):
            return cv2.cvtColor(target_u8[:, :, :3], cv2.COLOR_BGR2GRAY)
    except cv2.error:
        return None
    return None


def _alpha_to_unit_float(alpha: np.ndarray) -> np.ndarray:
    alpha_f32 = alpha.astype(np.float32)
    if np.issubdtype(alpha.dtype, np.floating):
        max_value = float(np.max(alpha_f32))
        if max_value <= 1.5:
            return np.clip(alpha_f32, 0.0, 1.0)
    return np.clip(alpha_f32 / 255.0, 0.0, 1.0)


def _restore_alpha_dtype(refined: np.ndarray, original_alpha: np.ndarray) -> np.ndarray:
    if np.issubdtype(original_alpha.dtype, np.integer):
        info = np.iinfo(original_alpha.dtype)
        return np.clip(refined, info.min, info.max).astype(original_alpha.dtype)
    if np.issubdtype(original_alpha.dtype, np.floating):
        return refined.astype(original_alpha.dtype)
    return refined.astype(np.uint8)


def _apply_profile_taper(
    mask: np.ndarray,
    face: object,
    points: np.ndarray,
    *,
    profile_amount: float,
    taper_ratio: float,
) -> np.ndarray:
    amount = float(np.clip(profile_amount, 0.0, 1.0))
    taper = float(np.clip(taper_ratio, 0.0, 1.0))
    if amount <= 0.0 or taper <= 0.0:
        return mask

    signed_offset = _profile_signed_offset(face)
    if abs(signed_offset) <= 1e-6:
        return mask

    left, _top = points.min(axis=0)
    right, _bottom = points.max(axis=0)
    width = max(float(right - left), 1.0)
    taper_width = max(width * taper, 1.0)
    x_coords = np.arange(mask.shape[1], dtype=np.float32)
    if signed_offset > 0.0:
        distance = np.clip((x_coords - float(left)) / taper_width, 0.0, 1.0)
    else:
        distance = np.clip((float(right) - x_coords) / taper_width, 0.0, 1.0)

    far_side_reduction = amount * min(abs(signed_offset), 1.0)
    multiplier = 1.0 - far_side_reduction * (1.0 - distance)
    tapered = mask.astype(np.float32) * multiplier.reshape(1, -1)
    return np.clip(tapered, 0, 255).astype(np.uint8)


def _face_array(face: object, attr: str) -> np.ndarray | None:
    value = getattr(face, attr, None)
    if value is None and isinstance(face, dict):
        value = face.get(attr)
    if value is None:
        return None
    array = np.asarray(value, dtype=np.float32)
    if array.size == 0 or not np.all(np.isfinite(array)):
        return None
    return array


def _profile_signed_offset(face: object) -> float:
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
    return float(np.clip((float(nose[0]) - center_x) / (reference_width * 0.5), -1.0, 1.0))


def _bbox_from_face_or_points(
    face: object,
    points: np.ndarray,
) -> tuple[float, float, float, float] | None:
    bbox = _face_array(face, "bbox")
    if bbox is not None and bbox.reshape(-1).size == 4:
        x1, y1, x2, y2 = bbox.reshape(-1).tolist()
        left, right = sorted((float(x1), float(x2)))
        top, bottom = sorted((float(y1), float(y2)))
        if right > left and bottom > top:
            return left, top, right, bottom
    if points.shape[0] < 3:
        return None
    left, top = points.min(axis=0)
    right, bottom = points.max(axis=0)
    if right <= left or bottom <= top:
        return None
    return float(left), float(top), float(right), float(bottom)


def _face_span(points: np.ndarray) -> float:
    left, top = points.min(axis=0)
    right, bottom = points.max(axis=0)
    return float(max(1.0, right - left, bottom - top))


def _odd_kernel(value: int) -> int:
    kernel = max(3, int(value))
    if kernel % 2 == 0:
        kernel += 1
    return kernel
