import json

import pytest

from modules.benchmark_report import (
    compare_benchmarks,
    format_benchmark_comparison,
    format_benchmark_summary,
    load_benchmark_jsonl,
    summarize_benchmark,
)


def record(
    *,
    event="final",
    fps=30.0,
    frames=60,
    dropped=0,
    swap_ms=10.0,
    detect_ms=4.0,
    vram=512,
    target_fps=30.0,
    drop_reasons=None,
    queues=None,
    capture_queue_maxsize=2,
    processed_queue_maxsize=2,
    live_process_latest_frame=None,
):
    drop_reasons = drop_reasons if drop_reasons is not None else {}
    queues = queues if queues is not None else {}
    benchmark_record = {
        "event": event,
        "name": "video",
        "frames": frames,
        "fps": fps,
        "dropped_frames": dropped,
        "drop_reasons": drop_reasons,
        "elapsed_seconds": 2.0,
        "stages": {
            "swap": {
                "count": frames,
                "avg_ms": swap_ms,
                "min_ms": swap_ms - 1,
                "max_ms": swap_ms + 1,
                "p95_ms": swap_ms + 0.5,
                "p99_ms": swap_ms + 0.9,
                "sample_count": min(frames, 512),
            },
            "detect": {
                "count": frames,
                "avg_ms": detect_ms,
                "min_ms": detect_ms - 1,
                "max_ms": detect_ms + 1,
                "p95_ms": detect_ms + 0.5,
                "p99_ms": detect_ms + 0.9,
                "sample_count": min(frames, 512),
            }
        },
        "queues": queues,
        "vram_mb": {"cuda_reserved": vram},
        "context": {
            "quality_mode": "cinematic",
            "frame_processors": ["face_swapper"],
            "target_fps": target_fps,
            "capture_queue_maxsize": capture_queue_maxsize,
            "processed_queue_maxsize": processed_queue_maxsize,
        },
    }
    if live_process_latest_frame is not None:
        benchmark_record["context"]["live_process_latest_frame"] = (
            live_process_latest_frame
        )
    return benchmark_record


def test_load_benchmark_jsonl_skips_blanks_and_selects_final_summary(tmp_path):
    path = tmp_path / "run.jsonl"
    path.write_text(
        json.dumps(record(event="periodic", fps=20.0)) + "\n\n"
        + json.dumps(record(event="final", fps=30.0)) + "\n",
        encoding="utf-8",
    )

    records = load_benchmark_jsonl(path)
    summary = summarize_benchmark(records)

    assert len(records) == 2
    assert summary["event"] == "final"
    assert summary["fps"] == 30.0
    assert summary["stages"]["swap"]["avg_ms"] == 10.0
    assert summary["stages"]["swap"]["p95_ms"] == 10.5
    assert summary["budget"]["stage_total_avg_ms"] == 14.0
    assert summary["budget"]["avg_headroom_ms"] == pytest.approx(19.3333)
    assert summary["bottlenecks"][0]["stage"] == "swap"
    assert summary["bottlenecks"][0]["avg_share_pct"] == pytest.approx(71.4286)
    assert "quality mode" in format_benchmark_summary(summary)
    assert "p95=10.500ms" in format_benchmark_summary(summary)
    assert "Budget:" in format_benchmark_summary(summary)
    assert "Bottlenecks:" in format_benchmark_summary(summary)


def test_summarize_benchmark_reports_drop_reasons_and_queue_pressure():
    summary = summarize_benchmark([
        record(
            dropped=5,
            drop_reasons={"capture_input_queue": 3},
            live_process_latest_frame=True,
            queues={
                "capture_queue_depth_after_get": {
                    "count": 4,
                    "avg_depth": 1.25,
                    "min_depth": 0,
                    "max_depth": 2,
                    "p95_depth": 1.8,
                    "p99_depth": 2,
                    "sample_count": 4,
                },
                "processed_queue_depth_before_put": {
                    "count": 4,
                    "avg_depth": 0.5,
                    "min_depth": 0,
                    "max_depth": 1,
                    "p95_depth": 1,
                    "p99_depth": 1,
                    "sample_count": 4,
                },
            },
        )
    ])

    assert summary["drop_reasons"] == {
        "capture_input_queue": 3,
        "unspecified": 2,
    }
    capture_queue = summary["queues"]["capture_queue_depth_after_get"]
    assert capture_queue["capacity"] == 2.0
    assert capture_queue["avg_fill_pct"] == 62.5
    assert capture_queue["p95_fill_pct"] == 90.0
    assert capture_queue["max_fill_pct"] == 100.0

    formatted = format_benchmark_summary(summary)
    assert "Drop Reasons:" in formatted
    assert "capture_input_queue: 3" in formatted
    assert "Queue Pressure:" in formatted
    assert "capture_queue_depth_after_get" in formatted
    assert "fill(avg=62.50%" in formatted
    assert "live latest-frame queue: yes" in formatted


