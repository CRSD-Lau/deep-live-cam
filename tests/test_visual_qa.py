import json

import cv2
import numpy as np
import pytest

from modules.utilities import read_image

from modules.visual_qa import (
    TemporalQACaptureSession,
    VisualQACaptureSession,
    compute_image_metrics,
    compute_temporal_consistency_metrics,
    create_difference_heatmap,
    create_edge_difference_heatmap,
    create_edge_map,
    create_side_by_side,
    create_temporal_edge_jitter_heatmap,
    create_temporal_flicker_heatmap,
    export_temporal_qa,
    export_visual_qa,
    parse_frame_selection,
)


def test_compute_image_metrics_reports_zero_for_identical_images():
    image = np.full((4, 5, 3), 80, dtype=np.uint8)

    metrics = compute_image_metrics(image, image.copy())

    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["max_abs_diff"] == 0
    assert metrics["before_shape"] == [4, 5, 3]
    assert metrics["after_shape"] == [4, 5, 3]
    assert metrics["p95_abs_diff"] == 0.0
    assert metrics["p99_abs_diff"] == 0.0
    assert metrics["changed_pixel_ratio_5"] == 0.0
    assert metrics["changed_pixel_ratio_15"] == 0.0
    assert metrics["luma_mae"] == 0.0
    assert metrics["chroma_mae"] == 0.0
    assert metrics["edge_mae"] == 0.0


def test_compute_image_metrics_reports_luma_chroma_edge_and_local_change():
    before = np.zeros((8, 8, 3), dtype=np.uint8)
    after = before.copy()
    after[:, 4:] = [0, 0, 80]
    after[2:6, 2:6, 1] = 180

    metrics = compute_image_metrics(before, after)

    assert metrics["mae"] > 0.0
    assert metrics["p95_abs_diff"] > 0.0
    assert metrics["p99_abs_diff"] >= metrics["p95_abs_diff"]
    assert 0.0 < metrics["changed_pixel_ratio_5"] <= 1.0
    assert metrics["changed_pixel_ratio_5"] >= metrics["changed_pixel_ratio_15"]
    assert metrics["luma_mae"] > 0.0
    assert metrics["chroma_mae"] > 0.0
    assert metrics["edge_mae"] > 0.0


def test_compute_temporal_consistency_metrics_reports_sequence_flicker():
    frame_0 = np.zeros((8, 8, 3), dtype=np.uint8)
    frame_1 = frame_0.copy()
    frame_1[:, 4:] = 40
    frame_2 = frame_1.copy()
    frame_2[2:6, 2:6, 1] = 120

    metrics = compute_temporal_consistency_metrics([frame_0, frame_1, frame_2])

    assert metrics["frame_count"] == 3
    assert metrics["pair_count"] == 2
    assert metrics["frame_shape"] == [8, 8, 3]
    assert metrics["mean_pair_mae"] > 0.0
    assert metrics["p95_pair_mae"] >= metrics["mean_pair_mae"]
    assert metrics["mean_luma_mae"] > 0.0
    assert metrics["mean_edge_mae"] > 0.0
    assert len(metrics["pairs"]) == 2
    assert metrics["pairs"][0]["from_frame"] == 0
    assert metrics["pairs"][1]["to_frame"] == 2


def test_compute_temporal_consistency_metrics_handles_short_sequences():
    metrics = compute_temporal_consistency_metrics(
        [np.zeros((4, 5, 3), dtype=np.uint8)]
    )

    assert metrics["frame_count"] == 1
    assert metrics["pair_count"] == 0
    assert metrics["mean_pair_mae"] == 0.0
    assert metrics["pairs"] == []


def test_side_by_side_resizes_to_common_height():
    before = np.full((12, 8, 3), 20, dtype=np.uint8)
    after = np.full((6, 4, 3), 200, dtype=np.uint8)

    panel = create_side_by_side(before, after, label_height=0, separator_width=2)

    assert panel.shape == (12, 18, 3)
    assert panel.dtype == np.uint8
    np.testing.assert_array_equal(panel[:, 8:10], np.full((12, 2, 3), 18, dtype=np.uint8))


def test_difference_heatmap_has_input_dimensions():
    before = np.zeros((10, 20, 3), dtype=np.uint8)
    after = np.full((5, 10, 3), 255, dtype=np.uint8)

    heatmap = create_difference_heatmap(before, after)

    assert heatmap.shape == before.shape
    assert heatmap.dtype == np.uint8
    assert heatmap.mean() > 0


def test_edge_map_highlights_edges_without_changing_dimensions():
    image = np.zeros((12, 16, 3), dtype=np.uint8)
    image[:, 8:] = 255

    edge_map = create_edge_map(image)

    assert edge_map.shape == image.shape
    assert edge_map.dtype == np.uint8
    assert edge_map[:, 7:9].mean() > edge_map[:, :3].mean()


def test_edge_difference_heatmap_tracks_edge_changes():
    before = np.zeros((12, 16, 3), dtype=np.uint8)
    after = before.copy()
    after[:, 8:] = 255

    heatmap = create_edge_difference_heatmap(before, after)

    assert heatmap.shape == before.shape
    assert heatmap.dtype == np.uint8
    assert heatmap[:, 7:9].mean() > heatmap[:, :3].mean()


