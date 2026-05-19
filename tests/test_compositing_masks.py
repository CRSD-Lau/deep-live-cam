from types import SimpleNamespace

import numpy as np

from modules.compositing.masks import (
    FeatherSettings,
    create_aligned_face_alpha,
    create_expression_occlusion_mask,
    create_landmark_face_mask,
    estimate_blur_amount,
    estimate_edge_contrast,
    get_adaptive_feather_settings,
    preserve_target_edges_in_alpha,
    refine_alpha_with_boundary_color_mismatch,
    refine_alpha_with_landmark_mask,
    refine_alpha_with_skin_chroma_mask,
)


def test_create_aligned_face_alpha_has_soft_edges():
    alpha = create_aligned_face_alpha(
        64,
        FeatherSettings(erode_ratio=0.12, blur_ratio=0.06),
    )

    assert alpha.shape == (64, 64)
    assert alpha.dtype == np.uint8
    assert alpha[32, 32] == 255
    assert alpha[0, 0] < alpha[32, 32]
    assert 0 < alpha[8, 32] < 255


def test_estimate_edge_contrast_distinguishes_flat_and_textured_crops():
    flat = np.full((32, 32, 3), 120, dtype=np.uint8)
    textured = np.zeros((32, 32, 3), dtype=np.uint8)
    textured[:, ::2] = 255

    assert estimate_edge_contrast(flat) == 0.0
    assert estimate_edge_contrast(textured) > estimate_edge_contrast(flat)


def test_estimate_blur_amount_distinguishes_softened_texture_from_sharp_texture():
    sharp = np.zeros((64, 64, 3), dtype=np.uint8)
    sharp[:, ::4] = 255
    sharp[::4, :] = 255
    blurred = _gaussian_blur(sharp, kernel_size=15)

    assert estimate_blur_amount(blurred) > estimate_blur_amount(sharp)
    assert estimate_blur_amount(blurred) > 0.10


def test_estimate_blur_amount_ignores_flat_crops_and_crisp_sparse_edges():
    flat = np.full((64, 64, 3), 128, dtype=np.uint8)
    crisp_edge = np.full((64, 64, 3), 128, dtype=np.uint8)
    crisp_edge[:, 32:] = 255
    blurred_edge = _gaussian_blur(crisp_edge, kernel_size=15)

    assert estimate_blur_amount(flat) == 0.0
    assert estimate_blur_amount(blurred_edge) > estimate_blur_amount(crisp_edge)


def test_adaptive_feather_increases_blur_for_high_contrast():
    low = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        edge_contrast=0.0,
        base_blur_ratio=0.05,
    )
    high = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        edge_contrast=1.0,
        base_blur_ratio=0.05,
    )

    assert high.blur_ratio > low.blur_ratio
    assert high.erode_ratio == low.erode_ratio


def test_adaptive_feather_increases_blur_for_motion_blur():
    sharp = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        blur_amount=0.0,
        blur_strength=0.35,
    )
    blurred = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        blur_amount=1.0,
        blur_strength=0.35,
    )

    assert blurred.blur_ratio > sharp.blur_ratio
    assert blurred.erode_ratio == sharp.erode_ratio


def test_adaptive_feather_blur_strength_zero_preserves_settings():
    sharp = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        blur_amount=0.0,
        blur_strength=0.0,
    )
    blurred = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        blur_amount=1.0,
        blur_strength=0.0,
    )

    assert blurred == sharp


def test_adaptive_feather_increases_blur_for_motion():
    still = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        motion_amount=0.0,
        motion_strength=0.35,
    )
    moving = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        motion_amount=1.0,
        motion_strength=0.35,
    )

    assert moving.blur_ratio > still.blur_ratio
    assert moving.erode_ratio == still.erode_ratio


def test_adaptive_feather_increases_blur_for_side_profile():
    frontal = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        profile_amount=0.0,
        profile_strength=0.35,
    )
    profile = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        profile_amount=1.0,
        profile_strength=0.35,
    )

    assert profile.blur_ratio > frontal.blur_ratio
    assert profile.erode_ratio == frontal.erode_ratio


