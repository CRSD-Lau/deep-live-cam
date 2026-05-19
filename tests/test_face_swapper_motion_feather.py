from types import SimpleNamespace

import numpy as np
import pytest

import modules.globals
from modules.processors.frame import face_swapper


def test_fast_paste_back_passes_tracking_motion_to_adaptive_feather(monkeypatch):
    captured = {}

    def fake_settings(**kwargs):
        captured.update(kwargs)
        return face_swapper.FeatherSettings(erode_ratio=0.1, blur_ratio=0.05)

    monkeypatch.setattr(face_swapper, "get_adaptive_feather_settings", fake_settings)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(modules.globals, "compositing_mask_motion_strength", 0.4)
    monkeypatch.setattr(modules.globals, "compositing_mask_profile_strength", 0.3)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)
    face = SimpleNamespace(
        tracking_motion_amount=0.6,
        kps=np.array(
            [
                [40.0, 40.0],
                [80.0, 40.0],
                [82.0, 60.0],
                [46.0, 84.0],
                [74.0, 84.0],
            ],
            dtype=np.float32,
        ),
    )

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, target_face=face)

    assert captured["motion_amount"] == 0.6
    assert captured["motion_strength"] == 0.4
    assert captured["profile_amount"] > 0.8
    assert captured["profile_strength"] == 0.3


def test_fast_paste_back_passes_motion_blur_to_adaptive_feather(monkeypatch):
    captured = {}

    def fake_settings(**kwargs):
        captured.update(kwargs)
        return face_swapper.FeatherSettings(erode_ratio=0.1, blur_ratio=0.05)

    monkeypatch.setattr(face_swapper, "get_adaptive_feather_settings", fake_settings)
    monkeypatch.setattr(face_swapper, "estimate_blur_amount", lambda _crop: 0.72)
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(
        modules.globals,
        "compositing_mask_motion_blur_strength",
        0.28,
    )
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, target_face=None)

    assert captured["blur_amount"] == 0.72
    assert captured["blur_strength"] == 0.28


def test_tracking_motion_amount_clamps_invalid_values():
    assert (
        face_swapper._tracking_motion_amount(
            SimpleNamespace(tracking_motion_amount=2.0),
        )
        == 1.0
    )
    assert (
        face_swapper._tracking_motion_amount(
            SimpleNamespace(tracking_motion_amount=-1.0),
        )
        == 0.0
    )
    assert (
        face_swapper._tracking_motion_amount(
            SimpleNamespace(tracking_motion_amount="bad"),
        )
        == 0.0
    )


def test_tracking_motion_amount_reads_plain_mapping_faces():
    assert face_swapper._tracking_motion_amount({"tracking_motion_amount": 0.6}) == 0.6


def test_fast_paste_back_passes_occlusion_edge_controls(monkeypatch):
    captured = {}

    def fake_preserve(alpha_crop, target_crop, **kwargs):
        captured["alpha_shape"] = alpha_crop.shape
        captured["target_shape"] = target_crop.shape
        captured.update(kwargs)
        return alpha_crop

    monkeypatch.setattr(
        face_swapper,
        "get_adaptive_feather_settings",
        lambda **_kwargs: face_swapper.FeatherSettings(
            erode_ratio=0.1,
            blur_ratio=0.05,
        ),
    )
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "preserve_target_edges_in_alpha", fake_preserve)
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.25)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_threshold", 0.31)
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_edge_max_reduction",
        0.44,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_edge_blur_ratio",
        0.02,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_edge_min_contrast",
        19.0,
    )
    monkeypatch.setattr(modules.globals, "compositing_occlusion_detail_strength", 0.17)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_detail_threshold", 0.09)

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    target[:, 6] = 0
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, target_face=None)

    assert captured["target_shape"][:2] == captured["alpha_shape"]
    assert captured["strength"] == 0.25
    assert captured["edge_threshold"] == 0.31
    assert captured["max_reduction"] == 0.44
    assert captured["blur_ratio"] == 0.02
    assert captured["min_contrast"] == 19.0
    assert captured["detail_strength"] == 0.17
    assert captured["detail_threshold"] == 0.09


