"""Local color and lighting matching for face compositing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ColorMatchStatistics:
    """LAB statistics used to color-match a generated face crop."""

    source_mean: np.ndarray
    source_std: np.ndarray
    target_mean: np.ndarray
    target_std: np.ndarray


@dataclass(frozen=True)
class LuminanceMatchStatistics:
    """L-channel statistics used to match low-frequency lighting."""

    source_mean: float
    source_std: float
    target_mean: float
    target_std: float


def match_color_statistics(
    source_bgr: np.ndarray,
    target_bgr: np.ndarray,
    mask: np.ndarray | None = None,
    *,
    strength: float = 1.0,
    trim_percentile: float = 0.0,
    chroma_trim_percentile: float = 0.0,
    statistics_transform: Callable[[ColorMatchStatistics], ColorMatchStatistics]
    | None = None,
) -> np.ndarray:
    """Match source crop LAB statistics toward the target crop.

    The operation is intended for already-warped face crops before alpha
    blending. ``mask`` should identify the pixels that will be composited, so
    black replicated border pixels do not skew the statistics.
    """
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0:
        return source_bgr.copy()
    if source_bgr.shape != target_bgr.shape or source_bgr.size == 0:
        return source_bgr.copy()

    weights = _normalised_weights(mask, source_bgr.shape[:2])
    if weights is None:
        return source_bgr.copy()

    source_lab = _bgr_to_lab(source_bgr)
    target_lab = _bgr_to_lab(target_bgr)
    weights = _trim_luminance_outliers(
        source_lab[:, :, 0],
        target_lab[:, :, 0],
        weights,
        trim_percentile=trim_percentile,
    )
    weights = _trim_chroma_outliers(
        source_lab,
        target_lab,
        weights,
        trim_percentile=chroma_trim_percentile,
    )

    source_mean, source_std = _weighted_mean_std(source_lab, weights)
    target_mean, target_std = _weighted_mean_std(target_lab, weights)
    stats = ColorMatchStatistics(
        source_mean=source_mean,
        source_std=source_std,
        target_mean=target_mean,
        target_std=target_std,
    )
    if statistics_transform is not None:
        stats = statistics_transform(stats)

    adjusted_lab = (
        (source_lab - stats.source_mean.reshape(1, 1, 3))
        * (stats.target_std / np.maximum(stats.source_std, 1e-6)).reshape(1, 1, 3)
        + stats.target_mean.reshape(1, 1, 3)
    )
    adjusted_bgr = _lab_to_bgr(adjusted_lab)
    if strength < 1.0:
        adjusted_bgr = cv2.addWeighted(
            source_bgr,
            1.0 - strength,
            adjusted_bgr,
            strength,
            0,
        )
    return adjusted_bgr


def match_luminance_statistics(
    source_bgr: np.ndarray,
    target_bgr: np.ndarray,
    mask: np.ndarray | None = None,
    *,
    strength: float = 1.0,
    contrast_strength: float = 0.35,
    max_mean_shift: float = 12.0,
    trim_percentile: float = 0.0,
    statistics_transform: Callable[[LuminanceMatchStatistics], LuminanceMatchStatistics]
    | None = None,
) -> np.ndarray:
    """Match only low-frequency LAB luminance toward the target crop.

    This is intentionally narrower than full color statistics matching: it
    adjusts the L channel while preserving the generated crop's chroma.
    """
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0:
        return source_bgr.copy()
    if source_bgr.shape != target_bgr.shape or source_bgr.size == 0:
        return source_bgr.copy()

    weights = _normalised_weights(mask, source_bgr.shape[:2])
    if weights is None:
        return source_bgr.copy()

    source_lab = _bgr_to_lab(source_bgr)
    target_lab = _bgr_to_lab(target_bgr)
    source_l = source_lab[:, :, 0]
    target_l = target_lab[:, :, 0]
    weights = _trim_luminance_outliers(
        source_l,
        target_l,
        weights,
        trim_percentile=trim_percentile,
    )

    source_mean, source_std = _weighted_channel_mean_std(source_l, weights)
    target_mean, target_std = _weighted_channel_mean_std(target_l, weights)
    stats = LuminanceMatchStatistics(
        source_mean=source_mean,
        source_std=source_std,
        target_mean=target_mean,
        target_std=target_std,
    )
    if statistics_transform is not None:
        stats = statistics_transform(stats)
    mean_shift = float(
        np.clip(stats.target_mean - stats.source_mean, -max_mean_shift, max_mean_shift)
    )

    contrast_strength = float(np.clip(contrast_strength, 0.0, 1.0))
    contrast_ratio = stats.target_std / max(stats.source_std, 1e-6)
    contrast_ratio = float(np.clip(contrast_ratio, 0.70, 1.35))
    contrast_ratio = 1.0 + (contrast_ratio - 1.0) * contrast_strength

    adjusted_lab = source_lab.copy()
    adjusted_l = (
        (source_l - stats.source_mean) * contrast_ratio
        + stats.source_mean
        + mean_shift
    )
    adjusted_lab[:, :, 0] = source_l * (1.0 - strength) + adjusted_l * strength
    return _lab_to_bgr(adjusted_lab)


def blend_color_match_statistics(
    previous: ColorMatchStatistics | None,
    current: ColorMatchStatistics,
    history_weight: float,
) -> ColorMatchStatistics:
    """Blend current LAB statistics with prior per-track statistics."""
    weight = float(np.clip(history_weight, 0.0, 1.0))
    if previous is None or weight <= 0.0:
        return current
    if not _color_statistics_compatible(previous, current):
        return current

    return ColorMatchStatistics(
        source_mean=_blend_array(previous.source_mean, current.source_mean, weight),
        source_std=np.maximum(
            _blend_array(previous.source_std, current.source_std, weight),
            1e-6,
        ),
        target_mean=_blend_array(previous.target_mean, current.target_mean, weight),
        target_std=np.maximum(
            _blend_array(previous.target_std, current.target_std, weight),
            1e-6,
        ),
    )


def blend_luminance_match_statistics(
    previous: LuminanceMatchStatistics | None,
    current: LuminanceMatchStatistics,
    history_weight: float,
) -> LuminanceMatchStatistics:
    """Blend current luminance statistics with prior per-track statistics."""
    weight = float(np.clip(history_weight, 0.0, 1.0))
    if previous is None or weight <= 0.0:
        return current

    return LuminanceMatchStatistics(
        source_mean=_blend_scalar(previous.source_mean, current.source_mean, weight),
        source_std=max(
            _blend_scalar(previous.source_std, current.source_std, weight),
            1e-6,
        ),
        target_mean=_blend_scalar(previous.target_mean, current.target_mean, weight),
        target_std=max(
            _blend_scalar(previous.target_std, current.target_std, weight),
            1e-6,
        ),
    )


def _normalised_weights(
    mask: np.ndarray | None,
    shape: tuple[int, int],
) -> np.ndarray | None:
    if mask is None:
        weights = np.ones(shape, dtype=np.float32)
    else:
        if mask.shape[:2] != shape:
            return None
        weights = mask.astype(np.float32)
        if weights.ndim == 3:
            weights = weights.mean(axis=2)
        weights *= 1.0 / 255.0

    # Ignore near-transparent pixels; they are usually warp borders.
    weights = np.where(weights >= 0.05, weights, 0.0).astype(np.float32)
    total = float(weights.sum())
    if total <= 1e-6:
        return None
    return weights / total


def _trim_luminance_outliers(
    source_l: np.ndarray,
    target_l: np.ndarray,
    weights: np.ndarray,
    *,
    trim_percentile: float,
) -> np.ndarray:
    trim = float(np.clip(trim_percentile, 0.0, 45.0))
    if trim <= 0.0:
        return weights

    active = weights > 0.0
    if np.count_nonzero(active) < 8:
        return weights

    source_values = source_l[active]
    target_values = target_l[active]
    source_low, source_high = np.percentile(source_values, [trim, 100.0 - trim])
    target_low, target_high = np.percentile(target_values, [trim, 100.0 - trim])
    keep = (
        active
        & (source_l >= source_low)
        & (source_l <= source_high)
        & (target_l >= target_low)
        & (target_l <= target_high)
    )
    trimmed = np.where(keep, weights, 0.0).astype(np.float32)
    total = float(trimmed.sum())
    if total <= 1e-6:
        return weights
    return trimmed / total


def _trim_chroma_outliers(
    source_lab: np.ndarray,
    target_lab: np.ndarray,
    weights: np.ndarray,
    *,
    trim_percentile: float,
) -> np.ndarray:
    trim = float(np.clip(trim_percentile, 0.0, 45.0))
    if trim <= 0.0:
        return weights

    active = weights > 0.0
    if np.count_nonzero(active) < 8:
        return weights

    source_distance = _chroma_distance_from_median(source_lab[:, :, 1:3], active)
    target_distance = _chroma_distance_from_median(target_lab[:, :, 1:3], active)
    source_high = np.percentile(source_distance[active], 100.0 - trim)
    target_high = np.percentile(target_distance[active], 100.0 - trim)
    keep = (
        active
        & (source_distance <= source_high)
        & (target_distance <= target_high)
    )
    trimmed = np.where(keep, weights, 0.0).astype(np.float32)
    total = float(trimmed.sum())
    if total <= 1e-6:
        return weights
    return trimmed / total


def _weighted_mean_std(
    lab_image: np.ndarray,
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    weights_3c = weights[:, :, None]
    mean = np.sum(lab_image * weights_3c, axis=(0, 1))
    variance = np.sum(((lab_image - mean.reshape(1, 1, 3)) ** 2) * weights_3c, axis=(0, 1))
    return mean.astype(np.float32), np.sqrt(np.maximum(variance, 1e-6)).astype(np.float32)


def _weighted_channel_mean_std(
    channel: np.ndarray,
    weights: np.ndarray,
) -> tuple[float, float]:
    mean = float(np.sum(channel * weights))
    variance = float(np.sum(((channel - mean) ** 2) * weights))
    return mean, float(np.sqrt(max(variance, 1e-6)))


def _chroma_distance_from_median(
    ab_channels: np.ndarray,
    active_mask: np.ndarray,
) -> np.ndarray:
    active_values = ab_channels[active_mask]
    center = np.median(active_values, axis=0)
    distance = np.linalg.norm(ab_channels - center.reshape(1, 1, 2), axis=2)
    return distance.astype(np.float32)


def _color_statistics_compatible(
    previous: ColorMatchStatistics,
    current: ColorMatchStatistics,
) -> bool:
    return (
        previous.source_mean.shape == current.source_mean.shape
        and previous.source_std.shape == current.source_std.shape
        and previous.target_mean.shape == current.target_mean.shape
        and previous.target_std.shape == current.target_std.shape
    )


def _blend_array(
    previous: np.ndarray,
    current: np.ndarray,
    history_weight: float,
) -> np.ndarray:
    return (
        previous.astype(np.float32) * history_weight
        + current.astype(np.float32) * (1.0 - history_weight)
    ).astype(np.float32)


def _blend_scalar(previous: float, current: float, history_weight: float) -> float:
    return float(previous * history_weight + current * (1.0 - history_weight))


def _bgr_to_lab(image: np.ndarray) -> np.ndarray:
    image_f32 = image.astype(np.float32) * (1.0 / 255.0)
    return cv2.cvtColor(image_f32, cv2.COLOR_BGR2LAB)


def _lab_to_bgr(image: np.ndarray) -> np.ndarray:
    bgr = cv2.cvtColor(image.astype(np.float32), cv2.COLOR_LAB2BGR)
    return np.clip(bgr * 255.0, 0, 255).astype(np.uint8)
