"""Quality/performance presets for the live render pipeline."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Mapping

from modules.enhancement_registry import ENHANCER_KEYS, get_enhancer_profile


@dataclass(frozen=True)
class QualityProfile:
    name: str
    label: str
    description: str
    enhancer: str | None
    live_process_latest_frame: bool
    live_detection_interval_ratio: float
    enable_interpolation: bool
    interpolation_weight: float
    temporal_smoothing_region_expansion: float
    temporal_smoothing_feather_ratio: float
    temporal_smoothing_mask_strength: float
    temporal_smoothing_motion_threshold: float
    temporal_smoothing_high_motion_threshold: float
    temporal_smoothing_motion_weight_boost: float
    temporal_smoothing_expression_region_boost: float
    temporal_smoothing_expression_mouth_strength: float
    temporal_smoothing_expression_eye_strength: float
    temporal_smoothing_expression_feather_ratio: float
    sharpness: float
    postprocess_sharpness_motion_reduction: float
    postprocess_sharpness_blur_reduction: float
    mouth_mask_size: float
    expression_mouth_min_confidence: float
    expression_eye_min_confidence: float
    mouth_mask_temporal_smoothing: float
    mouth_mask_temporal_motion_reduction: float
    expression_temporal_smoothing: bool
    expression_temporal_stable_weight_multiplier: float
    expression_temporal_motion_threshold: float
    expression_temporal_high_motion_threshold: float
    expression_temporal_motion_weight_boost: float
    expression_temporal_unilateral_eye_motion_scale: float
    expression_region_temporal_smoothing: float
    expression_region_temporal_motion_reduction: float
    poisson_blend: bool
    face_tracking_enabled: bool
    face_tracking_current_weight: float
    face_tracking_reset_ratio: float
    face_tracking_max_missed: int
    face_tracking_confidence_weight: float
    face_tracking_confidence_reference: float
    face_tracking_confidence_min_weight: float
    face_tracking_min_detection_confidence: float
    face_tracking_prediction_strength: float
    face_tracking_prediction_decay: float
    compositing_color_match_strength: float
    compositing_color_match_trim_percentile: float
    compositing_color_chroma_trim_percentile: float
    compositing_color_temporal_smoothing: float
    compositing_color_temporal_motion_threshold: float
    compositing_color_temporal_high_motion_threshold: float
    compositing_color_temporal_motion_reduction: float
    compositing_lighting_match_strength: float
    compositing_lighting_contrast_strength: float
    compositing_lighting_max_shift: float
    compositing_mask_erode_ratio: float
    compositing_mask_blur_ratio: float
    compositing_mask_scale_strength: float
    compositing_mask_edge_strength: float
    compositing_mask_motion_blur_strength: float
    compositing_mask_motion_strength: float
    compositing_mask_profile_strength: float
    compositing_landmark_mask_strength: float
    compositing_landmark_mask_dilation_ratio: float
    compositing_landmark_mask_feather_ratio: float
    compositing_landmark_mask_profile_taper: float
    compositing_skin_mask_strength: float
    compositing_skin_mask_chroma_threshold: float
    compositing_skin_mask_max_reduction: float
    compositing_skin_mask_blur_ratio: float
    compositing_skin_mask_luma_threshold: float
    compositing_skin_mask_luma_max_reduction: float
    compositing_boundary_mismatch_strength: float
    compositing_boundary_mismatch_threshold: float
    compositing_boundary_mismatch_max_reduction: float
    compositing_boundary_mismatch_band_ratio: float
    compositing_boundary_mismatch_blur_ratio: float
    compositing_alpha_temporal_smoothing: float
    compositing_alpha_temporal_motion_threshold: float
    compositing_alpha_temporal_high_motion_threshold: float
    compositing_alpha_temporal_motion_reduction: float
    compositing_occlusion_edge_strength: float
    compositing_occlusion_edge_threshold: float
    compositing_occlusion_edge_max_reduction: float
    compositing_occlusion_edge_blur_ratio: float
    compositing_occlusion_edge_min_contrast: float
    compositing_occlusion_detail_strength: float
    compositing_occlusion_detail_threshold: float
    compositing_occlusion_region_boost: float
    compositing_occlusion_mouth_region_strength: float
    compositing_occlusion_eye_region_strength: float
    compositing_occlusion_region_feather_ratio: float
    compositing_occlusion_region_temporal_smoothing: float
    compositing_occlusion_region_temporal_motion_reduction: float


QUALITY_PROFILES: dict[str, QualityProfile] = {
    "realtime": QualityProfile(
        name="realtime",
        label="Realtime",
        description="Lowest latency; no enhancer and fewer detector refreshes.",
        enhancer=None,
        live_process_latest_frame=True,
        live_detection_interval_ratio=0.12,
        enable_interpolation=False,
        interpolation_weight=0.0,
        temporal_smoothing_region_expansion=0.12,
        temporal_smoothing_feather_ratio=0.12,
        temporal_smoothing_mask_strength=0.0,
        temporal_smoothing_motion_threshold=0.12,
        temporal_smoothing_high_motion_threshold=0.45,
        temporal_smoothing_motion_weight_boost=0.0,
        temporal_smoothing_expression_region_boost=0.0,
        temporal_smoothing_expression_mouth_strength=0.0,
        temporal_smoothing_expression_eye_strength=0.0,
        temporal_smoothing_expression_feather_ratio=0.014,
        sharpness=0.0,
        postprocess_sharpness_motion_reduction=0.0,
        postprocess_sharpness_blur_reduction=0.0,
        mouth_mask_size=0.0,
        expression_mouth_min_confidence=0.0,
        expression_eye_min_confidence=0.0,
        mouth_mask_temporal_smoothing=0.0,
        mouth_mask_temporal_motion_reduction=0.0,
        expression_temporal_smoothing=False,
        expression_temporal_stable_weight_multiplier=1.0,
        expression_temporal_motion_threshold=0.06,
        expression_temporal_high_motion_threshold=0.14,
        expression_temporal_motion_weight_boost=0.0,
        expression_temporal_unilateral_eye_motion_scale=1.0,
        expression_region_temporal_smoothing=0.0,
        expression_region_temporal_motion_reduction=0.0,
        poisson_blend=False,
        face_tracking_enabled=False,
        face_tracking_current_weight=1.0,
        face_tracking_reset_ratio=1.2,
        face_tracking_max_missed=0,
        face_tracking_confidence_weight=0.0,
        face_tracking_confidence_reference=0.75,
        face_tracking_confidence_min_weight=0.35,
        face_tracking_min_detection_confidence=0.0,
        face_tracking_prediction_strength=0.0,
        face_tracking_prediction_decay=0.5,
        compositing_color_match_strength=0.0,
        compositing_color_match_trim_percentile=0.0,
        compositing_color_chroma_trim_percentile=0.0,
        compositing_color_temporal_smoothing=0.0,
        compositing_color_temporal_motion_threshold=0.12,
        compositing_color_temporal_high_motion_threshold=0.45,
        compositing_color_temporal_motion_reduction=0.0,
        compositing_lighting_match_strength=0.0,
        compositing_lighting_contrast_strength=0.20,
        compositing_lighting_max_shift=8.0,
        compositing_mask_erode_ratio=0.09,
        compositing_mask_blur_ratio=0.04,
        compositing_mask_scale_strength=0.15,
        compositing_mask_edge_strength=0.0,
        compositing_mask_motion_blur_strength=0.0,
        compositing_mask_motion_strength=0.0,
        compositing_mask_profile_strength=0.0,
        compositing_landmark_mask_strength=0.0,
        compositing_landmark_mask_dilation_ratio=0.018,
        compositing_landmark_mask_feather_ratio=0.012,
        compositing_landmark_mask_profile_taper=0.0,
        compositing_skin_mask_strength=0.0,
        compositing_skin_mask_chroma_threshold=1.9,
        compositing_skin_mask_max_reduction=0.30,
        compositing_skin_mask_blur_ratio=0.010,
        compositing_skin_mask_luma_threshold=0.0,
        compositing_skin_mask_luma_max_reduction=0.0,
        compositing_boundary_mismatch_strength=0.0,
        compositing_boundary_mismatch_threshold=0.22,
        compositing_boundary_mismatch_max_reduction=0.35,
        compositing_boundary_mismatch_band_ratio=0.025,
        compositing_boundary_mismatch_blur_ratio=0.010,
        compositing_alpha_temporal_smoothing=0.0,
        compositing_alpha_temporal_motion_threshold=0.12,
        compositing_alpha_temporal_high_motion_threshold=0.45,
        compositing_alpha_temporal_motion_reduction=0.0,
        compositing_occlusion_edge_strength=0.0,
        compositing_occlusion_edge_threshold=0.45,
        compositing_occlusion_edge_max_reduction=0.35,
        compositing_occlusion_edge_blur_ratio=0.010,
        compositing_occlusion_edge_min_contrast=32.0,
        compositing_occlusion_detail_strength=0.0,
        compositing_occlusion_detail_threshold=0.14,
        compositing_occlusion_region_boost=0.0,
        compositing_occlusion_mouth_region_strength=0.0,
        compositing_occlusion_eye_region_strength=0.0,
        compositing_occlusion_region_feather_ratio=0.014,
        compositing_occlusion_region_temporal_smoothing=0.0,
        compositing_occlusion_region_temporal_motion_reduction=0.0,
    ),
    "balanced": QualityProfile(
        name="balanced",
        label="Balanced",
        description="Preserves the stock behavior with conservative live cadence.",
        enhancer=None,
        live_process_latest_frame=True,
        live_detection_interval_ratio=0.08,
        enable_interpolation=True,
        interpolation_weight=0.0,
        temporal_smoothing_region_expansion=0.16,
        temporal_smoothing_feather_ratio=0.16,
        temporal_smoothing_mask_strength=0.0,
        temporal_smoothing_motion_threshold=0.10,
        temporal_smoothing_high_motion_threshold=0.40,
        temporal_smoothing_motion_weight_boost=0.0,
        temporal_smoothing_expression_region_boost=0.0,
        temporal_smoothing_expression_mouth_strength=0.0,
        temporal_smoothing_expression_eye_strength=0.0,
        temporal_smoothing_expression_feather_ratio=0.016,
        sharpness=0.0,
        postprocess_sharpness_motion_reduction=0.0,
        postprocess_sharpness_blur_reduction=0.0,
        mouth_mask_size=0.0,
        expression_mouth_min_confidence=0.0,
        expression_eye_min_confidence=0.0,
        mouth_mask_temporal_smoothing=0.0,
        mouth_mask_temporal_motion_reduction=0.0,
        expression_temporal_smoothing=False,
        expression_temporal_stable_weight_multiplier=1.0,
        expression_temporal_motion_threshold=0.05,
        expression_temporal_high_motion_threshold=0.12,
        expression_temporal_motion_weight_boost=0.0,
        expression_temporal_unilateral_eye_motion_scale=1.0,
        expression_region_temporal_smoothing=0.0,
        expression_region_temporal_motion_reduction=0.0,
        poisson_blend=False,
        face_tracking_enabled=True,
        face_tracking_current_weight=0.7,
        face_tracking_reset_ratio=1.2,
        face_tracking_max_missed=1,
        face_tracking_confidence_weight=0.0,
        face_tracking_confidence_reference=0.75,
        face_tracking_confidence_min_weight=0.35,
        face_tracking_min_detection_confidence=0.0,
        face_tracking_prediction_strength=0.0,
        face_tracking_prediction_decay=0.5,
        compositing_color_match_strength=0.0,
        compositing_color_match_trim_percentile=0.0,
        compositing_color_chroma_trim_percentile=0.0,
        compositing_color_temporal_smoothing=0.0,
        compositing_color_temporal_motion_threshold=0.10,
        compositing_color_temporal_high_motion_threshold=0.40,
        compositing_color_temporal_motion_reduction=0.0,
        compositing_lighting_match_strength=0.0,
        compositing_lighting_contrast_strength=0.25,
        compositing_lighting_max_shift=10.0,
        compositing_mask_erode_ratio=0.10,
        compositing_mask_blur_ratio=0.05,
        compositing_mask_scale_strength=0.25,
        compositing_mask_edge_strength=0.18,
        compositing_mask_motion_blur_strength=0.0,
        compositing_mask_motion_strength=0.0,
        compositing_mask_profile_strength=0.0,
        compositing_landmark_mask_strength=0.0,
        compositing_landmark_mask_dilation_ratio=0.022,
        compositing_landmark_mask_feather_ratio=0.016,
        compositing_landmark_mask_profile_taper=0.0,
        compositing_skin_mask_strength=0.0,
        compositing_skin_mask_chroma_threshold=1.9,
        compositing_skin_mask_max_reduction=0.35,
        compositing_skin_mask_blur_ratio=0.012,
        compositing_skin_mask_luma_threshold=0.0,
        compositing_skin_mask_luma_max_reduction=0.0,
        compositing_boundary_mismatch_strength=0.0,
        compositing_boundary_mismatch_threshold=0.20,
        compositing_boundary_mismatch_max_reduction=0.40,
        compositing_boundary_mismatch_band_ratio=0.030,
        compositing_boundary_mismatch_blur_ratio=0.010,
        compositing_alpha_temporal_smoothing=0.0,
        compositing_alpha_temporal_motion_threshold=0.10,
        compositing_alpha_temporal_high_motion_threshold=0.40,
        compositing_alpha_temporal_motion_reduction=0.0,
        compositing_occlusion_edge_strength=0.0,
        compositing_occlusion_edge_threshold=0.40,
        compositing_occlusion_edge_max_reduction=0.40,
        compositing_occlusion_edge_blur_ratio=0.012,
        compositing_occlusion_edge_min_contrast=28.0,
        compositing_occlusion_detail_strength=0.0,
        compositing_occlusion_detail_threshold=0.13,
        compositing_occlusion_region_boost=0.0,
        compositing_occlusion_mouth_region_strength=0.0,
        compositing_occlusion_eye_region_strength=0.0,
        compositing_occlusion_region_feather_ratio=0.016,
        compositing_occlusion_region_temporal_smoothing=0.0,
        compositing_occlusion_region_temporal_motion_reduction=0.0,
    ),
    "cinematic": QualityProfile(
        name="cinematic",
        label="Cinematic",
        description="Higher quality face restoration and softer temporal motion.",
        enhancer="face_enhancer_gpen512",
        live_process_latest_frame=True,
        live_detection_interval_ratio=0.05,
        enable_interpolation=True,
        interpolation_weight=0.35,
        temporal_smoothing_region_expansion=0.22,
        temporal_smoothing_feather_ratio=0.20,
        temporal_smoothing_mask_strength=0.55,
        temporal_smoothing_motion_threshold=0.08,
        temporal_smoothing_high_motion_threshold=0.35,
        temporal_smoothing_motion_weight_boost=0.18,
        temporal_smoothing_expression_region_boost=0.18,
        temporal_smoothing_expression_mouth_strength=0.80,
        temporal_smoothing_expression_eye_strength=0.70,
        temporal_smoothing_expression_feather_ratio=0.018,
        sharpness=0.3,
        postprocess_sharpness_motion_reduction=0.35,
        postprocess_sharpness_blur_reduction=0.45,
        mouth_mask_size=22.0,
        expression_mouth_min_confidence=0.35,
        expression_eye_min_confidence=0.30,
        mouth_mask_temporal_smoothing=0.35,
        mouth_mask_temporal_motion_reduction=0.65,
        expression_temporal_smoothing=True,
        expression_temporal_stable_weight_multiplier=0.86,
        expression_temporal_motion_threshold=0.035,
        expression_temporal_high_motion_threshold=0.09,
        expression_temporal_motion_weight_boost=0.22,
        expression_temporal_unilateral_eye_motion_scale=0.70,
        expression_region_temporal_smoothing=0.25,
        expression_region_temporal_motion_reduction=0.55,
        poisson_blend=False,
        face_tracking_enabled=True,
        face_tracking_current_weight=0.45,
        face_tracking_reset_ratio=1.0,
        face_tracking_max_missed=2,
        face_tracking_confidence_weight=0.55,
        face_tracking_confidence_reference=0.78,
        face_tracking_confidence_min_weight=0.35,
        face_tracking_min_detection_confidence=0.45,
        face_tracking_prediction_strength=0.35,
        face_tracking_prediction_decay=0.55,
        compositing_color_match_strength=0.6,
        compositing_color_match_trim_percentile=4.0,
        compositing_color_chroma_trim_percentile=3.0,
        compositing_color_temporal_smoothing=0.42,
        compositing_color_temporal_motion_threshold=0.08,
        compositing_color_temporal_high_motion_threshold=0.35,
        compositing_color_temporal_motion_reduction=0.55,
        compositing_lighting_match_strength=0.35,
        compositing_lighting_contrast_strength=0.35,
        compositing_lighting_max_shift=12.0,
        compositing_mask_erode_ratio=0.11,
        compositing_mask_blur_ratio=0.06,
        compositing_mask_scale_strength=0.40,
        compositing_mask_edge_strength=0.35,
        compositing_mask_motion_blur_strength=0.22,
        compositing_mask_motion_strength=0.25,
        compositing_mask_profile_strength=0.20,
        compositing_landmark_mask_strength=0.55,
        compositing_landmark_mask_dilation_ratio=0.026,
        compositing_landmark_mask_feather_ratio=0.020,
        compositing_landmark_mask_profile_taper=0.20,
        compositing_skin_mask_strength=0.16,
        compositing_skin_mask_chroma_threshold=1.8,
        compositing_skin_mask_max_reduction=0.38,
        compositing_skin_mask_blur_ratio=0.014,
        compositing_skin_mask_luma_threshold=1.45,
        compositing_skin_mask_luma_max_reduction=0.24,
        compositing_boundary_mismatch_strength=0.18,
        compositing_boundary_mismatch_threshold=0.16,
        compositing_boundary_mismatch_max_reduction=0.35,
        compositing_boundary_mismatch_band_ratio=0.035,
        compositing_boundary_mismatch_blur_ratio=0.012,
        compositing_alpha_temporal_smoothing=0.28,
        compositing_alpha_temporal_motion_threshold=0.08,
        compositing_alpha_temporal_high_motion_threshold=0.35,
        compositing_alpha_temporal_motion_reduction=0.60,
        compositing_occlusion_edge_strength=0.18,
        compositing_occlusion_edge_threshold=0.34,
        compositing_occlusion_edge_max_reduction=0.45,
        compositing_occlusion_edge_blur_ratio=0.014,
        compositing_occlusion_edge_min_contrast=24.0,
        compositing_occlusion_detail_strength=0.18,
        compositing_occlusion_detail_threshold=0.10,
        compositing_occlusion_region_boost=0.55,
        compositing_occlusion_mouth_region_strength=0.85,
        compositing_occlusion_eye_region_strength=0.65,
        compositing_occlusion_region_feather_ratio=0.018,
        compositing_occlusion_region_temporal_smoothing=0.30,
        compositing_occlusion_region_temporal_motion_reduction=0.60,
    ),
    "experimental": QualityProfile(
        name="experimental",
        label="Experimental",
        description="Most aggressive quality settings; useful for offline trials.",
        enhancer="face_enhancer",
        live_process_latest_frame=False,
        live_detection_interval_ratio=0.04,
        enable_interpolation=True,
        interpolation_weight=0.25,
        temporal_smoothing_region_expansion=0.28,
        temporal_smoothing_feather_ratio=0.24,
        temporal_smoothing_mask_strength=0.75,
        temporal_smoothing_motion_threshold=0.06,
        temporal_smoothing_high_motion_threshold=0.30,
        temporal_smoothing_motion_weight_boost=0.28,
        temporal_smoothing_expression_region_boost=0.26,
        temporal_smoothing_expression_mouth_strength=1.0,
        temporal_smoothing_expression_eye_strength=0.90,
        temporal_smoothing_expression_feather_ratio=0.022,
        sharpness=0.5,
        postprocess_sharpness_motion_reduction=0.45,
        postprocess_sharpness_blur_reduction=0.60,
        mouth_mask_size=35.0,
        expression_mouth_min_confidence=0.45,
        expression_eye_min_confidence=0.40,
        mouth_mask_temporal_smoothing=0.45,
        mouth_mask_temporal_motion_reduction=0.75,
        expression_temporal_smoothing=True,
        expression_temporal_stable_weight_multiplier=0.80,
        expression_temporal_motion_threshold=0.025,
        expression_temporal_high_motion_threshold=0.075,
        expression_temporal_motion_weight_boost=0.30,
        expression_temporal_unilateral_eye_motion_scale=0.85,
        expression_region_temporal_smoothing=0.35,
        expression_region_temporal_motion_reduction=0.65,
        poisson_blend=True,
        face_tracking_enabled=True,
        face_tracking_current_weight=0.35,
        face_tracking_reset_ratio=0.9,
        face_tracking_max_missed=3,
        face_tracking_confidence_weight=0.75,
        face_tracking_confidence_reference=0.80,
        face_tracking_confidence_min_weight=0.30,
        face_tracking_min_detection_confidence=0.50,
        face_tracking_prediction_strength=0.50,
        face_tracking_prediction_decay=0.65,
        compositing_color_match_strength=0.8,
        compositing_color_match_trim_percentile=6.0,
        compositing_color_chroma_trim_percentile=5.0,
        compositing_color_temporal_smoothing=0.55,
        compositing_color_temporal_motion_threshold=0.06,
        compositing_color_temporal_high_motion_threshold=0.30,
        compositing_color_temporal_motion_reduction=0.70,
        compositing_lighting_match_strength=0.55,
        compositing_lighting_contrast_strength=0.45,
        compositing_lighting_max_shift=14.0,
        compositing_mask_erode_ratio=0.12,
        compositing_mask_blur_ratio=0.07,
        compositing_mask_scale_strength=0.50,
        compositing_mask_edge_strength=0.50,
        compositing_mask_motion_blur_strength=0.35,
        compositing_mask_motion_strength=0.40,
        compositing_mask_profile_strength=0.35,
        compositing_landmark_mask_strength=0.75,
        compositing_landmark_mask_dilation_ratio=0.030,
        compositing_landmark_mask_feather_ratio=0.024,
        compositing_landmark_mask_profile_taper=0.35,
        compositing_skin_mask_strength=0.30,
        compositing_skin_mask_chroma_threshold=1.5,
        compositing_skin_mask_max_reduction=0.52,
        compositing_skin_mask_blur_ratio=0.018,
        compositing_skin_mask_luma_threshold=1.25,
        compositing_skin_mask_luma_max_reduction=0.38,
        compositing_boundary_mismatch_strength=0.32,
        compositing_boundary_mismatch_threshold=0.12,
        compositing_boundary_mismatch_max_reduction=0.50,
        compositing_boundary_mismatch_band_ratio=0.045,
        compositing_boundary_mismatch_blur_ratio=0.016,
        compositing_alpha_temporal_smoothing=0.38,
        compositing_alpha_temporal_motion_threshold=0.06,
        compositing_alpha_temporal_high_motion_threshold=0.30,
        compositing_alpha_temporal_motion_reduction=0.75,
        compositing_occlusion_edge_strength=0.32,
        compositing_occlusion_edge_threshold=0.28,
        compositing_occlusion_edge_max_reduction=0.60,
        compositing_occlusion_edge_blur_ratio=0.018,
        compositing_occlusion_edge_min_contrast=18.0,
        compositing_occlusion_detail_strength=0.30,
        compositing_occlusion_detail_threshold=0.08,
        compositing_occlusion_region_boost=0.85,
        compositing_occlusion_mouth_region_strength=1.0,
        compositing_occlusion_eye_region_strength=0.85,
        compositing_occlusion_region_feather_ratio=0.022,
        compositing_occlusion_region_temporal_smoothing=0.42,
        compositing_occlusion_region_temporal_motion_reduction=0.75,
    ),
}

QUALITY_MODE_NAMES = tuple(QUALITY_PROFILES.keys())
QUALITY_PROFILE_METADATA_FIELDS = frozenset(
    {
        "name",
        "label",
        "description",
        "enhancer",
    }
)
QUALITY_PROFILE_RUNTIME_FIELDS = tuple(
    field.name
    for field in fields(QualityProfile)
    if field.name not in QUALITY_PROFILE_METADATA_FIELDS
)


def get_quality_profile(name: str) -> QualityProfile:
    try:
        return QUALITY_PROFILES[name]
    except KeyError as exc:
        choices = ", ".join(QUALITY_MODE_NAMES)
        raise ValueError(f"Unknown quality mode '{name}'. Choose one of: {choices}.") from exc


def quality_profile_runtime_state(source_globals: Any) -> dict[str, Any]:
    """Capture persisted quality-profile runtime knobs from a globals-like object."""
    return {
        field_name: getattr(source_globals, field_name)
        for field_name in QUALITY_PROFILE_RUNTIME_FIELDS
        if hasattr(source_globals, field_name)
    }


def restore_quality_profile_runtime_state(
    target_globals: Any,
    state: Mapping[str, Any],
) -> None:
    """Restore persisted quality-profile runtime knobs onto a globals-like object."""
    for field_name in QUALITY_PROFILE_RUNTIME_FIELDS:
        if field_name in state:
            setattr(target_globals, field_name, state[field_name])


def apply_quality_profile(name: str, target_globals: Any) -> QualityProfile:
    """Apply a quality profile to a globals-like module/object.

    Only quality-related runtime knobs are changed. Paths, execution providers,
    and frame processor ordering are intentionally left alone.
    """
    profile = get_quality_profile(name)
    if profile.enhancer is not None:
        get_enhancer_profile(profile.enhancer)
    target_globals.quality_mode = profile.name
    restore_quality_profile_runtime_state(
        target_globals,
        quality_profile_runtime_state(profile),
    )
    target_globals.live_process_latest_frame = profile.live_process_latest_frame
    target_globals.live_detection_interval_ratio = profile.live_detection_interval_ratio
    target_globals.enable_interpolation = profile.enable_interpolation
    target_globals.interpolation_weight = profile.interpolation_weight
    target_globals.temporal_smoothing_region_expansion = (
        profile.temporal_smoothing_region_expansion
    )
    target_globals.temporal_smoothing_feather_ratio = (
        profile.temporal_smoothing_feather_ratio
    )
    target_globals.temporal_smoothing_mask_strength = (
        profile.temporal_smoothing_mask_strength
    )
    target_globals.temporal_smoothing_motion_threshold = (
        profile.temporal_smoothing_motion_threshold
    )
    target_globals.temporal_smoothing_high_motion_threshold = (
        profile.temporal_smoothing_high_motion_threshold
    )
    target_globals.temporal_smoothing_motion_weight_boost = (
        profile.temporal_smoothing_motion_weight_boost
    )
    target_globals.temporal_smoothing_expression_region_boost = (
        profile.temporal_smoothing_expression_region_boost
    )
    target_globals.temporal_smoothing_expression_mouth_strength = (
        profile.temporal_smoothing_expression_mouth_strength
    )
    target_globals.temporal_smoothing_expression_eye_strength = (
        profile.temporal_smoothing_expression_eye_strength
    )
    target_globals.temporal_smoothing_expression_feather_ratio = (
        profile.temporal_smoothing_expression_feather_ratio
    )
    target_globals.sharpness = profile.sharpness
    target_globals.postprocess_sharpness_motion_reduction = (
        profile.postprocess_sharpness_motion_reduction
    )
    target_globals.postprocess_sharpness_blur_reduction = (
        profile.postprocess_sharpness_blur_reduction
    )
    target_globals.mouth_mask_size = profile.mouth_mask_size
    target_globals.mouth_mask = profile.mouth_mask_size > 0
    target_globals.expression_mouth_min_confidence = (
        profile.expression_mouth_min_confidence
    )
    target_globals.expression_eye_min_confidence = profile.expression_eye_min_confidence
    target_globals.mouth_mask_temporal_smoothing = (
        profile.mouth_mask_temporal_smoothing
    )
    target_globals.mouth_mask_temporal_motion_reduction = (
        profile.mouth_mask_temporal_motion_reduction
    )
    target_globals.expression_temporal_smoothing = profile.expression_temporal_smoothing
    target_globals.expression_temporal_stable_weight_multiplier = (
        profile.expression_temporal_stable_weight_multiplier
    )
    target_globals.expression_temporal_motion_threshold = (
        profile.expression_temporal_motion_threshold
    )
    target_globals.expression_temporal_high_motion_threshold = (
        profile.expression_temporal_high_motion_threshold
    )
    target_globals.expression_temporal_motion_weight_boost = (
        profile.expression_temporal_motion_weight_boost
    )
    target_globals.expression_temporal_unilateral_eye_motion_scale = (
        profile.expression_temporal_unilateral_eye_motion_scale
    )
    target_globals.poisson_blend = profile.poisson_blend
    target_globals.face_tracking_enabled = profile.face_tracking_enabled
    target_globals.face_tracking_current_weight = profile.face_tracking_current_weight
    target_globals.face_tracking_reset_ratio = profile.face_tracking_reset_ratio
    target_globals.face_tracking_max_missed = profile.face_tracking_max_missed
    target_globals.face_tracking_confidence_weight = (
        profile.face_tracking_confidence_weight
    )
    target_globals.face_tracking_confidence_reference = (
        profile.face_tracking_confidence_reference
    )
    target_globals.face_tracking_confidence_min_weight = (
        profile.face_tracking_confidence_min_weight
    )
    target_globals.face_tracking_min_detection_confidence = (
        profile.face_tracking_min_detection_confidence
    )
    target_globals.compositing_color_match_strength = (
        profile.compositing_color_match_strength
    )
    target_globals.compositing_color_match_trim_percentile = (
        profile.compositing_color_match_trim_percentile
    )
    target_globals.compositing_color_chroma_trim_percentile = (
        profile.compositing_color_chroma_trim_percentile
    )
    target_globals.compositing_color_temporal_smoothing = (
        profile.compositing_color_temporal_smoothing
    )
    target_globals.compositing_color_temporal_motion_threshold = (
        profile.compositing_color_temporal_motion_threshold
    )
    target_globals.compositing_color_temporal_high_motion_threshold = (
        profile.compositing_color_temporal_high_motion_threshold
    )
    target_globals.compositing_color_temporal_motion_reduction = (
        profile.compositing_color_temporal_motion_reduction
    )
    target_globals.compositing_lighting_match_strength = (
        profile.compositing_lighting_match_strength
    )
    target_globals.compositing_lighting_contrast_strength = (
        profile.compositing_lighting_contrast_strength
    )
    target_globals.compositing_lighting_max_shift = (
        profile.compositing_lighting_max_shift
    )
    target_globals.compositing_mask_erode_ratio = profile.compositing_mask_erode_ratio
    target_globals.compositing_mask_blur_ratio = profile.compositing_mask_blur_ratio
    target_globals.compositing_mask_scale_strength = (
        profile.compositing_mask_scale_strength
    )
    target_globals.compositing_mask_edge_strength = (
        profile.compositing_mask_edge_strength
    )
    target_globals.compositing_mask_motion_blur_strength = (
        profile.compositing_mask_motion_blur_strength
    )
    target_globals.compositing_mask_motion_strength = (
        profile.compositing_mask_motion_strength
    )
    target_globals.compositing_mask_profile_strength = (
        profile.compositing_mask_profile_strength
    )
    target_globals.compositing_landmark_mask_strength = (
        profile.compositing_landmark_mask_strength
    )
    target_globals.compositing_landmark_mask_dilation_ratio = (
        profile.compositing_landmark_mask_dilation_ratio
    )
    target_globals.compositing_landmark_mask_feather_ratio = (
        profile.compositing_landmark_mask_feather_ratio
    )
    target_globals.compositing_landmark_mask_profile_taper = (
        profile.compositing_landmark_mask_profile_taper
    )
    target_globals.compositing_skin_mask_strength = (
        profile.compositing_skin_mask_strength
    )
    target_globals.compositing_skin_mask_chroma_threshold = (
        profile.compositing_skin_mask_chroma_threshold
    )
    target_globals.compositing_skin_mask_max_reduction = (
        profile.compositing_skin_mask_max_reduction
    )
    target_globals.compositing_skin_mask_blur_ratio = (
        profile.compositing_skin_mask_blur_ratio
    )
    target_globals.compositing_skin_mask_luma_threshold = (
        profile.compositing_skin_mask_luma_threshold
    )
    target_globals.compositing_skin_mask_luma_max_reduction = (
        profile.compositing_skin_mask_luma_max_reduction
    )
    target_globals.compositing_alpha_temporal_smoothing = (
        profile.compositing_alpha_temporal_smoothing
    )
    target_globals.compositing_alpha_temporal_motion_threshold = (
        profile.compositing_alpha_temporal_motion_threshold
    )
    target_globals.compositing_alpha_temporal_high_motion_threshold = (
        profile.compositing_alpha_temporal_high_motion_threshold
    )
    target_globals.compositing_alpha_temporal_motion_reduction = (
        profile.compositing_alpha_temporal_motion_reduction
    )
    target_globals.compositing_occlusion_edge_strength = (
        profile.compositing_occlusion_edge_strength
    )
    target_globals.compositing_occlusion_edge_threshold = (
        profile.compositing_occlusion_edge_threshold
    )
    target_globals.compositing_occlusion_edge_max_reduction = (
        profile.compositing_occlusion_edge_max_reduction
    )
    target_globals.compositing_occlusion_edge_blur_ratio = (
        profile.compositing_occlusion_edge_blur_ratio
    )
    target_globals.compositing_occlusion_edge_min_contrast = (
        profile.compositing_occlusion_edge_min_contrast
    )
    target_globals.compositing_occlusion_detail_strength = (
        profile.compositing_occlusion_detail_strength
    )
    target_globals.compositing_occlusion_detail_threshold = (
        profile.compositing_occlusion_detail_threshold
    )
    target_globals.compositing_occlusion_region_boost = (
        profile.compositing_occlusion_region_boost
    )
    target_globals.compositing_occlusion_mouth_region_strength = (
        profile.compositing_occlusion_mouth_region_strength
    )
    target_globals.compositing_occlusion_eye_region_strength = (
        profile.compositing_occlusion_eye_region_strength
    )
    target_globals.compositing_occlusion_region_feather_ratio = (
        profile.compositing_occlusion_region_feather_ratio
    )
    target_globals.compositing_occlusion_region_temporal_smoothing = (
        profile.compositing_occlusion_region_temporal_smoothing
    )
    target_globals.compositing_occlusion_region_temporal_motion_reduction = (
        profile.compositing_occlusion_region_temporal_motion_reduction
    )

    fp_ui = dict(getattr(target_globals, "fp_ui", {}))
    for enhancer_key in ENHANCER_KEYS:
        fp_ui[enhancer_key] = enhancer_key == profile.enhancer
    target_globals.fp_ui = fp_ui
    return profile