def test_fast_paste_back_passes_expression_occlusion_priority_mask(monkeypatch):
    captured = {}
    priority = np.full((9, 9), 128, dtype=np.uint8)

    def fake_expression_mask(face, frame_shape, crop_bounds, **kwargs):
        captured["face"] = face
        captured["frame_shape"] = frame_shape
        captured["crop_bounds"] = crop_bounds
        captured["mask_kwargs"] = kwargs
        return priority

    def fake_preserve(alpha_crop, target_crop, **kwargs):
        captured["alpha_shape"] = alpha_crop.shape
        captured["target_shape"] = target_crop.shape
        captured["preserve_kwargs"] = kwargs
        return alpha_crop

    monkeypatch.setattr(
        face_swapper,
        "get_adaptive_feather_settings",
        lambda **_kwargs: face_swapper.FeatherSettings(
            erode_ratio=0.1,
            blur_ratio=0.05,
        ),
    )
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(
        face_swapper,
        "create_expression_occlusion_mask",
        fake_expression_mask,
    )
    monkeypatch.setattr(face_swapper, "preserve_target_edges_in_alpha", fake_preserve)
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_skin_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_alpha_temporal_smoothing", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.25)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_region_boost", 0.65)
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_mouth_region_strength",
        0.85,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_eye_region_strength",
        0.55,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_region_feather_ratio",
        0.019,
    )
    monkeypatch.setattr(modules.globals, "expression_mouth_min_confidence", 0.31)
    monkeypatch.setattr(modules.globals, "expression_eye_min_confidence", 0.27)

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)
    face = SimpleNamespace()

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, target_face=face)

    assert captured["face"] is face
    assert captured["frame_shape"] == target.shape
    assert captured["crop_bounds"] == (2, 2, 11, 11)
    assert captured["mask_kwargs"]["mouth_strength"] == 0.85
    assert captured["mask_kwargs"]["eye_strength"] == 0.55
    assert captured["mask_kwargs"]["feather_ratio"] == 0.019
    assert captured["mask_kwargs"]["mouth_min_confidence"] == 0.31
    assert captured["mask_kwargs"]["eye_min_confidence"] == 0.27
    assert captured["preserve_kwargs"]["priority_mask"] is priority
    assert captured["preserve_kwargs"]["priority_strength"] == 0.65


def test_occlusion_priority_mask_temporally_smooths_by_track(monkeypatch):
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_region_temporal_smoothing",
        0.5,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_region_temporal_motion_reduction",
        0.0,
    )
    face_swapper.reset_compositing_temporal_state()

    first = np.zeros((4, 4), dtype=np.uint8)
    first[:, :2] = 255
    second = np.zeros((4, 4), dtype=np.uint8)
    second[:, 2:] = 255
    face = SimpleNamespace(tracking_id=7, tracking_motion_amount=0.0)

    initial = face_swapper._smooth_occlusion_priority_mask(first, face)
    smoothed = face_swapper._smooth_occlusion_priority_mask(second, face)

    np.testing.assert_array_equal(initial, first)
    assert smoothed[:, :2].mean() == pytest.approx(128.0, abs=1.0)
    assert smoothed[:, 2:].mean() == pytest.approx(128.0, abs=1.0)


def test_occlusion_priority_mask_motion_reduces_temporal_smoothing(monkeypatch):
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_region_temporal_smoothing",
        0.5,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_region_temporal_motion_reduction",
        1.0,
    )
    face_swapper.reset_compositing_temporal_state()

    first = np.zeros((4, 4), dtype=np.uint8)
    first[:, :2] = 255
    second = np.zeros((4, 4), dtype=np.uint8)
    second[:, 2:] = 255
    face_swapper._smooth_occlusion_priority_mask(
        first,
        SimpleNamespace(tracking_id=7, tracking_motion_amount=0.0),
    )
    smoothed = face_swapper._smooth_occlusion_priority_mask(
        second,
        SimpleNamespace(tracking_id=7, tracking_motion_amount=1.0),
    )

    np.testing.assert_array_equal(smoothed, second)


