import cv2
import numpy as np

from modules.compositing.color import (
    ColorMatchStatistics,
    LuminanceMatchStatistics,
    blend_color_match_statistics,
    blend_luminance_match_statistics,
    match_color_statistics,
    match_luminance_statistics,
)


def test_color_match_strength_zero_returns_source_pixels():
    source = np.full((4, 4, 3), [20, 60, 100], dtype=np.uint8)
    target = np.full((4, 4, 3), [200, 210, 220], dtype=np.uint8)
    mask = np.full((4, 4), 255, dtype=np.uint8)

    result = match_color_statistics(source, target, mask, strength=0.0)

    np.testing.assert_array_equal(result, source)


def test_color_match_moves_source_toward_target_statistics():
    source = np.full((8, 8, 3), [30, 50, 70], dtype=np.uint8)
    target = np.full((8, 8, 3), [120, 150, 180], dtype=np.uint8)
    mask = np.full((8, 8), 255, dtype=np.uint8)

    result = match_color_statistics(source, target, mask, strength=1.0)

    assert result.dtype == np.uint8
    assert result.shape == source.shape
    assert np.mean(np.abs(result.astype(np.int16) - target.astype(np.int16))) < np.mean(
        np.abs(source.astype(np.int16) - target.astype(np.int16))
    )


def test_color_match_respects_empty_mask():
    source = np.full((4, 4, 3), [20, 60, 100], dtype=np.uint8)
    target = np.full((4, 4, 3), [200, 210, 220], dtype=np.uint8)
    mask = np.zeros((4, 4), dtype=np.uint8)

    result = match_color_statistics(source, target, mask, strength=1.0)

    np.testing.assert_array_equal(result, source)


def test_color_match_limits_adjustment_with_partial_strength():
    source = np.full((8, 8, 3), [30, 50, 70], dtype=np.uint8)
    target = np.full((8, 8, 3), [120, 150, 180], dtype=np.uint8)
    mask = np.full((8, 8), 255, dtype=np.uint8)

    full = match_color_statistics(source, target, mask, strength=1.0)
    partial = match_color_statistics(source, target, mask, strength=0.5)

    source_delta = np.mean(np.abs(partial.astype(np.int16) - source.astype(np.int16)))
    full_delta = np.mean(np.abs(full.astype(np.int16) - source.astype(np.int16)))
    assert 0 < source_delta < full_delta


def test_color_match_trim_ignores_luminance_outliers():
    source = np.full((10, 10, 3), [60, 90, 120], dtype=np.uint8)
    target = np.full((10, 10, 3), [70, 100, 130], dtype=np.uint8)
    target[0, 0] = [255, 255, 255]
    mask = np.full((10, 10), 255, dtype=np.uint8)

    untrimmed = match_color_statistics(
        source,
        target,
        mask,
        strength=1.0,
        trim_percentile=0.0,
    )
    trimmed = match_color_statistics(
        source,
        target,
        mask,
        strength=1.0,
        trim_percentile=5.0,
    )

    clean_target = np.full((10, 10, 3), [70, 100, 130], dtype=np.uint8)
    assert np.mean(np.abs(trimmed.astype(np.int16) - clean_target.astype(np.int16))) < (
        np.mean(np.abs(untrimmed.astype(np.int16) - clean_target.astype(np.int16)))
    )


def test_color_match_chroma_trim_ignores_saturated_color_outliers():
    source = np.full((10, 10, 3), [60, 90, 120], dtype=np.uint8)
    target = np.full((10, 10, 3), [70, 100, 130], dtype=np.uint8)
    target[0:2, 0:2] = [0, 255, 0]
    mask = np.full((10, 10), 255, dtype=np.uint8)

    untrimmed = match_color_statistics(
        source,
        target,
        mask,
        strength=1.0,
        chroma_trim_percentile=0.0,
    )
    trimmed = match_color_statistics(
        source,
        target,
        mask,
        strength=1.0,
        chroma_trim_percentile=5.0,
    )

    clean_target = np.full((10, 10, 3), [70, 100, 130], dtype=np.uint8)
    assert np.mean(np.abs(trimmed.astype(np.int16) - clean_target.astype(np.int16))) < (
        np.mean(np.abs(untrimmed.astype(np.int16) - clean_target.astype(np.int16)))
    )


def test_blend_color_match_statistics_smooths_previous_track_values():
    previous = ColorMatchStatistics(
        source_mean=np.array([10.0, 20.0, 30.0], dtype=np.float32),
        source_std=np.array([1.0, 2.0, 3.0], dtype=np.float32),
        target_mean=np.array([40.0, 50.0, 60.0], dtype=np.float32),
        target_std=np.array([4.0, 5.0, 6.0], dtype=np.float32),
    )
    current = ColorMatchStatistics(
        source_mean=np.array([30.0, 40.0, 50.0], dtype=np.float32),
        source_std=np.array([3.0, 4.0, 5.0], dtype=np.float32),
        target_mean=np.array([80.0, 90.0, 100.0], dtype=np.float32),
        target_std=np.array([8.0, 9.0, 10.0], dtype=np.float32),
    )

    smoothed = blend_color_match_statistics(previous, current, history_weight=0.75)

    np.testing.assert_allclose(smoothed.source_mean, [15.0, 25.0, 35.0])
    np.testing.assert_allclose(smoothed.target_mean, [50.0, 60.0, 70.0])
    np.testing.assert_allclose(smoothed.source_std, [1.5, 2.5, 3.5])
    np.testing.assert_allclose(smoothed.target_std, [5.0, 6.0, 7.0])


