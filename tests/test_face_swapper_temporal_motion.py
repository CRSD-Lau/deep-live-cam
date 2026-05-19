from types import SimpleNamespace

import numpy as np
import pytest

import modules.globals
from modules.processors.frame import face_swapper


def test_motion_adjusted_interpolation_weight_boosts_fast_tracked_motion(
    monkeypatch,
):
    monkeypatch.setattr(modules.globals, "temporal_smoothing_motion_weight_boost", 0.2)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_motion_threshold", 0.1)
    monkeypatch.setattr(
        modules.globals, "temporal_smoothing_high_motion_threshold", 0.5
    )

    assert face_swapper._motion_adjusted_interpolation_weight(
        0.35,
        [SimpleNamespace(tracking_motion_amount=0.05)],
    ) == pytest.approx(0.35)
    assert face_swapper._motion_adjusted_interpolation_weight(
        0.35,
        [{"tracking_motion_amount": 0.3}],
    ) == pytest.approx(0.45)
    assert face_swapper._motion_adjusted_interpolation_weight(
        0.35,
        [SimpleNamespace(tracking_motion_amount=0.8)],
    ) == pytest.approx(0.55)


def test_motion_adjusted_interpolation_weight_bypasses_when_disabled(monkeypatch):
    monkeypatch.setattr(modules.globals, "temporal_smoothing_motion_weight_boost", 0.0)

    assert face_swapper._motion_adjusted_interpolation_weight(
        0.35,
        [SimpleNamespace(tracking_motion_amount=1.0)],
    ) == pytest.approx(0.35)


def test_adjusted_sharpness_strength_reduces_motion_and_blur(monkeypatch):
    monkeypatch.setattr(
        modules.globals,
        "postprocess_sharpness_motion_reduction",
        0.40,
    )
    monkeypatch.setattr(
        modules.globals,
        "postprocess_sharpness_blur_reduction",
        0.50,
    )
    monkeypatch.setattr(face_swapper, "estimate_blur_amount", lambda _region: 0.50)

    strength = face_swapper._adjusted_sharpness_strength(
        0.8,
        np.full((8, 8, 3), 128, dtype=np.uint8),
        SimpleNamespace(tracking_motion_amount=0.5),
    )

    assert strength == pytest.approx(0.48)


def test_adjusted_sharpness_strength_bypasses_when_reduction_disabled(monkeypatch):
    monkeypatch.setattr(
        modules.globals,
        "postprocess_sharpness_motion_reduction",
        0.0,
    )
    monkeypatch.setattr(
        modules.globals,
        "postprocess_sharpness_blur_reduction",
        0.0,
    )
    monkeypatch.setattr(
        face_swapper,
        "estimate_blur_amount",
        lambda _region: pytest.fail("blur should not be estimated"),
    )

    strength = face_swapper._adjusted_sharpness_strength(
        0.8,
        np.full((8, 8, 3), 128, dtype=np.uint8),
        SimpleNamespace(tracking_motion_amount=1.0),
    )

    assert strength == pytest.approx(0.8)


def test_apply_post_processing_uses_motion_adjusted_temporal_weight(monkeypatch):
    captured = {}

    monkeypatch.setattr(modules.globals, "sharpness", 0.0)
    monkeypatch.setattr(modules.globals, "enable_interpolation", True)
    monkeypatch.setattr(modules.globals, "interpolation_weight", 0.35)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_region_expansion", 0.0)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_feather_ratio", 0.0)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_motion_weight_boost", 0.2)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_motion_threshold", 0.1)
    monkeypatch.setattr(
        modules.globals, "temporal_smoothing_high_motion_threshold", 0.5
    )
    monkeypatch.setattr(modules.globals, "expression_temporal_smoothing", False)
    monkeypatch.setattr(modules.globals, "diagnostic_overlay", False)

    def fake_blend(_previous_frame, current_frame, _bboxes, **kwargs):
        captured["current_weight"] = kwargs["current_weight"]
        return current_frame

    monkeypatch.setattr(face_swapper, "blend_frame_regions", fake_blend)
    monkeypatch.setattr(
        face_swapper,
        "PREVIOUS_FRAME_RESULT",
        np.zeros((12, 12, 3), dtype=np.uint8),
    )

    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    face_swapper.apply_post_processing(
        current,
        [np.array([3, 3, 9, 9])],
        [{"tracking_motion_amount": 0.5}],
    )

    assert captured["current_weight"] == pytest.approx(0.55)


def test_expression_adjusted_weight_passes_unilateral_eye_scale(monkeypatch):
    captured = {}

    monkeypatch.setattr(modules.globals, "expression_temporal_smoothing", True)
    monkeypatch.setattr(
        modules.globals,
        "expression_temporal_unilateral_eye_motion_scale",
        0.42,
    )
    monkeypatch.setattr(
        face_swapper,
        "collect_expression_snapshots",
        lambda _faces: {"track:1": object()},
    )

    def fake_expression_temporal_weight(base_weight, previous, current, **kwargs):
        captured["base_weight"] = base_weight
        captured["previous"] = previous
        captured["current"] = current
        captured.update(kwargs)
        return 0.51

    monkeypatch.setattr(
        face_swapper,
        "expression_temporal_weight",
        fake_expression_temporal_weight,
    )
    monkeypatch.setattr(face_swapper, "PREVIOUS_EXPRESSION_SNAPSHOTS", {"track:1": object()})

    assert face_swapper._expression_adjusted_interpolation_weight(
        0.35,
        [object()],
    ) == pytest.approx(0.51)
    assert captured["unilateral_eye_motion_scale"] == pytest.approx(0.42)


def test_apply_post_processing_uses_adjusted_sharpness_strength(monkeypatch):
    captured = {}

    monkeypatch.setattr(modules.globals, "sharpness", 0.8)
    monkeypatch.setattr(modules.globals, "enable_interpolation", False)
    monkeypatch.setattr(
        modules.globals,
        "postprocess_sharpness_motion_reduction",
        0.40,
    )
    monkeypatch.setattr(
        modules.globals,
        "postprocess_sharpness_blur_reduction",
        0.50,
    )
    monkeypatch.setattr(modules.globals, "diagnostic_overlay", False)
    monkeypatch.setattr(face_swapper, "estimate_blur_amount", lambda _region: 0.50)

    def fake_sharpen(region, *, strength, sigma):
        captured["strength"] = strength
        captured["sigma"] = sigma
        return region

    monkeypatch.setattr(face_swapper, "gpu_sharpen", fake_sharpen)

    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    face_swapper.apply_post_processing(
        current,
        [np.array([3, 3, 9, 9])],
        [SimpleNamespace(tracking_motion_amount=0.5)],
    )

    assert captured["strength"] == pytest.approx(0.48)