def test_temporal_heatmaps_track_flicker_and_edge_jitter():
    frame_0 = np.zeros((12, 16, 3), dtype=np.uint8)
    frame_1 = frame_0.copy()
    frame_1[:, 8:] = 255
    frame_2 = frame_0.copy()
    frame_2[:, 7:] = 255

    flicker = create_temporal_flicker_heatmap([frame_0, frame_1, frame_2])
    edge_jitter = create_temporal_edge_jitter_heatmap([frame_0, frame_1, frame_2])

    flicker_gray = cv2.cvtColor(flicker, cv2.COLOR_BGR2GRAY)
    edge_gray = cv2.cvtColor(edge_jitter, cv2.COLOR_BGR2GRAY)
    assert flicker.shape == frame_0.shape
    assert edge_jitter.shape == frame_0.shape
    assert flicker_gray[:, 7:9].mean() > flicker_gray[:, :3].mean()
    assert edge_gray[:, 6:9].mean() > edge_gray[:, :3].mean()


@pytest.mark.parametrize("directory", ["ascii", "résultats_日本"])
def test_export_visual_qa_writes_snapshots_panel_heatmap_and_metadata(tmp_path, directory):
    before = np.full((8, 8, 3), [10, 20, 30], dtype=np.uint8)
    after = np.full((8, 8, 3), [30, 40, 50], dtype=np.uint8)

    result = export_visual_qa(
        before,
        after,
        tmp_path / directory,
        stem="sample",
        notes={"quality_mode": "cinematic"},
    )

    for path in result.paths.values():
        assert path.exists()
        if path.suffix == ".png":
            assert read_image(str(path)) is not None

    np.testing.assert_array_equal(read_image(str(result.paths["before"])), before)
    np.testing.assert_array_equal(read_image(str(result.paths["after"])), after)

    metadata = json.loads(result.paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["stem"] == "sample"
    assert "before_edges" in metadata["files"]
    assert "after_edges" in metadata["files"]
    assert "edge_difference_heatmap" in metadata["files"]
    assert metadata["notes"]["quality_mode"] == "cinematic"
    assert metadata["metrics"]["mae"] > 0
    assert metadata["metrics"]["luma_mae"] > 0
    assert metadata["metrics"]["edge_mae"] == result.metrics["edge_mae"]


@pytest.mark.parametrize("directory", ["ascii", "résultats_日本"])
def test_export_temporal_qa_writes_heatmaps_and_metadata(tmp_path, directory):
    frame_0 = np.zeros((8, 8, 3), dtype=np.uint8)
    frame_1 = frame_0.copy()
    frame_1[:, 4:] = 80
    frame_2 = np.full((4, 4, 3), 40, dtype=np.uint8)

    result = export_temporal_qa(
        [frame_0, frame_1, frame_2],
        tmp_path / directory,
        stem="clip",
        notes={"quality_mode": "experimental"},
    )

    for path in result.paths.values():
        assert path.exists()
        if path.suffix == ".png":
            assert read_image(str(path)) is not None

    metadata = json.loads(result.paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["stem"] == "clip"
    assert metadata["notes"]["quality_mode"] == "experimental"
    assert metadata["metrics"]["frame_count"] == 3
    assert metadata["metrics"]["pair_count"] == 2
    assert "temporal_flicker_heatmap" in metadata["files"]
    assert "temporal_edge_jitter_heatmap" in metadata["files"]


def test_parse_frame_selection_accepts_comma_separated_indices():
    assert parse_frame_selection("0, 10,42,10") == {0, 10, 42}
    assert parse_frame_selection(None) == set()


def test_parse_frame_selection_rejects_invalid_values():
    for value in ("   ", "0,,2", "-1", "abc"):
        try:
            parse_frame_selection(value)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {value!r}")


def test_visual_qa_capture_session_exports_selected_frame_without_mutating_notes(tmp_path):
    notes = {"quality_mode": "balanced"}
    session = VisualQACaptureSession(
        tmp_path,
        {2},
        notes=notes,
    )
    before = np.full((8, 8, 3), 20, dtype=np.uint8)
    after = np.full((8, 8, 3), 80, dtype=np.uint8)

    assert not session.should_capture(1)
    assert session.should_capture(2)

    result = session.capture(2, before, after)

    assert result.paths["before"].name == "frame_000002_before.png"
    metadata = json.loads(result.paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["stem"] == "frame_000002"
    assert metadata["notes"]["quality_mode"] == "balanced"
    assert metadata["notes"]["frame_index"] == 2
    assert "frame_index" not in notes


def test_temporal_qa_capture_session_exports_selected_processed_frames(tmp_path):
    notes = {"quality_mode": "cinematic"}
    session = TemporalQACaptureSession(
        tmp_path,
        {1, 3},
        notes=notes,
    )
    frame_1 = np.zeros((8, 8, 3), dtype=np.uint8)
    frame_2 = np.full((8, 8, 3), 80, dtype=np.uint8)
    frame_3 = np.full((8, 8, 3), 160, dtype=np.uint8)

    assert not session.should_capture(0)
    assert session.should_capture(1)

    session.capture(0, frame_1)
    session.capture(1, frame_2)
    session.capture(3, frame_3)
    result = session.export()

    assert result is not None
    assert session.captured_frame_indices == [1, 3]
    metadata = json.loads(result.paths["metadata"].read_text(encoding="utf-8"))
    assert metadata["notes"]["quality_mode"] == "cinematic"
    assert metadata["notes"]["frame_indices"] == [1, 3]
    assert metadata["notes"]["captured_frame_indices"] == [1, 3]
    assert metadata["metrics"]["frame_count"] == 2
    assert "captured_frame_indices" not in notes


def test_temporal_qa_capture_session_export_bypasses_without_frames(tmp_path):
    session = TemporalQACaptureSession(tmp_path, {4})

    assert session.export() is None
