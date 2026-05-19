from types import SimpleNamespace

import numpy as np
import pytest

import modules.globals
from modules.compositing.color import ColorMatchStatistics, LuminanceMatchStatistics
from modules.processors.frame import face_swapper


def test_fast_paste_back_applies_luminance_compensation(monkeypatch):
    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 1.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_contrast_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_max_shift", 12.0)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)

    result = face_swapper._fast_paste_back(target.copy(), fake, fake, matrix)

    assert result[5, 5, 0] > 40
    assert result[5, 5, 0] < 160


def test_fast_paste_back_skips_luminance_compensation_when_disabled(monkeypatch):
    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)

    result = face_swapper._fast_paste_back(target.copy(), fake, fake, matrix)

    assert result[5, 5, 0] <= 80


def test_fast_paste_back_passes_color_trims_to_color_and_lighting(monkeypatch):
    captured = {}

    def fake_color(source, _target, _mask, **kwargs):
        captured["color_trim"] = kwargs["trim_percentile"]
        captured["color_chroma_trim"] = kwargs["chroma_trim_percentile"]
        return source

    def fake_lighting(source, _target, _mask, **kwargs):
        captured["lighting_trim"] = kwargs["trim_percentile"]
        return source

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "match_color_statistics", fake_color)
    monkeypatch.setattr(face_swapper, "match_luminance_statistics", fake_lighting)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 1.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 1.0)
    monkeypatch.setattr(modules.globals, "compositing_color_match_trim_percentile", 5.0)
    monkeypatch.setattr(
        modules.globals, "compositing_color_chroma_trim_percentile", 4.0
    )
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix)

    assert captured["color_trim"] == 5.0
    assert captured["color_chroma_trim"] == 4.0
    assert captured["lighting_trim"] == 5.0


def test_fast_paste_back_smooths_color_and_lighting_stats_by_track(monkeypatch):
    color_targets = [100.0, 140.0]
    lighting_targets = [50.0, 90.0]
    captured = {"color": [], "lighting": []}

    def fake_color(source, _target, _mask, **kwargs):
        stats = ColorMatchStatistics(
            source_mean=np.array([10.0, 10.0, 10.0], dtype=np.float32),
            source_std=np.ones(3, dtype=np.float32),
            target_mean=np.full(3, color_targets.pop(0), dtype=np.float32),
            target_std=np.ones(3, dtype=np.float32),
        )
        transformed = kwargs["statistics_transform"](stats)
        captured["color"].append(float(transformed.target_mean[0]))
        return source

    def fake_lighting(source, _target, _mask, **kwargs):
        stats = LuminanceMatchStatistics(
            source_mean=10.0,
            source_std=1.0,
            target_mean=lighting_targets.pop(0),
            target_std=1.0,
        )
        transformed = kwargs["statistics_transform"](stats)
        captured["lighting"].append(transformed.target_mean)
        return source

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)
    tracked_face = SimpleNamespace(tracking_id=7)

    face_swapper.reset_compositing_temporal_state()
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "match_color_statistics", fake_color)
    monkeypatch.setattr(face_swapper, "match_luminance_statistics", fake_lighting)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 1.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 1.0)
    monkeypatch.setattr(modules.globals, "compositing_color_match_trim_percentile", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_temporal_smoothing", 0.5)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, tracked_face)
    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, tracked_face)

    assert captured["color"] == [100.0, 120.0]
    assert captured["lighting"] == [50.0, 70.0]


def test_fast_paste_back_reduces_color_history_during_fast_motion(monkeypatch):
    color_targets = [100.0, 140.0]
    captured = []

    def fake_color(source, _target, _mask, **kwargs):
        stats = ColorMatchStatistics(
            source_mean=np.array([10.0, 10.0, 10.0], dtype=np.float32),
            source_std=np.ones(3, dtype=np.float32),
            target_mean=np.full(3, color_targets.pop(0), dtype=np.float32),
            target_std=np.ones(3, dtype=np.float32),
        )
        transformed = kwargs["statistics_transform"](stats)
        captured.append(float(transformed.target_mean[0]))
        return source

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    face_swapper.reset_compositing_temporal_state()
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "match_color_statistics", fake_color)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 1.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_temporal_smoothing", 0.5)
    monkeypatch.setattr(
        modules.globals, "compositing_color_temporal_motion_threshold", 0.1
    )
    monkeypatch.setattr(
        modules.globals, "compositing_color_temporal_high_motion_threshold", 0.5
    )
    monkeypatch.setattr(
        modules.globals, "compositing_color_temporal_motion_reduction", 0.6
    )
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)

    face_swapper._fast_paste_back(
        target.copy(),
        fake,
        fake,
        matrix,
        SimpleNamespace(tracking_id=9, tracking_motion_amount=0.0),
    )
    face_swapper._fast_paste_back(
        target.copy(),
        fake,
        fake,
        matrix,
        SimpleNamespace(tracking_id=9, tracking_motion_amount=0.5),
    )

    assert captured == pytest.approx([100.0, 132.0])


