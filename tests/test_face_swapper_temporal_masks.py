import numpy as np

import modules.globals
from modules.processors.frame import face_swapper


def test_apply_post_processing_passes_landmark_masks_to_temporal_blend(monkeypatch):
    captured = {}
    mask = np.full((12, 12), 255, dtype=np.uint8)
    face = {
        "bbox": np.array([3.0, 3.0, 9.0, 9.0], dtype=np.float32),
        "landmark_2d_106": np.zeros((106, 2), dtype=np.float32),
    }

    monkeypatch.setattr(modules.globals, "sharpness", 0.0)
    monkeypatch.setattr(modules.globals, "enable_interpolation", True)
    monkeypatch.setattr(modules.globals, "interpolation_weight", 0.5)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_region_expansion", 0.0)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_feather_ratio", 0.0)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_mask_strength", 0.7)
    monkeypatch.setattr(
        modules.globals,
        "temporal_smoothing_expression_region_boost",
        0.0,
    )
    monkeypatch.setattr(modules.globals, "expression_temporal_smoothing", False)
    monkeypatch.setattr(modules.globals, "diagnostic_overlay", False)
    def fake_landmark_mask(observed_face, _shape, **_kwargs):
        captured["face"] = observed_face
        return mask

    monkeypatch.setattr(face_swapper, "create_landmark_face_mask", fake_landmark_mask)

    def fake_blend(previous_frame, current_frame, bboxes, **kwargs):
        captured["previous"] = previous_frame
        captured["bboxes"] = bboxes
        captured["masks"] = kwargs["masks"]
        captured["mask_strength"] = kwargs["mask_strength"]
        return current_frame

    monkeypatch.setattr(face_swapper, "blend_frame_regions", fake_blend)

    previous = np.zeros((12, 12, 3), dtype=np.uint8)
    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    monkeypatch.setattr(face_swapper, "PREVIOUS_FRAME_RESULT", previous)

    result = face_swapper.apply_post_processing(
        current,
        [np.array([3, 3, 9, 9])],
        [face],
    )

    np.testing.assert_array_equal(result, current)
    assert captured["face"] is face
    assert captured["masks"] == [mask]
    assert captured["mask_strength"] == 0.7
    np.testing.assert_array_equal(captured["bboxes"][0], [3, 3, 9, 9])


def test_temporal_smoothing_masks_bypasses_when_strength_disabled(monkeypatch):
    monkeypatch.setattr(modules.globals, "temporal_smoothing_mask_strength", 0.0)

    assert (
        face_swapper._temporal_smoothing_masks(
            [{"landmark_2d_106": np.zeros((106, 2), dtype=np.float32)}],
            np.zeros((12, 12, 3), dtype=np.uint8),
        )
        is None
    )


def test_temporal_expression_response_masks_passes_region_controls(monkeypatch):
    captured = {}
    response_mask = np.full((12, 12), 255, dtype=np.uint8)
    face = {"landmark_2d_106": np.zeros((106, 2), dtype=np.float32)}

    def fake_expression_mask(observed_face, frame_shape, crop_bounds, **kwargs):
        captured["face"] = observed_face
        captured["frame_shape"] = frame_shape
        captured["crop_bounds"] = crop_bounds
        captured.update(kwargs)
        return response_mask

    monkeypatch.setattr(
        face_swapper,
        "create_expression_occlusion_mask",
        fake_expression_mask,
    )
    monkeypatch.setattr(
        modules.globals,
        "temporal_smoothing_expression_region_boost",
        0.18,
    )
    monkeypatch.setattr(
        modules.globals,
        "temporal_smoothing_expression_mouth_strength",
        0.8,
    )
    monkeypatch.setattr(
        modules.globals,
        "temporal_smoothing_expression_eye_strength",
        0.7,
    )
    monkeypatch.setattr(
        modules.globals,
        "temporal_smoothing_expression_feather_ratio",
        0.021,
    )
    monkeypatch.setattr(modules.globals, "expression_mouth_min_confidence", 0.35)
    monkeypatch.setattr(modules.globals, "expression_eye_min_confidence", 0.30)

    masks = face_swapper._temporal_expression_response_masks(
        [face],
        np.zeros((12, 12, 3), dtype=np.uint8),
    )

    assert masks == [response_mask]
    assert captured["face"] is face
    assert captured["frame_shape"] == (12, 12, 3)
    assert captured["crop_bounds"] == (0, 0, 12, 12)
    assert captured["mouth_strength"] == 0.8
    assert captured["eye_strength"] == 0.7
    assert captured["feather_ratio"] == 0.021
    assert captured["mouth_min_confidence"] == 0.35
    assert captured["eye_min_confidence"] == 0.30


def test_temporal_expression_response_masks_bypasses_when_boost_disabled(
    monkeypatch,
):
    monkeypatch.setattr(
        modules.globals,
        "temporal_smoothing_expression_region_boost",
        0.0,
    )

    assert (
        face_swapper._temporal_expression_response_masks(
            [{"landmark_2d_106": np.zeros((106, 2), dtype=np.float32)}],
            np.zeros((12, 12, 3), dtype=np.uint8),
        )
        is None
    )


def test_apply_post_processing_passes_expression_response_masks_to_temporal_blend(
    monkeypatch,
):
    captured = {}
    response_mask = np.full((12, 12), 255, dtype=np.uint8)
    face = {"landmark_2d_106": np.zeros((106, 2), dtype=np.float32)}

    monkeypatch.setattr(modules.globals, "sharpness", 0.0)
    monkeypatch.setattr(modules.globals, "enable_interpolation", True)
    monkeypatch.setattr(modules.globals, "interpolation_weight", 0.5)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_region_expansion", 0.0)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_feather_ratio", 0.0)
    monkeypatch.setattr(modules.globals, "temporal_smoothing_mask_strength", 0.0)
    monkeypatch.setattr(
        modules.globals,
        "temporal_smoothing_expression_region_boost",
        0.22,
    )
    monkeypatch.setattr(modules.globals, "expression_temporal_smoothing", False)
    monkeypatch.setattr(modules.globals, "diagnostic_overlay", False)
    def fake_response_masks(observed_faces, _frame):
        captured["response_faces"] = observed_faces
        return [response_mask]

    monkeypatch.setattr(
        face_swapper,
        "_temporal_expression_response_masks",
        fake_response_masks,
    )

    def fake_blend(previous_frame, current_frame, bboxes, **kwargs):
        captured["previous"] = previous_frame
        captured["bboxes"] = bboxes
        captured["local_masks"] = kwargs["local_current_weight_masks"]
        captured["local_boost"] = kwargs["local_current_weight_boost"]
        return current_frame

    monkeypatch.setattr(face_swapper, "blend_frame_regions", fake_blend)
    monkeypatch.setattr(
        face_swapper,
        "PREVIOUS_FRAME_RESULT",
        np.zeros((12, 12, 3), dtype=np.uint8),
    )

    current = np.full((12, 12, 3), 100, dtype=np.uint8)
    result = face_swapper.apply_post_processing(
        current,
        [np.array([3, 3, 9, 9])],
        [face],
    )

    np.testing.assert_array_equal(result, current)
    assert captured["response_faces"] == [face]
    assert captured["local_masks"] == [response_mask]
    assert captured["local_boost"] == 0.22