def test_occlusion_priority_mask_resets_on_missed_track(monkeypatch):
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_region_temporal_smoothing",
        0.5,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_occlusion_region_temporal_motion_reduction",
        0.0,
    )
    face_swapper.reset_compositing_temporal_state()

    first = np.zeros((4, 4), dtype=np.uint8)
    first[:, :2] = 255
    second = np.zeros((4, 4), dtype=np.uint8)
    second[:, 2:] = 255
    face_swapper._smooth_occlusion_priority_mask(
        first,
        SimpleNamespace(tracking_id=7, tracking_motion_amount=0.0),
    )
    smoothed = face_swapper._smooth_occlusion_priority_mask(
        second,
        SimpleNamespace(
            tracking_id=7,
            tracking_motion_amount=0.0,
            tracking_missed_frames=1,
        ),
    )

    np.testing.assert_array_equal(smoothed, second)
    assert face_swapper.COMPOSITING_OCCLUSION_PRIORITY_MASKS["mask"] == {}


def test_fast_paste_back_passes_skin_chroma_mask_controls(monkeypatch):
    captured = {}

    def fake_skin_mask(alpha_crop, target_crop, **kwargs):
        captured["alpha_shape"] = alpha_crop.shape
        captured["target_shape"] = target_crop.shape
        captured.update(kwargs)
        return alpha_crop

    monkeypatch.setattr(
        face_swapper,
        "get_adaptive_feather_settings",
        lambda **_kwargs: face_swapper.FeatherSettings(
            erode_ratio=0.1,
            blur_ratio=0.05,
        ),
    )
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(
        face_swapper,
        "refine_alpha_with_skin_chroma_mask",
        fake_skin_mask,
    )
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_skin_mask_strength", 0.21)
    monkeypatch.setattr(
        modules.globals,
        "compositing_skin_mask_chroma_threshold",
        1.55,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_skin_mask_max_reduction",
        0.42,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_skin_mask_blur_ratio",
        0.017,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_skin_mask_luma_threshold",
        1.25,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_skin_mask_luma_max_reduction",
        0.31,
    )
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, target_face=None)

    assert captured["target_shape"][:2] == captured["alpha_shape"]
    assert captured["strength"] == 0.21
    assert captured["chroma_threshold"] == 1.55
    assert captured["max_reduction"] == 0.42
    assert captured["blur_ratio"] == 0.017
    assert captured["luma_threshold"] == 1.25
    assert captured["luma_max_reduction"] == 0.31


def test_fast_paste_back_passes_boundary_mismatch_controls(monkeypatch):
    captured = {}

    def fake_boundary(alpha_crop, source_crop, target_crop, **kwargs):
        captured["alpha_shape"] = alpha_crop.shape
        captured["source_shape"] = source_crop.shape
        captured["target_shape"] = target_crop.shape
        captured.update(kwargs)
        return alpha_crop

    monkeypatch.setattr(
        face_swapper,
        "get_adaptive_feather_settings",
        lambda **_kwargs: face_swapper.FeatherSettings(
            erode_ratio=0.1,
            blur_ratio=0.05,
        ),
    )
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(
        face_swapper,
        "refine_alpha_with_boundary_color_mismatch",
        fake_boundary,
    )
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_skin_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_alpha_temporal_smoothing", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)
    monkeypatch.setattr(
        modules.globals,
        "compositing_boundary_mismatch_strength",
        0.22,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_boundary_mismatch_threshold",
        0.14,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_boundary_mismatch_max_reduction",
        0.39,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_boundary_mismatch_band_ratio",
        0.041,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_boundary_mismatch_blur_ratio",
        0.013,
    )

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, target_face=None)

    assert captured["source_shape"][:2] == captured["alpha_shape"]
    assert captured["target_shape"][:2] == captured["alpha_shape"]
    assert captured["strength"] == 0.22
    assert captured["color_threshold"] == 0.14
    assert captured["max_reduction"] == 0.39
    assert captured["band_ratio"] == 0.041
    assert captured["blur_ratio"] == 0.013