def test_adaptive_feather_profile_strength_zero_preserves_settings():
    frontal = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        profile_amount=0.0,
        profile_strength=0.0,
    )
    profile = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        profile_amount=1.0,
        profile_strength=0.0,
    )

    assert profile == frontal


def test_adaptive_feather_motion_strength_zero_preserves_settings():
    still = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        motion_amount=0.0,
        motion_strength=0.0,
    )
    moving = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(120, 120, 3),
        frame_shape=(720, 1280, 3),
        motion_amount=1.0,
        motion_strength=0.0,
    )

    assert moving == still


def test_adaptive_feather_responds_to_face_scale_and_cache_key():
    small = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(80, 80, 3),
        frame_shape=(1080, 1920, 3),
    )
    large = get_adaptive_feather_settings(
        face_size=128,
        crop_shape=(600, 600, 3),
        frame_shape=(1080, 1920, 3),
    )

    assert large.erode_ratio > small.erode_ratio
    assert large.blur_ratio > small.blur_ratio
    assert large.cache_key(128)[0] == 128


def test_create_landmark_face_mask_uses_face_shape():
    face = _synthetic_face()

    mask = create_landmark_face_mask(face, (96, 96, 3), dilation_ratio=0.0, feather_ratio=0.0)

    assert mask is not None
    assert mask.shape == (96, 96)
    assert mask.dtype == np.uint8
    assert mask[48, 48] == 255
    assert mask[5, 5] == 0


def test_create_landmark_face_mask_tapers_far_side_for_profile_faces():
    face = _synthetic_profile_face(nose_x=68.0)

    frontal = create_landmark_face_mask(
        face,
        (96, 96, 3),
        dilation_ratio=0.0,
        feather_ratio=0.0,
        forehead_ratio=0.0,
        profile_amount=0.0,
        profile_taper_ratio=0.0,
    )
    tapered = create_landmark_face_mask(
        face,
        (96, 96, 3),
        dilation_ratio=0.0,
        feather_ratio=0.0,
        forehead_ratio=0.0,
        profile_amount=1.0,
        profile_taper_ratio=0.55,
    )

    assert frontal is not None
    assert tapered is not None
    assert tapered[50, 32] < frontal[50, 32]
    assert tapered[50, 58] == frontal[50, 58]


def test_refine_alpha_with_landmark_mask_constrains_crop():
    face = _synthetic_face()
    alpha = np.full((96, 96), 255, dtype=np.uint8)

    refined = refine_alpha_with_landmark_mask(
        alpha,
        face,
        (96, 96, 3),
        (0, 0, 96, 96),
        strength=1.0,
        dilation_ratio=0.0,
        feather_ratio=0.0,
    )

    assert refined[48, 48] == 255
    assert refined[5, 5] == 0
    assert alpha[5, 5] == 255


def test_refine_alpha_with_landmark_mask_bypasses_missing_landmarks():
    alpha = np.full((8, 8), 123, dtype=np.uint8)

    refined = refine_alpha_with_landmark_mask(
        alpha,
        SimpleNamespace(bbox=np.array([1, 1, 6, 6], dtype=np.float32)),
        (8, 8, 3),
        (0, 0, 8, 8),
        strength=1.0,
    )

    np.testing.assert_array_equal(refined, alpha)


def test_refine_alpha_with_skin_chroma_mask_reduces_chroma_outliers():
    alpha = np.full((40, 40), 220, dtype=np.uint8)
    target = np.full((40, 40, 3), [82, 132, 176], dtype=np.uint8)
    target[:, 28:] = [210, 36, 42]

    refined = refine_alpha_with_skin_chroma_mask(
        alpha,
        target,
        strength=1.0,
        chroma_threshold=1.1,
        max_reduction=0.60,
        blur_ratio=0.0,
    )

    assert refined.dtype == np.uint8
    assert refined[:, 30:36].mean() < alpha[:, 30:36].mean()
    assert refined[:, 4:18].mean() > refined[:, 30:36].mean()


