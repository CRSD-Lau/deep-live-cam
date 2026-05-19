from dataclasses import fields
from types import SimpleNamespace

import pytest

from modules.quality_profiles import (
    QUALITY_MODE_NAMES,
    QUALITY_PROFILE_METADATA_FIELDS,
    QUALITY_PROFILE_RUNTIME_FIELDS,
    QualityProfile,
    apply_quality_profile,
    get_quality_profile,
    quality_profile_runtime_state,
    restore_quality_profile_runtime_state,
)


def blank_state():
    return SimpleNamespace(fp_ui={}, quality_mode="balanced")


def test_profiles_cover_required_modes():
    assert QUALITY_MODE_NAMES == ("realtime", "balanced", "cinematic", "experimental")
    assert get_quality_profile("cinematic").enhancer == "face_enhancer_gpen512"


def test_runtime_fields_track_profile_schema_without_metadata():
    profile_fields = {field.name for field in fields(QualityProfile)}

    assert set(QUALITY_PROFILE_RUNTIME_FIELDS) == (
        profile_fields - QUALITY_PROFILE_METADATA_FIELDS
    )
    assert "enhancer" not in QUALITY_PROFILE_RUNTIME_FIELDS
    assert "compositing_skin_mask_luma_threshold" in QUALITY_PROFILE_RUNTIME_FIELDS
    assert "compositing_occlusion_detail_strength" in QUALITY_PROFILE_RUNTIME_FIELDS
    assert (
        "expression_temporal_unilateral_eye_motion_scale"
        in QUALITY_PROFILE_RUNTIME_FIELDS
    )
    assert "live_process_latest_frame" in QUALITY_PROFILE_RUNTIME_FIELDS


def test_quality_profile_runtime_state_captures_available_runtime_fields_only():
    state = SimpleNamespace(
        enhancer="face_enhancer",
        quality_mode="cinematic",
        live_process_latest_frame=False,
        compositing_skin_mask_luma_threshold=1.25,
    )

    captured = quality_profile_runtime_state(state)

    assert captured == {
        "live_process_latest_frame": False,
        "compositing_skin_mask_luma_threshold": 1.25,
    }


def test_restore_quality_profile_runtime_state_restores_known_runtime_fields_only():
    state = SimpleNamespace(
        quality_mode="balanced",
        live_process_latest_frame=True,
        compositing_skin_mask_luma_threshold=0.0,
    )

    restore_quality_profile_runtime_state(
        state,
        {
            "quality_mode": "experimental",
            "enhancer": "face_enhancer",
            "live_process_latest_frame": False,
            "compositing_skin_mask_luma_threshold": 1.45,
            "unknown_new_key": "ignored",
        },
    )

    assert state.quality_mode == "balanced"
    assert not hasattr(state, "enhancer")
    assert not hasattr(state, "unknown_new_key")
    assert state.live_process_latest_frame is False
    assert state.compositing_skin_mask_luma_threshold == 1.45


def test_apply_quality_profile_sets_every_runtime_field_from_profile():
    state = blank_state()

    profile = apply_quality_profile("experimental", state)

    for field_name in QUALITY_PROFILE_RUNTIME_FIELDS:
        assert getattr(state, field_name) == getattr(profile, field_name)


