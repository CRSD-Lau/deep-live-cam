import numpy as np

from modules.temporal_smoothing import blend_frame_regions


def test_blend_frame_regions_changes_only_selected_region():
    previous = np.full((12, 12, 3), 20, dtype=np.uint8)
    current = np.full((12, 12, 3), 100, dtype=np.uint8)

    result = blend_frame_regions(
        previous,
        current,
        [np.array([4, 4, 8, 8])],
        current_weight=0.5,
        expansion_ratio=0.0,
        feather_ratio=0.0,
        min_feather=0,
    )

    assert result[0, 0, 0] == 100
    assert result[5, 5, 0] == 60
    assert result[9, 9, 0] == 100
    assert current[5, 5, 0] == 100


def test_blend_frame_regions_feathers_edges():
    previous = np.zeros((24, 24, 3), dtype=np.uint8)
    current = np.full((24, 24, 3), 100, dtype=np.uint8)

    result = blend_frame_regions(
        previous,
        current,
        [[4, 4, 20, 20]],
        current_weight=0.5,
        expansion_ratio=0.0,
        feather_ratio=0.25,
        min_feather=3,
    )

    center_delta = int(current[12, 12, 0]) - int(result[12, 12, 0])
    corner_delta = int(current[4, 4, 0]) - int(result[4, 4, 0])

    assert center_delta > 25
    assert corner_delta < center_delta


def test_blend_frame_regions_ignores_invalid_history_or_regions():
    current = np.full((10, 10, 3), 100, dtype=np.uint8)
    wrong_shape_previous = np.full((8, 10, 3), 20, dtype=np.uint8)
    previous = np.full((10, 10, 3), 20, dtype=np.uint8)

    np.testing.assert_array_equal(
        blend_frame_regions(
            wrong_shape_previous,
            current,
            [[2, 2, 8, 8]],
            current_weight=0.5,
        ),
        current,
    )
    np.testing.assert_array_equal(
        blend_frame_regions(
            previous,
            current,
            [[2, 2, 2, 8], [np.nan, 0, 4, 4]],
            current_weight=0.5,
        ),
        current,
    )


def test_blend_frame_regions_expands_bbox():
    previous = np.full((20, 20, 3), 0, dtype=np.uint8)
    current = np.full((20, 20, 3), 100, dtype=np.uint8)

    result = blend_frame_regions(
        previous,
        current,
        [[8, 8, 12, 12]],
        current_weight=0.5,
        expansion_ratio=0.5,
        feather_ratio=0.0,
        min_feather=0,
    )

    assert result[7, 7, 0] == 50
    assert result[5, 5, 0] == 100


def test_blend_frame_regions_constrains_history_with_face_mask():
    previous = np.zeros((12, 12, 3), dtype=np.uint8)
    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    face_mask = np.zeros((12, 12), dtype=np.uint8)
    face_mask[5:7, 5:7] = 255

    result = blend_frame_regions(
        previous,
        current,
        [[3, 3, 9, 9]],
        current_weight=0.5,
        expansion_ratio=0.0,
        feather_ratio=0.0,
        masks=[face_mask],
        mask_strength=1.0,
        min_feather=0,
    )

    assert result[5, 5, 0] == 50
    assert result[3, 3, 0] == 100


def test_blend_frame_regions_mask_strength_zero_preserves_bbox_behavior():
    previous = np.zeros((12, 12, 3), dtype=np.uint8)
    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    face_mask = np.zeros((12, 12), dtype=np.uint8)

    result = blend_frame_regions(
        previous,
        current,
        [[3, 3, 9, 9]],
        current_weight=0.5,
        expansion_ratio=0.0,
        feather_ratio=0.0,
        masks=[face_mask],
        mask_strength=0.0,
        min_feather=0,
    )

    assert result[3, 3, 0] == 50
    assert result[5, 5, 0] == 50


def test_blend_frame_regions_boosts_current_weight_inside_local_mask():
    previous = np.zeros((12, 12, 3), dtype=np.uint8)
    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    expression_mask = np.zeros((12, 12), dtype=np.uint8)
    expression_mask[5:7, 5:7] = 255

    result = blend_frame_regions(
        previous,
        current,
        [[3, 3, 9, 9]],
        current_weight=0.3,
        expansion_ratio=0.0,
        feather_ratio=0.0,
        local_current_weight_masks=[expression_mask],
        local_current_weight_boost=0.4,
        min_feather=0,
    )

    assert result[4, 4, 0] == 30
    assert result[5, 5, 0] == 70
    assert result[0, 0, 0] == 100


def test_blend_frame_regions_local_weight_boost_is_mask_limited_when_clamped():
    previous = np.zeros((12, 12, 3), dtype=np.uint8)
    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    expression_mask = np.zeros((12, 12), dtype=np.uint8)
    expression_mask[5:7, 5:7] = 255

    result = blend_frame_regions(
        previous,
        current,
        [[3, 3, 9, 9]],
        current_weight=0.8,
        expansion_ratio=0.0,
        feather_ratio=0.0,
        local_current_weight_masks=[expression_mask],
        local_current_weight_boost=0.6,
        min_feather=0,
    )

    assert result[4, 4, 0] == 80
    assert result[5, 5, 0] == 100


def test_blend_frame_regions_ignores_invalid_local_weight_masks():
    previous = np.zeros((12, 12, 3), dtype=np.uint8)
    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    invalid_mask = np.full((8, 8), 255, dtype=np.uint8)

    result = blend_frame_regions(
        previous,
        current,
        [[3, 3, 9, 9]],
        current_weight=0.3,
        expansion_ratio=0.0,
        feather_ratio=0.0,
        local_current_weight_masks=[invalid_mask],
        local_current_weight_boost=0.4,
        min_feather=0,
    )

    assert result[5, 5, 0] == 30