def test_refine_alpha_with_skin_chroma_mask_reduces_luma_outliers():
    alpha = np.full((40, 40), 220, dtype=np.uint8)
    target = np.full((40, 40, 3), [128, 128, 128], dtype=np.uint8)
    target[:, 28:] = [36, 36, 36]

    chroma_only = refine_alpha_with_skin_chroma_mask(
        alpha,
        target,
        strength=1.0,
        chroma_threshold=1.1,
        max_reduction=0.60,
        blur_ratio=0.0,
        luma_threshold=0.0,
        luma_max_reduction=0.0,
    )
    luma_refined = refine_alpha_with_skin_chroma_mask(
        alpha,
        target,
        strength=1.0,
        chroma_threshold=1.1,
        max_reduction=0.60,
        blur_ratio=0.0,
        luma_threshold=1.0,
        luma_max_reduction=0.55,
    )

    np.testing.assert_array_equal(chroma_only, alpha)
    assert luma_refined[:, 30:36].mean() < alpha[:, 30:36].mean()
    assert luma_refined[:, 4:18].mean() > luma_refined[:, 30:36].mean()


def test_refine_alpha_with_skin_chroma_mask_zero_strength_preserves_alpha():
    alpha = np.full((12, 12), 0.75, dtype=np.float32)
    target = np.full((12, 12, 3), 128, dtype=np.uint8)
    target[:, 8:] = [255, 0, 0]

    refined = refine_alpha_with_skin_chroma_mask(alpha, target, strength=0.0)

    np.testing.assert_array_equal(refined, alpha)


def test_refine_alpha_with_skin_chroma_mask_bypasses_invalid_inputs():
    alpha = np.full((8, 8), 155, dtype=np.uint8)
    mismatched = np.full((7, 8, 3), 255, dtype=np.uint8)
    grayscale = np.full((8, 8), 128, dtype=np.uint8)

    np.testing.assert_array_equal(
        refine_alpha_with_skin_chroma_mask(alpha, mismatched, strength=1.0),
        alpha,
    )
    np.testing.assert_array_equal(
        refine_alpha_with_skin_chroma_mask(alpha, grayscale, strength=1.0),
        alpha,
    )


def test_refine_alpha_with_boundary_color_mismatch_reduces_boundary_alpha_only():
    alpha = np.zeros((40, 40), dtype=np.uint8)
    alpha[10:30, 10:30] = 220
    source = np.full((40, 40, 3), [32, 40, 220], dtype=np.uint8)
    target = np.full((40, 40, 3), [160, 160, 160], dtype=np.uint8)

    refined = refine_alpha_with_boundary_color_mismatch(
        alpha,
        source,
        target,
        strength=1.0,
        color_threshold=0.01,
        max_reduction=0.50,
        band_ratio=0.08,
        blur_ratio=0.0,
    )

    assert refined.dtype == np.uint8
    assert refined[10:13, 20].mean() < alpha[10:13, 20].mean()
    assert refined[20, 20] == alpha[20, 20]
    assert refined[0, 0] == alpha[0, 0]


def test_refine_alpha_with_boundary_color_mismatch_preserves_low_mismatch_alpha():
    alpha = np.zeros((40, 40), dtype=np.uint8)
    alpha[10:30, 10:30] = 220
    target = np.full((40, 40, 3), [128, 128, 128], dtype=np.uint8)

    refined = refine_alpha_with_boundary_color_mismatch(
        alpha,
        target.copy(),
        target,
        strength=1.0,
        color_threshold=0.05,
        max_reduction=0.50,
        band_ratio=0.08,
        blur_ratio=0.0,
    )

    np.testing.assert_array_equal(refined, alpha)


def test_refine_alpha_with_boundary_color_mismatch_zero_strength_preserves_alpha():
    alpha = np.full((12, 12), 0.75, dtype=np.float32)
    source = np.full((12, 12, 3), [0, 0, 255], dtype=np.uint8)
    target = np.full((12, 12, 3), [128, 128, 128], dtype=np.uint8)

    refined = refine_alpha_with_boundary_color_mismatch(
        alpha,
        source,
        target,
        strength=0.0,
    )

    np.testing.assert_array_equal(refined, alpha)


def test_preserve_target_edges_reduces_alpha_on_strong_occluder_edges():
    alpha = np.full((40, 40), 220, dtype=np.uint8)
    target = np.full((40, 40, 3), 128, dtype=np.uint8)
    target[:, 20:22] = 0

    refined = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.10,
        max_reduction=0.50,
        blur_ratio=0.06,
    )

    assert refined.dtype == np.uint8
    assert refined[:, 20:22].mean() < alpha[:, 20:22].mean()
    assert refined[:, 2:6].mean() > refined[:, 20:22].mean()