def test_cinematic_profile_sets_quality_defaults():
    state = blank_state()

    profile = apply_quality_profile("cinematic", state)

    assert profile.name == "cinematic"
    assert state.quality_mode == "cinematic"
    assert state.fp_ui["face_enhancer_gpen512"] is True
    assert state.fp_ui["face_enhancer"] is False
    assert state.mouth_mask is True
    assert state.expression_mouth_min_confidence == 0.35
    assert state.expression_eye_min_confidence == 0.30
    assert state.enable_interpolation is True
    assert state.live_process_latest_frame is True
    assert 0.0 < state.interpolation_weight < 1.0
    assert state.temporal_smoothing_region_expansion > 0.0
    assert state.temporal_smoothing_feather_ratio > 0.0
    assert state.temporal_smoothing_mask_strength > 0.0
    assert 0.0 < state.temporal_smoothing_expression_region_boost < 1.0
    assert 0.0 < state.temporal_smoothing_expression_mouth_strength <= 1.0
    assert 0.0 < state.temporal_smoothing_expression_eye_strength <= 1.0
    assert state.temporal_smoothing_expression_feather_ratio > 0.0
    assert state.expression_temporal_smoothing is True
    assert 0.0 < state.expression_temporal_stable_weight_multiplier < 1.0
    assert state.expression_temporal_motion_threshold > 0.0
    assert state.expression_temporal_high_motion_threshold > (
        state.expression_temporal_motion_threshold
    )
    assert state.expression_temporal_motion_weight_boost > 0.0
    assert 0.0 < state.expression_temporal_unilateral_eye_motion_scale < 1.0
    assert 0.0 < state.postprocess_sharpness_motion_reduction < 1.0
    assert 0.0 < state.postprocess_sharpness_blur_reduction < 1.0
    assert state.face_tracking_enabled is True
    assert 0.0 < state.face_tracking_current_weight < 1.0
    assert state.face_tracking_reset_ratio > 0.0
    assert state.face_tracking_max_missed >= 1
    assert 0.0 < state.face_tracking_confidence_weight < 1.0
    assert state.face_tracking_confidence_reference > 0.0
    assert 0.0 < state.face_tracking_confidence_min_weight < 1.0
    assert 0.0 < state.face_tracking_min_detection_confidence < 1.0
    assert 0.0 < state.mouth_mask_temporal_smoothing < 1.0
    assert 0.0 < state.mouth_mask_temporal_motion_reduction < 1.0
    assert 0.0 < state.compositing_color_match_strength <= 1.0
    assert state.compositing_color_match_trim_percentile > 0.0
    assert state.compositing_color_chroma_trim_percentile > 0.0
    assert 0.0 < state.compositing_color_temporal_smoothing < 1.0
    assert state.compositing_color_temporal_motion_threshold > 0.0
    assert state.compositing_color_temporal_high_motion_threshold > (
        state.compositing_color_temporal_motion_threshold
    )
    assert 0.0 < state.compositing_color_temporal_motion_reduction < 1.0
    assert 0.0 < state.compositing_lighting_match_strength <= 1.0
    assert 0.0 < state.compositing_lighting_contrast_strength <= 1.0
    assert state.compositing_lighting_max_shift > 0.0
    assert state.compositing_mask_erode_ratio > 0.0
    assert state.compositing_mask_blur_ratio > 0.0
    assert state.compositing_mask_scale_strength > 0.0
    assert state.compositing_mask_edge_strength > 0.0
    assert state.compositing_mask_motion_blur_strength > 0.0
    assert state.compositing_mask_motion_strength > 0.0
    assert state.compositing_mask_profile_strength > 0.0
    assert 0.0 < state.compositing_landmark_mask_strength < 1.0
    assert state.compositing_landmark_mask_dilation_ratio > 0.0
    assert state.compositing_landmark_mask_feather_ratio > 0.0
    assert state.compositing_landmark_mask_profile_taper > 0.0
    assert 0.0 < state.compositing_skin_mask_strength < 1.0
    assert state.compositing_skin_mask_chroma_threshold > 0.0
    assert 0.0 < state.compositing_skin_mask_max_reduction < 1.0
    assert state.compositing_skin_mask_blur_ratio > 0.0
    assert 0.0 < state.compositing_alpha_temporal_smoothing < 1.0
    assert state.compositing_alpha_temporal_motion_threshold > 0.0
    assert state.compositing_alpha_temporal_high_motion_threshold > (
        state.compositing_alpha_temporal_motion_threshold
    )
    assert 0.0 < state.compositing_alpha_temporal_motion_reduction < 1.0
    assert 0.0 < state.compositing_occlusion_edge_strength < 1.0
    assert 0.0 < state.compositing_occlusion_edge_threshold < 1.0
    assert 0.0 < state.compositing_occlusion_edge_max_reduction < 1.0
    assert state.compositing_occlusion_edge_blur_ratio > 0.0
    assert state.compositing_occlusion_edge_min_contrast > 0.0
    assert 0.0 < state.compositing_occlusion_region_boost < 1.0
    assert 0.0 < state.compositing_occlusion_mouth_region_strength <= 1.0
    assert 0.0 < state.compositing_occlusion_eye_region_strength < 1.0
    assert state.compositing_occlusion_region_feather_ratio > 0.0
    assert 0.0 < state.compositing_occlusion_region_temporal_smoothing < 1.0
    assert 0.0 < state.compositing_occlusion_region_temporal_motion_reduction < 1.0