def test_luminance_match_strength_zero_returns_source_pixels():
    source = np.full((4, 4, 3), [30, 70, 120], dtype=np.uint8)
    target = np.full((4, 4, 3), [150, 180, 210], dtype=np.uint8)
    mask = np.full((4, 4), 255, dtype=np.uint8)

    result = match_luminance_statistics(source, target, mask, strength=0.0)

    np.testing.assert_array_equal(result, source)


def test_luminance_match_moves_brightness_without_large_chroma_shift():
    source = np.full((8, 8, 3), [40, 80, 120], dtype=np.uint8)
    target = np.full((8, 8, 3), [160, 190, 220], dtype=np.uint8)
    mask = np.full((8, 8), 255, dtype=np.uint8)

    result = match_luminance_statistics(
        source,
        target,
        mask,
        strength=1.0,
        contrast_strength=0.0,
        max_mean_shift=12.0,
    )

    source_lab = cv2.cvtColor(source.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)
    target_lab = cv2.cvtColor(target.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)
    result_lab = cv2.cvtColor(result.astype(np.float32) / 255.0, cv2.COLOR_BGR2LAB)
    source_l_delta = abs(float(source_lab[:, :, 0].mean() - target_lab[:, :, 0].mean()))
    result_l_delta = abs(float(result_lab[:, :, 0].mean() - target_lab[:, :, 0].mean()))
    source_ab = source_lab[:, :, 1:3].mean(axis=(0, 1))
    result_ab = result_lab[:, :, 1:3].mean(axis=(0, 1))

    assert result_l_delta < source_l_delta
    assert np.linalg.norm(result_ab - source_ab) < 4.0


def test_luminance_match_respects_empty_mask():
    source = np.full((4, 4, 3), [30, 70, 120], dtype=np.uint8)
    target = np.full((4, 4, 3), [150, 180, 210], dtype=np.uint8)
    mask = np.zeros((4, 4), dtype=np.uint8)

    result = match_luminance_statistics(source, target, mask, strength=1.0)

    np.testing.assert_array_equal(result, source)


def test_luminance_match_clamps_large_mean_shift():
    source = np.full((8, 8, 3), [15, 20, 25], dtype=np.uint8)
    target = np.full((8, 8, 3), [240, 245, 250], dtype=np.uint8)
    mask = np.full((8, 8), 255, dtype=np.uint8)

    limited = match_luminance_statistics(
        source, target, mask, strength=1.0, max_mean_shift=4.0
    )
    broader = match_luminance_statistics(
        source, target, mask, strength=1.0, max_mean_shift=14.0
    )

    assert broader.mean() > limited.mean()


def test_luminance_match_trim_ignores_target_highlights():
    source = np.full((10, 10, 3), [80, 80, 80], dtype=np.uint8)
    target = np.full((10, 10, 3), [120, 120, 120], dtype=np.uint8)
    target[0:2, 0:2] = [255, 255, 255]
    mask = np.full((10, 10), 255, dtype=np.uint8)

    untrimmed = match_luminance_statistics(
        source,
        target,
        mask,
        strength=1.0,
        contrast_strength=0.0,
        max_mean_shift=30.0,
        trim_percentile=0.0,
    )
    trimmed = match_luminance_statistics(
        source,
        target,
        mask,
        strength=1.0,
        contrast_strength=0.0,
        max_mean_shift=30.0,
        trim_percentile=5.0,
    )

    clean_target = np.full((10, 10, 3), [120, 120, 120], dtype=np.uint8)
    assert np.mean(np.abs(trimmed.astype(np.int16) - clean_target.astype(np.int16))) < (
        np.mean(np.abs(untrimmed.astype(np.int16) - clean_target.astype(np.int16)))
    )


def test_blend_luminance_match_statistics_smooths_previous_track_values():
    previous = LuminanceMatchStatistics(
        source_mean=20.0,
        source_std=2.0,
        target_mean=50.0,
        target_std=5.0,
    )
    current = LuminanceMatchStatistics(
        source_mean=40.0,
        source_std=6.0,
        target_mean=90.0,
        target_std=13.0,
    )

    smoothed = blend_luminance_match_statistics(
        previous,
        current,
        history_weight=0.25,
    )

    assert smoothed.source_mean == 35.0
    assert smoothed.source_std == 5.0
    assert smoothed.target_mean == 80.0
    assert smoothed.target_std == 11.0