def test_expression_occlusion_mask_weights_mouth_and_eyes():
    face = _synthetic_expression_face()

    mask = create_expression_occlusion_mask(
        face,
        (100, 100, 3),
        (20, 20, 80, 80),
        mouth_strength=1.0,
        eye_strength=0.55,
        feather_ratio=0.0,
        padding_ratio=0.20,
    )

    assert mask is not None
    assert mask.shape == (60, 60)
    assert mask.dtype == np.uint8
    assert mask[45, 30] > 220
    assert 110 <= mask[22, 18] <= 150
    assert mask[6, 6] == 0


def test_expression_occlusion_mask_honors_confidence_gates():
    face = _synthetic_expression_face()

    mask = create_expression_occlusion_mask(
        face,
        (100, 100, 3),
        (20, 20, 80, 80),
        mouth_strength=1.0,
        eye_strength=1.0,
        feather_ratio=0.0,
        mouth_min_confidence=1.1,
        eye_min_confidence=1.1,
    )

    assert mask is None


def test_preserve_target_edges_priority_mask_boosts_expression_regions():
    alpha = np.full((40, 40), 220, dtype=np.uint8)
    target = np.full((40, 40, 3), 128, dtype=np.uint8)
    target[:, 5:7] = 0
    target[:, 20:22] = 188
    priority = np.zeros((40, 40), dtype=np.uint8)
    priority[12:28, 18:24] = 255

    baseline = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.62,
        max_reduction=0.50,
        blur_ratio=0.0,
        min_contrast=0.0,
    )
    boosted = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.62,
        max_reduction=0.50,
        blur_ratio=0.0,
        min_contrast=0.0,
        priority_mask=priority,
        priority_strength=1.0,
    )

    assert boosted[12:28, 19:23].mean() < baseline[12:28, 19:23].mean()
    np.testing.assert_array_equal(boosted[:6, :6], baseline[:6, :6])


def test_preserve_target_edges_detail_score_preserves_thin_structure_interiors():
    alpha = np.full((48, 48), 220, dtype=np.uint8)
    target = np.full((48, 48, 3), 172, dtype=np.uint8)
    target[:, 23:26] = 16

    baseline = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.98,
        max_reduction=0.55,
        blur_ratio=0.0,
        min_contrast=0.0,
        detail_strength=0.0,
    )
    detailed = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.98,
        max_reduction=0.55,
        blur_ratio=0.0,
        min_contrast=0.0,
        detail_strength=1.0,
        detail_threshold=0.05,
    )

    assert detailed[:, 24].mean() < baseline[:, 24].mean()
    assert detailed[:, 4:10].mean() == baseline[:, 4:10].mean()


def test_preserve_target_edges_zero_strength_preserves_alpha():
    alpha = np.full((16, 16), 177, dtype=np.uint8)
    target = np.zeros((16, 16, 3), dtype=np.uint8)
    target[8:] = 255

    refined = preserve_target_edges_in_alpha(alpha, target, strength=0.0)

    np.testing.assert_array_equal(refined, alpha)


def test_preserve_target_edges_bypasses_flat_target():
    alpha = np.full((16, 16), 201, dtype=np.uint8)
    target = np.full((16, 16, 3), 90, dtype=np.uint8)

    refined = preserve_target_edges_in_alpha(alpha, target, strength=1.0)

    np.testing.assert_array_equal(refined, alpha)


def test_preserve_target_edges_bypasses_low_contrast_texture():
    alpha = np.full((32, 32), 190, dtype=np.uint8)
    target = np.full((32, 32, 3), 128, dtype=np.uint8)
    target[:, ::2] = 131

    refined = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.0,
        max_reduction=0.75,
    )

    np.testing.assert_array_equal(refined, alpha)