def test_realtime_profile_disables_heavy_quality_features():
    state = blank_state()

    apply_quality_profile("realtime", state)

    assert state.quality_mode == "realtime"
    assert all(state.fp_ui[key] is False for key in state.fp_ui)
    assert state.mouth_mask is False
    assert state.expression_mouth_min_confidence == 0.0
    assert state.expression_eye_min_confidence == 0.0
    assert state.mouth_mask_temporal_smoothing == 0.0
    assert state.mouth_mask_temporal_motion_reduction == 0.0
    assert state.enable_interpolation is False
    assert state.live_process_latest_frame is True
    assert state.temporal_smoothing_region_expansion > 0.0
    assert state.temporal_smoothing_mask_strength == 0.0
    assert state.temporal_smoothing_expression_region_boost == 0.0
    assert state.temporal_smoothing_expression_mouth_strength == 0.0
    assert state.temporal_smoothing_expression_eye_strength == 0.0
    assert state.expression_temporal_smoothing is False
    assert state.expression_temporal_motion_weight_boost == 0.0
    assert state.expression_temporal_unilateral_eye_motion_scale == 1.0
    assert state.postprocess_sharpness_motion_reduction == 0.0
    assert state.postprocess_sharpness_blur_reduction == 0.0
    assert state.poisson_blend is False
    assert state.face_tracking_enabled is False
    assert state.face_tracking_confidence_weight == 0.0
    assert state.face_tracking_min_detection_confidence == 0.0
    assert state.compositing_color_match_strength == 0.0
    assert state.compositing_color_match_trim_percentile == 0.0
    assert state.compositing_color_chroma_trim_percentile == 0.0
    assert state.compositing_color_temporal_smoothing == 0.0
    assert state.compositing_color_temporal_motion_reduction == 0.0
    assert state.compositing_lighting_match_strength == 0.0
    assert state.compositing_mask_edge_strength == 0.0
    assert state.compositing_mask_motion_blur_strength == 0.0
    assert state.compositing_mask_motion_strength == 0.0
    assert state.compositing_mask_profile_strength == 0.0
    assert state.compositing_landmark_mask_strength == 0.0
    assert state.compositing_landmark_mask_profile_taper == 0.0
    assert state.compositing_skin_mask_strength == 0.0
    assert state.compositing_alpha_temporal_smoothing == 0.0
    assert state.compositing_alpha_temporal_motion_reduction == 0.0
    assert state.compositing_occlusion_edge_strength == 0.0
    assert state.compositing_occlusion_region_boost == 0.0
    assert state.compositing_occlusion_mouth_region_strength == 0.0
    assert state.compositing_occlusion_eye_region_strength == 0.0
    assert state.compositing_occlusion_region_temporal_smoothing == 0.0
    assert state.compositing_occlusion_region_temporal_motion_reduction == 0.0


def test_unknown_profile_raises_readable_error():
    with pytest.raises(ValueError, match="Unknown quality mode"):
        get_quality_profile("ultra")


