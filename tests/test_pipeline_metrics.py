import json

from modules.pipeline_metrics import (
    MetricsJsonlWriter,
    PipelineMetrics,
    format_metrics,
    metrics_snapshot,
)


def test_metrics_accumulate_stage_latency():
    metrics = PipelineMetrics("test")

    metrics.observe("detect", 0.002)
    metrics.observe("detect", 0.004)

    snapshot = metrics.stage_snapshot()
    assert snapshot["detect"]["count"] == 2
    assert snapshot["detect"]["avg_ms"] == 3.0
    assert snapshot["detect"]["min_ms"] == 2.0
    assert snapshot["detect"]["max_ms"] == 4.0
    assert snapshot["detect"]["p95_ms"] == 3.9
    assert snapshot["detect"]["p99_ms"] == 3.98
    assert snapshot["detect"]["sample_count"] == 2


def test_metrics_stage_latency_samples_are_bounded():
    metrics = PipelineMetrics("test")

    for index in range(600):
        metrics.observe("swap", index / 1000.0)

    snapshot = metrics.stage_snapshot()
    assert snapshot["swap"]["count"] == 600
    assert snapshot["swap"]["sample_count"] == 512
    assert snapshot["swap"]["p95_ms"] > snapshot["swap"]["avg_ms"]


def test_metrics_format_includes_fps_and_stage():
    metrics = PipelineMetrics("test")

    metrics.observe("swap", 0.001)
    metrics.frame_complete()
    text = format_metrics(metrics, include_vram=False)

    assert "[benchmark:test]" in text
    assert "fps=" in text
    assert "swap=" in text
    assert "p95=" in text


def test_metrics_count_dropped_frames():
    metrics = PipelineMetrics("test")

    metrics.drop_frame()
    text = format_metrics(metrics, include_vram=False)

    assert "dropped=1" in text


def test_metrics_distinguish_drop_reasons():
    metrics = PipelineMetrics("test")

    metrics.drop_frame("capture_input_queue")
    metrics.drop_frames("capture_stale_queue", 2)
    metrics.drop_frame("processed_output_queue")
    metrics.drop_frame()

    dropped_frames, drop_reasons = metrics.drop_summary()
    snapshot = metrics_snapshot(metrics, include_vram=False)
    text = format_metrics(metrics, include_vram=False)

    assert dropped_frames == 5
    assert drop_reasons == {
        "capture_input_queue": 1,
        "capture_stale_queue": 2,
        "processed_output_queue": 1,
        "unspecified": 1,
    }
    assert snapshot["dropped_frames"] == 5
    assert snapshot["drop_reasons"] == {
        "capture_input_queue": 1,
        "capture_stale_queue": 2,
        "processed_output_queue": 1,
        "unspecified": 1,
    }
    assert "dropped=5" in text
    assert "capture_input_queue=1" in text
    assert "capture_stale_queue=2" in text
    assert "processed_output_queue=1" in text
    assert "unspecified=1" in text


def test_metrics_snapshot_includes_queue_depth_samples():
    metrics = PipelineMetrics("test")

    metrics.observe_queue_depth("capture_queue_depth_after_get", 2)
    metrics.observe_queue_depth("capture_queue_depth_after_get", 0)
    metrics.observe_queue_depth("processed_queue_depth_before_put", 1)

    snapshot = metrics_snapshot(metrics, include_vram=False)
    text = format_metrics(metrics, include_vram=False)

    assert snapshot["queues"]["capture_queue_depth_after_get"]["count"] == 2
    assert snapshot["queues"]["capture_queue_depth_after_get"]["avg_depth"] == 1.0
    assert snapshot["queues"]["capture_queue_depth_after_get"]["min_depth"] == 0.0
    assert snapshot["queues"]["capture_queue_depth_after_get"]["max_depth"] == 2.0
    assert snapshot["queues"]["processed_queue_depth_before_put"]["avg_depth"] == 1.0
    assert "queues:" in text
    assert "capture_queue_depth_after_get=" in text
    assert "processed_queue_depth_before_put=" in text


def test_metrics_snapshot_is_json_serializable_with_context():
    metrics = PipelineMetrics("video")
    metrics.observe("swap", 0.002)
    metrics.frame_complete()
    metrics.drop_frame()

    snapshot = metrics_snapshot(
        metrics,
        event="final",
        include_vram=False,
        extra={"quality_mode": "cinematic", "processors": ("face_swapper",)},
    )

    assert snapshot["event"] == "final"
    assert snapshot["name"] == "video"
    assert snapshot["frames"] == 1
    assert snapshot["dropped_frames"] == 1
    assert snapshot["stages"]["swap"]["avg_ms"] == 2.0
    assert snapshot["stages"]["swap"]["p95_ms"] == 2.0
    assert snapshot["context"]["processors"] == ["face_swapper"]
    json.dumps(snapshot)


def test_metrics_jsonl_writer_appends_snapshots(tmp_path):
    metrics = PipelineMetrics("live")
    metrics.frame_complete()
    output_path = tmp_path / "benchmarks" / "run.jsonl"
    writer = MetricsJsonlWriter(output_path)

    writer.write(metrics, event="periodic", include_vram=False, extra={"fps": 30})
    metrics.frame_complete()
    writer.write(metrics, event="final", include_vram=False)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["event"] == "periodic"
    assert first["context"]["fps"] == 30
    assert second["event"] == "final"
    assert second["frames"] == 2