def test_preserve_target_edges_min_contrast_is_tunable():
    alpha = np.full((32, 32), 190, dtype=np.uint8)
    target = np.full((32, 32, 3), 128, dtype=np.uint8)
    target[:, 16:] = 136

    conservative = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.0,
        max_reduction=0.75,
        min_contrast=64.0,
    )
    sensitive = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.0,
        max_reduction=0.75,
        min_contrast=0.0,
    )

    np.testing.assert_array_equal(conservative, alpha)
    assert sensitive[:, 15:17].mean() < alpha[:, 15:17].mean()


def test_preserve_target_edges_bypasses_invalid_inputs():
    alpha = np.full((8, 8), 155, dtype=np.uint8)
    mismatched = np.full((7, 8, 3), 255, dtype=np.uint8)
    object_target = np.full((8, 8, 3), 255, dtype=object)
    nonfinite_target = np.full((8, 8, 3), 0.5, dtype=np.float32)
    nonfinite_target[0, 0, 0] = np.nan

    np.testing.assert_array_equal(
        preserve_target_edges_in_alpha(alpha, mismatched, strength=1.0),
        alpha,
    )
    np.testing.assert_array_equal(
        preserve_target_edges_in_alpha(alpha, object_target, strength=1.0),
        alpha,
    )
    np.testing.assert_array_equal(
        preserve_target_edges_in_alpha(alpha, nonfinite_target, strength=1.0),
        alpha,
    )


def test_preserve_target_edges_accepts_four_channel_targets_and_float_alpha():
    alpha = np.full((24, 24), 0.8, dtype=np.float32)
    target = np.full((24, 24, 4), 0.5, dtype=np.float32)
    target[:, 12:14, :3] = 0.0

    refined = preserve_target_edges_in_alpha(
        alpha,
        target,
        strength=1.0,
        edge_threshold=0.10,
        max_reduction=0.50,
    )

    assert refined.dtype == np.float32
    assert refined[:, 12:14].mean() < alpha[:, 12:14].mean()
    assert refined[:, 2:6].mean() > refined[:, 12:14].mean()


def _synthetic_face():
    angles = np.linspace(0, 2 * np.pi, 106, endpoint=False)
    landmarks = np.column_stack([
        48.0 + np.cos(angles) * 22.0,
        50.0 + np.sin(angles) * 28.0,
    ]).astype(np.float32)
    return SimpleNamespace(
        bbox=np.array([26.0, 22.0, 70.0, 78.0], dtype=np.float32),
        landmark_2d_106=landmarks,
    )


def _synthetic_expression_face():
    face = _synthetic_face()
    landmarks = face.landmark_2d_106.copy()

    mouth_angles = np.linspace(0, 2 * np.pi, 20, endpoint=False)
    landmarks[list(range(52, 72))] = np.column_stack(
        [
            50.0 + np.cos(mouth_angles) * 12.0,
            65.0 + np.sin(mouth_angles) * 5.0,
        ]
    )

    right_eye_angles = np.linspace(0, 2 * np.pi, 9, endpoint=False)
    landmarks[list(range(33, 42))] = np.column_stack(
        [
            38.0 + np.cos(right_eye_angles) * 6.0,
            42.0 + np.sin(right_eye_angles) * 2.5,
        ]
    )
    landmarks[list(range(43, 51))] = np.column_stack(
        [
            np.linspace(32.0, 44.0, 8),
            np.full(8, 36.0),
        ]
    )

    left_eye_angles = np.linspace(0, 2 * np.pi, 9, endpoint=False)
    landmarks[list(range(87, 96))] = np.column_stack(
        [
            62.0 + np.cos(left_eye_angles) * 6.0,
            42.0 + np.sin(left_eye_angles) * 2.5,
        ]
    )
    landmarks[list(range(97, 105))] = np.column_stack(
        [
            np.linspace(56.0, 68.0, 8),
            np.full(8, 36.0),
        ]
    )

    face.landmark_2d_106 = landmarks.astype(np.float32)
    return face


def _synthetic_profile_face(nose_x: float):
    face = _synthetic_face()
    face.kps = np.array(
        [
            [36.0, 40.0],
            [60.0, 40.0],
            [nose_x, 54.0],
            [40.0, 68.0],
            [58.0, 68.0],
        ],
        dtype=np.float32,
    )
    return face


def _gaussian_blur(image: np.ndarray, *, kernel_size: int) -> np.ndarray:
    import cv2

    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