@pytest.mark.parametrize(
    ("mode", "mouth_confidence", "eye_confidence"),
    [
        ("realtime", 0.0, 0.0),
        ("balanced", 0.0, 0.0),
        ("cinematic", 0.35, 0.30),
        ("experimental", 0.45, 0.40),
    ],
)
def test_profiles_wire_expression_region_confidence_thresholds(
    mode, mouth_confidence, eye_confidence
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.expression_mouth_min_confidence == mouth_confidence
    assert profile.expression_eye_min_confidence == eye_confidence
    assert state.expression_mouth_min_confidence == mouth_confidence
    assert state.expression_eye_min_confidence == eye_confidence


@pytest.mark.parametrize(
    ("mode", "process_latest"),
    [
        ("realtime", True),
        ("balanced", True),
        ("cinematic", True),
        ("experimental", False),
    ],
)
def test_profiles_wire_live_queue_freshness_policy(mode, process_latest):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.live_process_latest_frame is process_latest
    assert state.live_process_latest_frame is process_latest


@pytest.mark.parametrize(
    ("mode", "smoothing", "motion_reduction"),
    [
        ("realtime", 0.0, 0.0),
        ("balanced", 0.0, 0.0),
        ("cinematic", 0.35, 0.65),
        ("experimental", 0.45, 0.75),
    ],
)
def test_profiles_wire_mouth_mask_temporal_smoothing(
    mode,
    smoothing,
    motion_reduction,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.mouth_mask_temporal_smoothing == smoothing
    assert state.mouth_mask_temporal_smoothing == smoothing
    assert profile.mouth_mask_temporal_motion_reduction == motion_reduction
    assert state.mouth_mask_temporal_motion_reduction == motion_reduction


@pytest.mark.parametrize(
    ("mode", "confidence_weight", "reference", "min_weight"),
    [
        ("realtime", 0.0, 0.75, 0.35),
        ("balanced", 0.0, 0.75, 0.35),
        ("cinematic", 0.55, 0.78, 0.35),
        ("experimental", 0.75, 0.80, 0.30),
    ],
)
def test_profiles_wire_confidence_aware_tracking(
    mode,
    confidence_weight,
    reference,
    min_weight,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.face_tracking_confidence_weight == confidence_weight
    assert state.face_tracking_confidence_weight == confidence_weight
    assert profile.face_tracking_confidence_reference == reference
    assert state.face_tracking_confidence_reference == reference
    assert profile.face_tracking_confidence_min_weight == min_weight
    assert state.face_tracking_confidence_min_weight == min_weight


@pytest.mark.parametrize(
    ("mode", "min_confidence"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.45),
        ("experimental", 0.50),
    ],
)
def test_profiles_wire_tracking_min_detection_confidence(mode, min_confidence):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.face_tracking_min_detection_confidence == min_confidence
    assert state.face_tracking_min_detection_confidence == min_confidence


@pytest.mark.parametrize(
    ("mode", "prediction_strength", "prediction_decay"),
    [
        ("realtime", 0.0, 0.5),
        ("balanced", 0.0, 0.5),
        ("cinematic", 0.35, 0.55),
        ("experimental", 0.50, 0.65),
    ],
)
def test_profiles_wire_tracking_prediction_hold(
    mode,
    prediction_strength,
    prediction_decay,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.face_tracking_prediction_strength == prediction_strength
    assert state.face_tracking_prediction_strength == prediction_strength
    assert profile.face_tracking_prediction_decay == prediction_decay
    assert state.face_tracking_prediction_decay == prediction_decay


@pytest.mark.parametrize(
    ("mode", "enabled", "boost"),
    [
        ("realtime", False, 0.0),
        ("balanced", False, 0.0),
        ("cinematic", True, 0.22),
        ("experimental", True, 0.30),
    ],
)
def test_profiles_wire_expression_temporal_weighting(mode, enabled, boost):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.expression_temporal_smoothing is enabled
    assert state.expression_temporal_smoothing is enabled
    assert state.expression_temporal_motion_weight_boost == boost
    assert state.expression_temporal_high_motion_threshold >= (
        state.expression_temporal_motion_threshold
    )


@pytest.mark.parametrize(
    ("mode", "eye_scale"),
    [
        ("realtime", 1.0),
        ("balanced", 1.0),
        ("cinematic", 0.70),
        ("experimental", 0.85),
    ],
)
def test_profiles_wire_unilateral_eye_motion_scale(mode, eye_scale):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.expression_temporal_unilateral_eye_motion_scale == eye_scale
    assert state.expression_temporal_unilateral_eye_motion_scale == eye_scale


@pytest.mark.parametrize(
    ("mode", "smoothing", "motion_reduction"),
    [
        ("realtime", 0.0, 0.0),
        ("balanced", 0.0, 0.0),
        ("cinematic", 0.25, 0.55),
        ("experimental", 0.35, 0.65),
    ],
)
def test_profiles_wire_expression_region_landmark_stabilization(
    mode,
    smoothing,
    motion_reduction,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.expression_region_temporal_smoothing == smoothing
    assert state.expression_region_temporal_smoothing == smoothing
    assert profile.expression_region_temporal_motion_reduction == motion_reduction
    assert state.expression_region_temporal_motion_reduction == motion_reduction


@pytest.mark.parametrize(
    ("mode", "motion_reduction", "blur_reduction"),
    [
        ("realtime", 0.0, 0.0),
        ("balanced", 0.0, 0.0),
        ("cinematic", 0.35, 0.45),
        ("experimental", 0.45, 0.60),
    ],
)
def test_profiles_wire_sharpness_safety_reduction(
    mode,
    motion_reduction,
    blur_reduction,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.postprocess_sharpness_motion_reduction == motion_reduction
    assert state.postprocess_sharpness_motion_reduction == motion_reduction
    assert profile.postprocess_sharpness_blur_reduction == blur_reduction
    assert state.postprocess_sharpness_blur_reduction == blur_reduction


@pytest.mark.parametrize(
    ("mode", "lighting_strength"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.35),
        ("experimental", 0.55),
    ],
)
def test_profiles_wire_luminance_lighting_compensation(mode, lighting_strength):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_lighting_match_strength == lighting_strength
    assert state.compositing_lighting_match_strength == lighting_strength
    assert state.compositing_lighting_contrast_strength > 0.0
    assert state.compositing_lighting_max_shift > 0.0


@pytest.mark.parametrize(
    ("mode", "trim_percentile"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 4.0),
        ("experimental", 6.0),
    ],
)
def test_profiles_wire_robust_color_match_trim(mode, trim_percentile):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_color_match_trim_percentile == trim_percentile
    assert state.compositing_color_match_trim_percentile == trim_percentile


@pytest.mark.parametrize(
    ("mode", "chroma_trim_percentile"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 3.0),
        ("experimental", 5.0),
    ],
)
def test_profiles_wire_robust_color_chroma_trim(mode, chroma_trim_percentile):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_color_chroma_trim_percentile == chroma_trim_percentile
    assert state.compositing_color_chroma_trim_percentile == chroma_trim_percentile


@pytest.mark.parametrize(
    ("mode", "history_weight"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.42),
        ("experimental", 0.55),
    ],
)
def test_profiles_wire_temporal_color_statistics_smoothing(mode, history_weight):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_color_temporal_smoothing == history_weight
    assert state.compositing_color_temporal_smoothing == history_weight
    assert state.compositing_color_temporal_high_motion_threshold >= (
        state.compositing_color_temporal_motion_threshold
    )


@pytest.mark.parametrize(
    ("mode", "motion_reduction"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.55),
        ("experimental", 0.70),
    ],
)
def test_profiles_wire_temporal_color_motion_response(mode, motion_reduction):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_color_temporal_motion_reduction == motion_reduction
    assert state.compositing_color_temporal_motion_reduction == motion_reduction
    assert state.compositing_color_temporal_high_motion_threshold >= (
        state.compositing_color_temporal_motion_threshold
    )