def test_fast_paste_back_resets_color_history_on_missed_tracking(monkeypatch):
    color_targets = [100.0, 140.0, 180.0]
    captured = []

    def fake_color(source, _target, _mask, **kwargs):
        stats = ColorMatchStatistics(
            source_mean=np.array([10.0, 10.0, 10.0], dtype=np.float32),
            source_std=np.ones(3, dtype=np.float32),
            target_mean=np.full(3, color_targets.pop(0), dtype=np.float32),
            target_std=np.ones(3, dtype=np.float32),
        )
        transform = kwargs["statistics_transform"]
        transformed = transform(stats) if transform is not None else stats
        captured.append(float(transformed.target_mean[0]))
        return source

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    face_swapper.reset_compositing_temporal_state()
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "match_color_statistics", fake_color)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 1.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_temporal_smoothing", 0.5)
    monkeypatch.setattr(
        modules.globals, "compositing_color_temporal_motion_reduction", 0.0
    )
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)

    face_swapper._fast_paste_back(
        target.copy(),
        fake,
        fake,
        matrix,
        SimpleNamespace(tracking_id=11, tracking_missed_frames=0),
    )
    face_swapper._fast_paste_back(
        target.copy(),
        fake,
        fake,
        matrix,
        SimpleNamespace(tracking_id=11, tracking_missed_frames=1),
    )
    face_swapper._fast_paste_back(
        target.copy(),
        fake,
        fake,
        matrix,
        SimpleNamespace(tracking_id=11, tracking_missed_frames=0),
    )

    assert captured == [100.0, 140.0, 180.0]


def test_fast_paste_back_preserves_color_history_on_predicted_tracking_hold(
    monkeypatch,
):
    color_targets = [100.0, 140.0]
    captured = []

    def fake_color(source, _target, _mask, **kwargs):
        stats = ColorMatchStatistics(
            source_mean=np.array([10.0, 10.0, 10.0], dtype=np.float32),
            source_std=np.ones(3, dtype=np.float32),
            target_mean=np.full(3, color_targets.pop(0), dtype=np.float32),
            target_std=np.ones(3, dtype=np.float32),
        )
        transform = kwargs["statistics_transform"]
        transformed = transform(stats) if transform is not None else stats
        captured.append(float(transformed.target_mean[0]))
        return source

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    face_swapper.reset_compositing_temporal_state()
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "match_color_statistics", fake_color)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 1.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_temporal_smoothing", 0.5)
    monkeypatch.setattr(
        modules.globals, "compositing_color_temporal_motion_reduction", 0.0
    )
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)

    face_swapper._fast_paste_back(
        target.copy(),
        fake,
        fake,
        matrix,
        SimpleNamespace(tracking_id=12, tracking_missed_frames=0),
    )
    face_swapper._fast_paste_back(
        target.copy(),
        fake,
        fake,
        matrix,
        SimpleNamespace(
            tracking_id=12,
            tracking_missed_frames=1,
            tracking_prediction_active=True,
        ),
    )

    assert captured == [100.0, 120.0]


def test_smooth_compositing_alpha_blends_by_track():
    face_swapper.reset_compositing_temporal_state()
    first = np.full((4, 4), 100, dtype=np.uint8)
    second = np.full((4, 4), 200, dtype=np.uint8)

    initial = face_swapper._smooth_compositing_alpha(first, "track:alpha", 0.5)
    smoothed = face_swapper._smooth_compositing_alpha(second, "track:alpha", 0.5)

    np.testing.assert_array_equal(initial, first)
    assert smoothed.mean() == 150


def test_smooth_compositing_alpha_resets_on_shape_change():
    face_swapper.reset_compositing_temporal_state()
    face_swapper._smooth_compositing_alpha(
        np.full((4, 4), 100, dtype=np.uint8),
        "track:alpha",
        0.5,
    )
    changed = np.full((5, 4), 200, dtype=np.uint8)

    result = face_swapper._smooth_compositing_alpha(changed, "track:alpha", 0.5)

    np.testing.assert_array_equal(result, changed)


def test_motion_adjusted_alpha_temporal_strength_reduces_history(monkeypatch):
    monkeypatch.setattr(modules.globals, "compositing_alpha_temporal_motion_threshold", 0.1)
    monkeypatch.setattr(
        modules.globals,
        "compositing_alpha_temporal_high_motion_threshold",
        0.5,
    )
    monkeypatch.setattr(modules.globals, "compositing_alpha_temporal_motion_reduction", 0.6)

    still = face_swapper._motion_adjusted_compositing_alpha_temporal_strength(
        0.4,
        SimpleNamespace(tracking_motion_amount=0.0),
    )
    moving = face_swapper._motion_adjusted_compositing_alpha_temporal_strength(
        0.4,
        SimpleNamespace(tracking_motion_amount=0.5),
    )

    assert still == pytest.approx(0.4)
    assert moving == pytest.approx(0.16)


def test_prediction_hold_preserves_temporal_strength(monkeypatch):
    monkeypatch.setattr(
        modules.globals,
        "compositing_color_temporal_motion_reduction",
        0.0,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_alpha_temporal_motion_reduction",
        0.0,
    )
    predicted = SimpleNamespace(
        tracking_missed_frames=1,
        tracking_prediction_active=True,
    )

    color_strength = face_swapper._motion_adjusted_compositing_temporal_strength(
        0.42,
        predicted,
    )
    alpha_strength = (
        face_swapper._motion_adjusted_compositing_alpha_temporal_strength(
            0.37,
            predicted,
        )
    )

    assert color_strength == pytest.approx(0.42)
    assert alpha_strength == pytest.approx(0.37)
