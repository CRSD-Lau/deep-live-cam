import json

import pytest

from modules.visual_qa_report import (
    compare_visual_qa,
    format_visual_qa_comparison,
    format_visual_qa_summary,
    load_visual_qa_metadata,
    summarize_visual_qa,
)


def frame_metadata(*, stem="frame", mae=12.0, edge_mae=4.0):
    return {
        "stem": stem,
        "files": {"metadata": "ignored"},
        "metrics": {
            "mae": mae,
            "rmse": mae + 2.0,
            "edge_mae": edge_mae,
            "mean_abs_bgr": [mae, mae, mae],
        },
        "notes": {
            "quality_mode": "cinematic",
            "frame_index": 7,
        },
    }


def temporal_metadata(*, stem="temporal", mean_pair_mae=8.0, edge_mae=3.0):
    return {
        "stem": stem,
        "files": {"metadata": "ignored"},
        "metrics": {
            "frame_count": 3,
            "pair_count": 2,
            "mean_pair_mae": mean_pair_mae,
            "mean_edge_mae": edge_mae,
            "pairs": [{"mae": mean_pair_mae}],
        },
        "notes": {
            "quality_mode": "experimental",
            "captured_frame_indices": [0, 3, 6],
        },
    }


def test_load_visual_qa_metadata_validates_json_shape(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(frame_metadata()), encoding="utf-8")

    metadata = load_visual_qa_metadata(path)

    assert metadata["metrics"]["mae"] == 12.0


def test_load_visual_qa_metadata_rejects_invalid_json(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_text("{not-json}", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid visual QA JSON"):
        load_visual_qa_metadata(path)


def test_summarize_visual_qa_detects_frame_and_formats_context():
    summary = summarize_visual_qa(frame_metadata())

    assert summary["kind"] == "frame"
    assert summary["metrics"]["mae"] == 12.0
    assert "mean_abs_bgr" not in summary["metrics"]
    formatted = format_visual_qa_summary(summary)
    assert "quality mode: cinematic" in formatted
    assert "frame index: 7" in formatted
    assert "mae: 12.0000" in formatted


def test_summarize_visual_qa_detects_temporal_metadata():
    summary = summarize_visual_qa(temporal_metadata())

    assert summary["kind"] == "temporal"
    assert summary["metrics"]["mean_pair_mae"] == 8.0
    formatted = format_visual_qa_summary(summary)
    assert "captured frames: 0, 3, 6" in formatted


def test_compare_visual_qa_reports_lower_is_better_improvement():
    baseline = frame_metadata(stem="base", mae=12.0, edge_mae=5.0)
    candidate = frame_metadata(stem="candidate", mae=9.0, edge_mae=7.0)

    comparison = compare_visual_qa(baseline, candidate)

    assert comparison["kind"] == "frame"
    assert comparison["metrics"]["mae"]["delta"] == -3.0
    assert comparison["metrics"]["mae"]["improvement"] == 3.0
    assert comparison["metrics"]["mae"]["improvement_pct"] == 25.0
    assert comparison["metrics"]["mae"]["direction"] == "lower_is_better"
    assert comparison["metrics"]["edge_mae"]["improvement"] == -2.0
    assert comparison["summary"]["improved"] == 2
    assert comparison["summary"]["regressed"] == 1
    assert comparison["improvements"][0]["metric"] == "mae"
    assert comparison["regressions"][0]["metric"] == "edge_mae"
    formatted = format_visual_qa_comparison(comparison)
    assert "Visual QA Comparison" in formatted
    assert "Regressions:" in formatted
    assert "Top Improvements:" in formatted
    assert "lower is better" in formatted
    assert "mae" in formatted


def test_compare_visual_qa_handles_temporal_metadata():
    comparison = compare_visual_qa(
        temporal_metadata(stem="base", mean_pair_mae=8.0, edge_mae=4.0),
        temporal_metadata(stem="candidate", mean_pair_mae=6.0, edge_mae=3.0),
    )

    assert comparison["kind"] == "temporal"
    assert comparison["metrics"]["mean_pair_mae"]["improvement"] == 2.0
    assert comparison["metrics"]["mean_edge_mae"]["improvement_pct"] == 25.0
    assert "frame_count" not in comparison["metrics"]
    assert "pair_count" not in comparison["metrics"]
    assert comparison["summary"]["shared_metrics"] == 2


def test_compare_visual_qa_ranks_largest_regression_by_percent():
    baseline = frame_metadata(stem="base", mae=10.0, edge_mae=2.0)
    candidate = frame_metadata(stem="candidate", mae=11.0, edge_mae=4.0)

    comparison = compare_visual_qa(baseline, candidate)

    assert comparison["summary"]["improved"] == 0
    assert comparison["summary"]["regressed"] == 3
    assert comparison["regressions"][0]["metric"] == "edge_mae"
    assert comparison["regressions"][0]["improvement_pct"] == -100.0