@pytest.mark.parametrize(
    ("mode", "motion_strength"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.25),
        ("experimental", 0.40),
    ],
)
def test_profiles_wire_motion_feather_strength(mode, motion_strength):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_mask_motion_strength == motion_strength
    assert state.compositing_mask_motion_strength == motion_strength


@pytest.mark.parametrize(
    ("mode", "blur_strength"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.22),
        ("experimental", 0.35),
    ],
)
def test_profiles_wire_motion_blur_feather_strength(mode, blur_strength):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_mask_motion_blur_strength == blur_strength
    assert state.compositing_mask_motion_blur_strength == blur_strength


@pytest.mark.parametrize(
    ("mode", "profile_strength"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.20),
        ("experimental", 0.35),
    ],
)
def test_profiles_wire_profile_feather_strength(mode, profile_strength):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_mask_profile_strength == profile_strength
    assert state.compositing_mask_profile_strength == profile_strength


@pytest.mark.parametrize(
    (
        "mode",
        "edge_strength",
        "edge_threshold",
        "max_reduction",
        "min_contrast",
        "detail_strength",
        "detail_threshold",
    ),
    [
        ("realtime", 0.0, 0.45, 0.35, 32.0, 0.0, 0.14),
        ("balanced", 0.0, 0.40, 0.40, 28.0, 0.0, 0.13),
        ("cinematic", 0.18, 0.34, 0.45, 24.0, 0.18, 0.10),
        ("experimental", 0.32, 0.28, 0.60, 18.0, 0.30, 0.08),
    ],
)
def test_profiles_wire_occlusion_edge_preservation(
    mode,
    edge_strength,
    edge_threshold,
    max_reduction,
    min_contrast,
    detail_strength,
    detail_threshold,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_occlusion_edge_strength == edge_strength
    assert state.compositing_occlusion_edge_strength == edge_strength
    assert state.compositing_occlusion_edge_threshold == edge_threshold
    assert state.compositing_occlusion_edge_max_reduction == max_reduction
    assert state.compositing_occlusion_edge_blur_ratio > 0.0
    assert state.compositing_occlusion_edge_min_contrast == min_contrast
    assert profile.compositing_occlusion_detail_strength == detail_strength
    assert state.compositing_occlusion_detail_strength == detail_strength
    assert profile.compositing_occlusion_detail_threshold == detail_threshold
    assert state.compositing_occlusion_detail_threshold == detail_threshold


@pytest.mark.parametrize(
    ("mode", "boost", "mouth_strength", "eye_strength"),
    [
        ("realtime", 0.0, 0.0, 0.0),
        ("balanced", 0.0, 0.0, 0.0),
        ("cinematic", 0.55, 0.85, 0.65),
        ("experimental", 0.85, 1.0, 0.85),
    ],
)
def test_profiles_wire_expression_occlusion_priority(
    mode,
    boost,
    mouth_strength,
    eye_strength,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_occlusion_region_boost == boost
    assert state.compositing_occlusion_region_boost == boost
    assert profile.compositing_occlusion_mouth_region_strength == mouth_strength
    assert state.compositing_occlusion_mouth_region_strength == mouth_strength
    assert profile.compositing_occlusion_eye_region_strength == eye_strength
    assert state.compositing_occlusion_eye_region_strength == eye_strength
    assert state.compositing_occlusion_region_feather_ratio > 0.0


@pytest.mark.parametrize(
    ("mode", "history_weight", "motion_reduction"),
    [
        ("realtime", 0.0, 0.0),
        ("balanced", 0.0, 0.0),
        ("cinematic", 0.30, 0.60),
        ("experimental", 0.42, 0.75),
    ],
)
def test_profiles_wire_expression_occlusion_temporal_smoothing(
    mode,
    history_weight,
    motion_reduction,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_occlusion_region_temporal_smoothing == history_weight
    assert state.compositing_occlusion_region_temporal_smoothing == history_weight
    assert (
        profile.compositing_occlusion_region_temporal_motion_reduction
        == motion_reduction
    )
    assert (
        state.compositing_occlusion_region_temporal_motion_reduction
        == motion_reduction
    )


@pytest.mark.parametrize(
    ("mode", "mask_strength"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.55),
        ("experimental", 0.75),
    ],
)
def test_profiles_wire_temporal_mask_strength(mode, mask_strength):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.temporal_smoothing_mask_strength == mask_strength
    assert state.temporal_smoothing_mask_strength == mask_strength


@pytest.mark.parametrize(
    ("mode", "boost", "mouth_strength", "eye_strength"),
    [
        ("realtime", 0.0, 0.0, 0.0),
        ("balanced", 0.0, 0.0, 0.0),
        ("cinematic", 0.18, 0.80, 0.70),
        ("experimental", 0.26, 1.0, 0.90),
    ],
)
def test_profiles_wire_temporal_expression_region_response(
    mode,
    boost,
    mouth_strength,
    eye_strength,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.temporal_smoothing_expression_region_boost == boost
    assert state.temporal_smoothing_expression_region_boost == boost
    assert profile.temporal_smoothing_expression_mouth_strength == mouth_strength
    assert state.temporal_smoothing_expression_mouth_strength == mouth_strength
    assert profile.temporal_smoothing_expression_eye_strength == eye_strength
    assert state.temporal_smoothing_expression_eye_strength == eye_strength
    assert state.temporal_smoothing_expression_feather_ratio > 0.0


@pytest.mark.parametrize(
    ("mode", "profile_taper"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.20),
        ("experimental", 0.35),
    ],
)
def test_profiles_wire_profile_landmark_mask_taper(mode, profile_taper):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_landmark_mask_profile_taper == profile_taper
    assert state.compositing_landmark_mask_profile_taper == profile_taper


@pytest.mark.parametrize(
    (
        "mode",
        "skin_strength",
        "chroma_threshold",
        "max_reduction",
        "luma_threshold",
        "luma_max_reduction",
    ),
    [
        ("realtime", 0.0, 1.9, 0.30, 0.0, 0.0),
        ("balanced", 0.0, 1.9, 0.35, 0.0, 0.0),
        ("cinematic", 0.16, 1.8, 0.38, 1.45, 0.24),
        ("experimental", 0.30, 1.5, 0.52, 1.25, 0.38),
    ],
)
def test_profiles_wire_adaptive_skin_chroma_mask(
    mode,
    skin_strength,
    chroma_threshold,
    max_reduction,
    luma_threshold,
    luma_max_reduction,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_skin_mask_strength == skin_strength
    assert state.compositing_skin_mask_strength == skin_strength
    assert profile.compositing_skin_mask_chroma_threshold == chroma_threshold
    assert state.compositing_skin_mask_chroma_threshold == chroma_threshold
    assert profile.compositing_skin_mask_max_reduction == max_reduction
    assert state.compositing_skin_mask_max_reduction == max_reduction
    assert state.compositing_skin_mask_blur_ratio > 0.0
    assert profile.compositing_skin_mask_luma_threshold == luma_threshold
    assert state.compositing_skin_mask_luma_threshold == luma_threshold
    assert profile.compositing_skin_mask_luma_max_reduction == luma_max_reduction
    assert state.compositing_skin_mask_luma_max_reduction == luma_max_reduction


@pytest.mark.parametrize(
    (
        "mode",
        "strength",
        "threshold",
        "max_reduction",
        "band_ratio",
        "blur_ratio",
    ),
    [
        ("realtime", 0.0, 0.22, 0.35, 0.025, 0.010),
        ("balanced", 0.0, 0.20, 0.40, 0.030, 0.010),
        ("cinematic", 0.18, 0.16, 0.35, 0.035, 0.012),
        ("experimental", 0.32, 0.12, 0.50, 0.045, 0.016),
    ],
)
def test_profiles_wire_boundary_color_mismatch_refinement(
    mode,
    strength,
    threshold,
    max_reduction,
    band_ratio,
    blur_ratio,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_boundary_mismatch_strength == strength
    assert state.compositing_boundary_mismatch_strength == strength
    assert profile.compositing_boundary_mismatch_threshold == threshold
    assert state.compositing_boundary_mismatch_threshold == threshold
    assert profile.compositing_boundary_mismatch_max_reduction == max_reduction
    assert state.compositing_boundary_mismatch_max_reduction == max_reduction
    assert profile.compositing_boundary_mismatch_band_ratio == band_ratio
    assert state.compositing_boundary_mismatch_band_ratio == band_ratio
    assert profile.compositing_boundary_mismatch_blur_ratio == blur_ratio
    assert state.compositing_boundary_mismatch_blur_ratio == blur_ratio


@pytest.mark.parametrize(
    ("mode", "history_weight", "motion_reduction"),
    [
        ("realtime", 0.0, 0.0),
        ("balanced", 0.0, 0.0),
        ("cinematic", 0.28, 0.60),
        ("experimental", 0.38, 0.75),
    ],
)
def test_profiles_wire_temporal_alpha_smoothing(
    mode,
    history_weight,
    motion_reduction,
):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.compositing_alpha_temporal_smoothing == history_weight
    assert state.compositing_alpha_temporal_smoothing == history_weight
    assert profile.compositing_alpha_temporal_motion_reduction == motion_reduction
    assert state.compositing_alpha_temporal_motion_reduction == motion_reduction
    assert state.compositing_alpha_temporal_high_motion_threshold >= (
        state.compositing_alpha_temporal_motion_threshold
    )


@pytest.mark.parametrize(
    ("mode", "motion_boost"),
    [
        ("realtime", 0.0),
        ("balanced", 0.0),
        ("cinematic", 0.18),
        ("experimental", 0.28),
    ],
)
def test_profiles_wire_temporal_motion_response(mode, motion_boost):
    state = blank_state()

    profile = apply_quality_profile(mode, state)

    assert profile.temporal_smoothing_motion_weight_boost == motion_boost
    assert state.temporal_smoothing_motion_weight_boost == motion_boost
    assert state.temporal_smoothing_high_motion_threshold >= (
        state.temporal_smoothing_motion_threshold
    )
