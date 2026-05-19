from types import SimpleNamespace

import numpy as np
import pytest

from modules.diagnostics.overlays import (
    DEFAULT_OVERLAY_LAYERS,
    draw_diagnostic_overlay,
    parse_overlay_layers,
)


def test_parse_overlay_layers_defaults_and_deduplicates():
    assert parse_overlay_layers(None) == list(DEFAULT_OVERLAY_LAYERS)
    assert parse_overlay_layers("bbox, kps,bbox") == ["bbox", "kps"]
    assert "mask" in parse_overlay_layers("all")
    assert "mouth" in parse_overlay_layers("all")
    assert "eyes" in parse_overlay_layers("all")


def test_parse_overlay_layers_rejects_invalid_values():
    for value in (" ", "bbox,,kps", "unknown"):
        with pytest.raises(ValueError):
            parse_overlay_layers(value)


def test_draw_diagnostic_overlay_draws_bbox_kps_and_profile_without_mutating_input():
    frame = np.zeros((80, 100, 3), dtype=np.uint8)
    face = SimpleNamespace(
        bbox=np.array([20, 15, 60, 55], dtype=np.float32),
        kps=np.array([[25, 20], [55, 20], [40, 35], [28, 48], [52, 48]], dtype=np.float32),
        det_score=0.95,
        tracking_id=7,
    )

    result = draw_diagnostic_overlay(
        frame,
        [face],
        layers=["bbox", "kps", "profile"],
        profile_name="cinematic",
    )

    assert result.shape == frame.shape
    assert result.dtype == np.uint8
    assert result.sum() > 0
    assert frame.sum() == 0


def test_draw_diagnostic_overlay_blends_mask_layer():
    frame = np.zeros((20, 20, 3), dtype=np.uint8)
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[5:15, 5:15] = 255

    result = draw_diagnostic_overlay(
        frame,
        [],
        layers=["mask"],
        masks=[mask],
    )

    assert result[10, 10, 1] > 0
    assert result[0, 0].sum() == 0


def test_draw_diagnostic_overlay_skips_missing_landmarks():
    frame = np.zeros((40, 40, 3), dtype=np.uint8)
    face = SimpleNamespace(bbox=np.array([5, 5, 20, 20], dtype=np.float32))

    result = draw_diagnostic_overlay(
        frame,
        [face],
        layers=["landmarks"],
    )

    np.testing.assert_array_equal(result, frame)


def test_draw_diagnostic_overlay_draws_mouth_and_eye_layers_for_mapping_faces():
    frame = np.zeros((120, 140, 3), dtype=np.uint8)
    face = {
        "bbox": np.array([20.0, 20.0, 120.0, 110.0], dtype=np.float32),
        "landmark_2d_106": _landmarks_with_expression_regions(),
        "tracking_id": 12,
        "det_score": 0.91,
    }

    result = draw_diagnostic_overlay(
        frame,
        [face],
        layers=["mouth", "eyes", "bbox"],
        profile_name="cinematic",
    )

    assert result.shape == frame.shape
    assert result.sum() > 0
    assert result[82, 80].sum() > 0
    assert result[45, 52].sum() > 0
    assert result[45, 90].sum() > 0


def _region_points(count, center, width, height):
    angles = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    return np.column_stack(
        [
            center[0] + np.cos(angles) * width / 2.0,
            center[1] + np.sin(angles) * height / 2.0,
        ]
    ).astype(np.float32)


def _landmarks_with_expression_regions():
    landmarks = np.zeros((106, 2), dtype=np.float32)
    landmarks[52:72] = _region_points(20, center=(60.0, 82.0), width=40.0, height=12.0)
    landmarks[33:42] = _region_points(9, center=(42.0, 45.0), width=20.0, height=4.0)
    landmarks[87:96] = _region_points(9, center=(78.0, 45.0), width=24.0, height=6.0)
    return landmarks