def test_load_benchmark_jsonl_reports_invalid_json(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid benchmark JSON"):
        load_benchmark_jsonl(path)


def test_compare_benchmarks_reports_fps_stage_drop_and_vram_deltas():
    baseline = [record(fps=30.0, dropped=1, swap_ms=10.0, vram=400)]
    candidate = [record(fps=36.0, dropped=0, swap_ms=8.0, detect_ms=3.0, vram=450)]

    comparison = compare_benchmarks(baseline, candidate)

    assert comparison["fps"]["delta"] == 6.0
    assert comparison["fps"]["delta_pct"] == 20.0
    assert comparison["dropped_frames_delta"] == -1
    assert comparison["stages"]["swap"]["delta_ms"] == -2.0
    assert comparison["stages"]["swap"]["delta_pct"] == -20.0
    assert comparison["stages"]["swap"]["p95_delta_ms"] == -2.0
    assert comparison["budget"]["stage_total_avg_ms"]["delta"] == -3.0
    assert comparison["budget"]["avg_headroom_ms"]["delta"] == 3.0
    assert comparison["vram_mb"]["cuda_reserved"]["delta"] == 50
    formatted = format_benchmark_comparison(comparison)
    assert "fps delta" in formatted
    assert "p95" in formatted
    assert "Budget Delta" in formatted


def test_compare_benchmarks_reports_drop_reason_and_queue_pressure_deltas():
    baseline = [
        record(
            dropped=1,
            drop_reasons={"processed_output_queue": 1},
            queues={
                "capture_queue_depth_after_get": {
                    "count": 3,
                    "avg_depth": 0.25,
                    "min_depth": 0,
                    "max_depth": 1,
                    "p95_depth": 0.5,
                    "p99_depth": 1,
                    "sample_count": 3,
                },
            },
        )
    ]
    candidate = [
        record(
            dropped=4,
            drop_reasons={
                "capture_input_queue": 3,
                "processed_output_queue": 1,
            },
            queues={
                "capture_queue_depth_after_get": {
                    "count": 3,
                    "avg_depth": 1.25,
                    "min_depth": 1,
                    "max_depth": 2,
                    "p95_depth": 2,
                    "p99_depth": 2,
                    "sample_count": 3,
                },
            },
        )
    ]

    comparison = compare_benchmarks(baseline, candidate)

    assert comparison["drop_reasons"]["capture_input_queue"]["delta"] == 3
    assert comparison["drop_reasons"]["processed_output_queue"]["delta"] == 0
    capture_queue = comparison["queues"]["capture_queue_depth_after_get"]
    assert capture_queue["avg_depth"]["delta"] == 1.0
    assert capture_queue["p95_fill_pct"]["delta"] == 75.0
    assert capture_queue["max_fill_pct"]["delta"] == 50.0

    formatted = format_benchmark_comparison(comparison)
    assert "Drop Reason Delta:" in formatted
    assert "capture_input_queue" in formatted
    assert "Queue Pressure Delta:" in formatted


def test_summarize_benchmark_falls_back_to_last_record_without_final():
    summary = summarize_benchmark([
        record(event="periodic", fps=15.0),
        record(event="periodic", fps=18.0),
    ])

    assert summary["event"] == "periodic"
    assert summary["fps"] == 18.0


def test_summarize_benchmark_omits_budget_when_no_target_fps():
    summary = summarize_benchmark([record(target_fps=0.0)])

    assert summary["budget"]["target_fps"] == 0.0
    assert summary["budget"]["frame_budget_ms"] == 0.0
    assert "Budget:" not in format_benchmark_summary(summary)