def test_fast_paste_back_passes_alpha_temporal_smoothing(monkeypatch):
    captured = {}

    def fake_smooth(alpha_crop, track_key, history_weight):
        captured["alpha_shape"] = alpha_crop.shape
        captured["track_key"] = track_key
        captured["history_weight"] = history_weight
        return alpha_crop

    monkeypatch.setattr(
        face_swapper,
        "get_adaptive_feather_settings",
        lambda **_kwargs: face_swapper.FeatherSettings(
            erode_ratio=0.1,
            blur_ratio=0.05,
        ),
    )
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "_smooth_compositing_alpha", fake_smooth)
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_skin_mask_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_alpha_temporal_smoothing", 0.4)
    monkeypatch.setattr(
        modules.globals,
        "compositing_alpha_temporal_motion_threshold",
        0.1,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_alpha_temporal_high_motion_threshold",
        0.5,
    )
    monkeypatch.setattr(
        modules.globals,
        "compositing_alpha_temporal_motion_reduction",
        0.5,
    )
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)
    face = SimpleNamespace(tracking_id=12, tracking_motion_amount=0.3)

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, target_face=face)

    assert captured["alpha_shape"] == (9, 9)
    assert captured["track_key"] == "track:12"
    assert abs(captured["history_weight"] - 0.3) < 1e-6


def test_fast_paste_back_passes_profile_taper_to_landmark_refinement(monkeypatch):
    captured = {}

    def fake_refine(alpha_crop, face, frame_shape, crop_bounds, **kwargs):
        captured["face"] = face
        captured["frame_shape"] = frame_shape
        captured["crop_bounds"] = crop_bounds
        captured.update(kwargs)
        return alpha_crop

    monkeypatch.setattr(
        face_swapper,
        "get_adaptive_feather_settings",
        lambda **_kwargs: face_swapper.FeatherSettings(
            erode_ratio=0.1,
            blur_ratio=0.05,
        ),
    )
    monkeypatch.setattr(
        face_swapper,
        "_get_soft_alpha",
        lambda size, _settings: np.full((size, size), 255, dtype=np.uint8),
    )
    monkeypatch.setattr(face_swapper, "refine_alpha_with_landmark_mask", fake_refine)
    monkeypatch.setattr(face_swapper, "_HAS_TORCH_CUDA", False)
    monkeypatch.setattr(modules.globals, "compositing_landmark_mask_strength", 0.5)
    monkeypatch.setattr(
        modules.globals,
        "compositing_landmark_mask_profile_taper",
        0.25,
    )
    monkeypatch.setattr(modules.globals, "compositing_color_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_lighting_match_strength", 0.0)
    monkeypatch.setattr(modules.globals, "compositing_occlusion_edge_strength", 0.0)

    target = np.full((12, 12, 3), 160, dtype=np.uint8)
    fake = np.full((4, 4, 3), 40, dtype=np.uint8)
    matrix = np.array([[1.0, 0.0, -4.0], [0.0, 1.0, -4.0]], dtype=np.float32)
    face = SimpleNamespace(
        kps=np.array(
            [
                [40.0, 40.0],
                [80.0, 40.0],
                [82.0, 60.0],
                [46.0, 84.0],
                [74.0, 84.0],
            ],
            dtype=np.float32,
        ),
    )

    face_swapper._fast_paste_back(target.copy(), fake, fake, matrix, target_face=face)

    assert captured["strength"] == 0.5
    assert captured["profile_amount"] > 0.8
    assert captured["profile_taper_ratio"] == 0.25
