import numpy as np

from modules.expression_regions import LEFT_EYE_INDICES, MOUTH_OUTER_INDICES
from modules.expression_stabilizer import blend_expression_region_landmarks


def test_blend_expression_region_landmarks_only_blends_selected_regions():
    previous = np.zeros((106, 2), dtype=np.float32)
    current = np.full((106, 2), 10.0, dtype=np.float32)

    blended = blend_expression_region_landmarks(
        previous,
        current,
        history_weight=0.25,
        indices=MOUTH_OUTER_INDICES,
    )

    np.testing.assert_allclose(blended[list(MOUTH_OUTER_INDICES)], 7.5)
    np.testing.assert_allclose(blended[0], [10.0, 10.0])


def test_blend_expression_region_landmarks_supports_multiple_regions():
    previous = np.zeros((106, 2), dtype=np.float32)
    current = np.full((106, 2), 20.0, dtype=np.float32)

    blended = blend_expression_region_landmarks(
        previous,
        current,
        history_weight=0.5,
        indices=MOUTH_OUTER_INDICES + LEFT_EYE_INDICES,
    )

    np.testing.assert_allclose(blended[list(MOUTH_OUTER_INDICES)], 10.0)
    np.testing.assert_allclose(blended[list(LEFT_EYE_INDICES)], 10.0)
    np.testing.assert_allclose(blended[0], [20.0, 20.0])


def test_blend_expression_region_landmarks_bypasses_invalid_previous_shape():
    previous = np.zeros((5, 2), dtype=np.float32)
    current = np.full((106, 2), 10.0, dtype=np.float32)

    blended = blend_expression_region_landmarks(
        previous,
        current,
        history_weight=0.8,
        indices=MOUTH_OUTER_INDICES,
    )

    np.testing.assert_allclose(blended, current)
