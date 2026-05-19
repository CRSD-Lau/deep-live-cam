"""Benchmark JSONL loading, summarization, and comparison helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_benchmark_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load benchmark snapshots from a JSONL file."""
    records: list[dict[str, Any]] = []
    benchmark_path = Path(path)
    for line_number, line in enumerate(
        benchmark_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid benchmark JSON on line {line_number} of {benchmark_path}"
            ) from exc
        if not isinstance(record, dict):
            raise ValueError(
                f"Benchmark record on line {line_number} of {benchmark_path} is not an object"
            )
        records.append(record)
    if not records:
        raise ValueError(f"No benchmark records found in {benchmark_path}")
    return records


def select_benchmark_snapshot(
    records: list[dict[str, Any]],
    *,
    preferred_event: str = "final",
) -> dict[str, Any]:
    """Select the last matching snapshot, falling back to the final record."""
    for record in reversed(records):
        if record.get("event") == preferred_event:
            return record
    return records[-1]


def summarize_benchmark(records: list[dict[str, Any]]) -> dict[str, Any]:
    snapshot = select_benchmark_snapshot(records)
    stages = _stage_summary(snapshot.get("stages") or {})
    context = snapshot.get("context") or {}
    dropped_frames = int(snapshot.get("dropped_frames") or 0)
    return {
        "event": snapshot.get("event"),
        "name": snapshot.get("name"),
        "frames": int(snapshot.get("frames") or 0),
        "fps": _as_float(snapshot.get("fps")),
        "dropped_frames": dropped_frames,
        "drop_reasons": _drop_reason_summary(
            snapshot.get("drop_reasons") or {},
            dropped_frames,
        ),
        "elapsed_seconds": _as_float(snapshot.get("elapsed_seconds")),
        "stages": stages,
        "budget": _budget_summary(snapshot, stages),
        "bottlenecks": _bottleneck_summary(stages),
        "queues": _queue_summary(snapshot.get("queues") or {}, context),
        "vram_mb": _numeric_dict(snapshot.get("vram_mb") or {}),
        "context": context,
    }


def compare_benchmarks(
    baseline_records: list[dict[str, Any]],
    candidate_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare two benchmark runs using their selected final snapshots."""
    baseline = summarize_benchmark(baseline_records)
    candidate = summarize_benchmark(candidate_records)
    return {
        "baseline": baseline,
        "candidate": candidate,
        "fps": _delta_block(baseline["fps"], candidate["fps"]),
        "dropped_frames_delta": candidate["dropped_frames"] - baseline["dropped_frames"],
        "elapsed_seconds": _delta_block(
            baseline["elapsed_seconds"], candidate["elapsed_seconds"]
        ),
        "budget": _compare_budget_summaries(
            baseline.get("budget") or {},
            candidate.get("budget") or {},
        ),
        "drop_reasons": _compare_numeric_dicts(
            baseline.get("drop_reasons") or {},
            candidate.get("drop_reasons") or {},
        ),
        "queues": _compare_queue_summaries(
            baseline.get("queues") or {},
            candidate.get("queues") or {},
        ),
        "stages": _compare_stage_summaries(
            baseline.get("stages") or {},
            candidate.get("stages") or {},
        ),
        "vram_mb": _compare_numeric_dicts(
            baseline.get("vram_mb") or {},
            candidate.get("vram_mb") or {},
        ),
    }


def format_benchmark_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"Benchmark {summary.get('name') or 'run'} ({summary.get('event') or 'snapshot'})",
        f"- frames: {summary['frames']}",
        f"- fps: {summary['fps']:.2f}",
        f"- dropped frames: {summary['dropped_frames']}",
        f"- elapsed seconds: {summary['elapsed_seconds']:.3f}",
    ]
    if summary.get("context"):
        context = summary["context"]
        if context.get("quality_mode"):
            lines.append(f"- quality mode: {context['quality_mode']}")
        if context.get("frame_processors"):
            lines.append(f"- processors: {', '.join(map(str, context['frame_processors']))}")
        if "live_process_latest_frame" in context:
            latest = "yes" if context.get("live_process_latest_frame") else "no"
            lines.append(f"- live latest-frame queue: {latest}")
    if summary.get("stages"):
        lines.append("Stages:")
        for stage_name, values in sorted(summary["stages"].items()):
            lines.append(
                f"- {stage_name}: avg={values['avg_ms']:.3f}ms "
                f"p95={values['p95_ms']:.3f}ms "
                f"min={values['min_ms']:.3f}ms max={values['max_ms']:.3f}ms "
                f"count={values['count']}"
            )
    if summary.get("drop_reasons"):
        lines.append("Drop Reasons:")
        for reason, count in sorted(
            summary["drop_reasons"].items(),
            key=lambda item: (-int(item[1]), item[0]),
        ):
            lines.append(f"- {reason}: {int(count)}")
    if summary.get("queues"):
        lines.append("Queue Pressure:")
        for queue_name, values in sorted(
            summary["queues"].items(),
            key=lambda item: (
                -float(item[1].get("p95_fill_pct", 0.0)),
                -float(item[1].get("max_depth", 0.0)),
                item[0],
            ),
        ):
            line = (
                f"- {queue_name}: avg={values['avg_depth']:.3f} "
                f"p95={values['p95_depth']:.3f} "
                f"max={values['max_depth']:.3f}"
            )
            if values.get("capacity", 0.0) > 0.0:
                line += (
                    f" fill(avg={values['avg_fill_pct']:.2f}% "
                    f"p95={values['p95_fill_pct']:.2f}% "
                    f"max={values['max_fill_pct']:.2f}%)"
                )
            lines.append(line)
    if summary.get("budget", {}).get("frame_budget_ms", 0.0) > 0.0:
        budget = summary["budget"]
        lines.append("Budget:")
        lines.append(
            f"- target fps: {budget['target_fps']:.2f} "
            f"({budget['frame_budget_ms']:.3f}ms/frame)"
        )
        lines.append(
            f"- stage avg total: {budget['stage_total_avg_ms']:.3f}ms "
            f"headroom={budget['avg_headroom_ms']:+.3f}ms "
            f"utilization={budget['avg_utilization_pct']:.2f}%"
        )
        lines.append(
            f"- stage p95 total: {budget['stage_total_p95_ms']:.3f}ms "
            f"headroom={budget['p95_headroom_ms']:+.3f}ms "
            f"utilization={budget['p95_utilization_pct']:.2f}%"
        )
    if summary.get("bottlenecks"):
        lines.append("Bottlenecks:")
        for item in summary["bottlenecks"][:5]:
            lines.append(
                f"- {item['stage']}: avg={item['avg_ms']:.3f}ms "
                f"share={item['avg_share_pct']:.2f}% "
                f"p95={item['p95_ms']:.3f}ms"
            )
    if summary.get("vram_mb"):
        lines.append("VRAM:")
        for key, value in sorted(summary["vram_mb"].items()):
            lines.append(f"- {key}: {int(value)}MB")
    return "\n".join(lines)


def format_benchmark_comparison(comparison: dict[str, Any]) -> str:
    baseline = comparison["baseline"]
    candidate = comparison["candidate"]
    fps = comparison["fps"]
    lines = [
        "Benchmark Comparison",
        f"- baseline: {baseline.get('name') or 'run'} "
        f"frames={baseline['frames']} fps={baseline['fps']:.2f}",
        f"- candidate: {candidate.get('name') or 'run'} "
        f"frames={candidate['frames']} fps={candidate['fps']:.2f}",
        f"- fps delta: {fps['delta']:+.2f} ({fps['delta_pct']:+.2f}%)",
        f"- dropped frame delta: {comparison['dropped_frames_delta']:+d}",
    ]
    if comparison.get("drop_reasons"):
        lines.append("Drop Reason Delta:")
        for reason, values in sorted(
            comparison["drop_reasons"].items(),
            key=lambda item: (-abs(int(item[1].get("delta", 0))), item[0]),
        ):
            lines.append(
                f"- {reason}: {values['baseline']} -> {values['candidate']} "
                f"({values['delta']:+d})"
            )
    if comparison.get("queues"):
        lines.append("Queue Pressure Delta:")
        for queue_name, values in sorted(comparison["queues"].items()):
            avg = values["avg_depth"]
            p95 = values["p95_depth"]
            max_depth = values["max_depth"]
            lines.append(
                f"- {queue_name}: avg {avg['baseline']:.3f} -> "
                f"{avg['candidate']:.3f} ({avg['delta']:+.3f}), "
                f"p95 {p95['baseline']:.3f} -> {p95['candidate']:.3f} "
                f"({p95['delta']:+.3f}), "
                f"max {max_depth['baseline']:.3f} -> "
                f"{max_depth['candidate']:.3f} ({max_depth['delta']:+.3f})"
            )
    if comparison.get("budget", {}).get("stage_total_avg_ms"):
        budget = comparison["budget"]
        avg = budget["stage_total_avg_ms"]
        p95 = budget["stage_total_p95_ms"]
        headroom = budget["avg_headroom_ms"]
        lines.append("Budget Delta:")
        lines.append(
            f"- stage avg total: {avg['baseline']:.3f}ms -> "
            f"{avg['candidate']:.3f}ms "
            f"({avg['delta']:+.3f}ms, {avg['delta_pct']:+.2f}%)"
        )
        lines.append(
            f"- stage p95 total: {p95['baseline']:.3f}ms -> "
            f"{p95['candidate']:.3f}ms "
            f"({p95['delta']:+.3f}ms, {p95['delta_pct']:+.2f}%)"
        )
        lines.append(
            f"- avg headroom: {headroom['baseline']:+.3f}ms -> "
            f"{headroom['candidate']:+.3f}ms "
            f"({headroom['delta']:+.3f}ms)"
        )
    if comparison.get("stages"):
        lines.append("Stage Avg Delta:")
        for stage_name, values in sorted(comparison["stages"].items()):
            lines.append(
                f"- {stage_name}: {values['baseline_avg_ms']:.3f}ms -> "
                f"{values['candidate_avg_ms']:.3f}ms "
                f"({values['delta_ms']:+.3f}ms, {values['delta_pct']:+.2f}%) "
                f"p95 {values['baseline_p95_ms']:.3f}ms -> "
                f"{values['candidate_p95_ms']:.3f}ms "
                f"({values['p95_delta_ms']:+.3f}ms)"
            )
    if comparison.get("vram_mb"):
        lines.append("VRAM Delta:")
        for key, values in sorted(comparison["vram_mb"].items()):
            lines.append(
                f"- {key}: {values['baseline']}MB -> {values['candidate']}MB "
                f"({values['delta']:+d}MB)"
            )
    return "\n".join(lines)


def _stage_summary(stages: dict[str, Any]) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for stage_name, values in stages.items():
        if not isinstance(values, dict):
            continue
        result[str(stage_name)] = {
            "count": int(values.get("count") or 0),
            "avg_ms": _as_float(values.get("avg_ms")),
            "min_ms": _as_float(values.get("min_ms")),
            "max_ms": _as_float(values.get("max_ms")),
            "p95_ms": _as_float(values.get("p95_ms")),
            "p99_ms": _as_float(values.get("p99_ms")),
            "sample_count": int(values.get("sample_count") or 0),
        }
    return result


def _queue_summary(
    queues: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for queue_name, values in queues.items():
        if not isinstance(values, dict):
            continue
        name = str(queue_name)
        capacity = _queue_capacity(name, context)
        avg_depth = _as_float(values.get("avg_depth"))
        max_depth = _as_float(values.get("max_depth"))
        p95_depth = _as_float(values.get("p95_depth"))
        p99_depth = _as_float(values.get("p99_depth"))
        result[name] = {
            "count": int(values.get("count") or 0),
            "avg_depth": avg_depth,
            "min_depth": _as_float(values.get("min_depth")),
            "max_depth": max_depth,
            "p95_depth": p95_depth,
            "p99_depth": p99_depth,
            "sample_count": int(values.get("sample_count") or 0),
            "capacity": capacity,
            "avg_fill_pct": _utilization_pct(avg_depth, capacity),
            "max_fill_pct": _utilization_pct(max_depth, capacity),
            "p95_fill_pct": _utilization_pct(p95_depth, capacity),
            "p99_fill_pct": _utilization_pct(p99_depth, capacity),
        }
    return result


def _drop_reason_summary(
    reasons: dict[str, Any],
    dropped_frames: int,
) -> dict[str, int]:
    result = _numeric_dict(reasons)
    unaccounted = int(dropped_frames) - sum(result.values())
    if unaccounted > 0:
        result["unspecified"] = result.get("unspecified", 0) + unaccounted
    return dict(sorted(result.items()))


def _compare_stage_summaries(
    baseline: dict[str, dict[str, float | int]],
    candidate: dict[str, dict[str, float | int]],
) -> dict[str, dict[str, float]]:
    comparison: dict[str, dict[str, float]] = {}
    for stage_name in sorted(set(baseline) | set(candidate)):
        baseline_avg = float(baseline.get(stage_name, {}).get("avg_ms", 0.0))
        candidate_avg = float(candidate.get(stage_name, {}).get("avg_ms", 0.0))
        baseline_p95 = float(baseline.get(stage_name, {}).get("p95_ms", 0.0))
        candidate_p95 = float(candidate.get(stage_name, {}).get("p95_ms", 0.0))
        delta = candidate_avg - baseline_avg
        p95_delta = candidate_p95 - baseline_p95
        comparison[stage_name] = {
            "baseline_avg_ms": round(baseline_avg, 4),
            "candidate_avg_ms": round(candidate_avg, 4),
            "delta_ms": round(delta, 4),
            "delta_pct": _percent_delta(baseline_avg, candidate_avg),
            "baseline_p95_ms": round(baseline_p95, 4),
            "candidate_p95_ms": round(candidate_p95, 4),
            "p95_delta_ms": round(p95_delta, 4),
            "p95_delta_pct": _percent_delta(baseline_p95, candidate_p95),
        }
    return comparison


def _compare_queue_summaries(
    baseline: dict[str, dict[str, float | int]],
    candidate: dict[str, dict[str, float | int]],
) -> dict[str, dict[str, dict[str, float]]]:
    comparison: dict[str, dict[str, dict[str, float]]] = {}
    for queue_name in sorted(set(baseline) | set(candidate)):
        baseline_values = baseline.get(queue_name, {})
        candidate_values = candidate.get(queue_name, {})
        comparison[queue_name] = {
            key: _delta_block(
                float(baseline_values.get(key, 0.0)),
                float(candidate_values.get(key, 0.0)),
            )
            for key in (
                "avg_depth",
                "p95_depth",
                "max_depth",
                "avg_fill_pct",
                "p95_fill_pct",
                "max_fill_pct",
            )
        }
    return comparison


def _budget_summary(
    snapshot: dict[str, Any],
    stages: dict[str, dict[str, float | int]],
) -> dict[str, float]:
    stage_total_avg = round(
        sum(float(values.get("avg_ms", 0.0)) for values in stages.values()),
        4,
    )
    stage_total_p95 = round(
        sum(float(values.get("p95_ms", 0.0)) for values in stages.values()),
        4,
    )
    estimated_stage_fps = _fps_from_ms(stage_total_avg)
    target_fps = _target_fps(snapshot)
    frame_budget_ms = round(1000.0 / target_fps, 4) if target_fps > 0.0 else 0.0
    avg_headroom = (
        round(frame_budget_ms - stage_total_avg, 4)
        if frame_budget_ms > 0.0
        else 0.0
    )
    p95_headroom = (
        round(frame_budget_ms - stage_total_p95, 4)
        if frame_budget_ms > 0.0
        else 0.0
    )
    return {
        "target_fps": round(target_fps, 4),
        "frame_budget_ms": frame_budget_ms,
        "stage_total_avg_ms": stage_total_avg,
        "stage_total_p95_ms": stage_total_p95,
        "estimated_stage_fps": estimated_stage_fps,
        "avg_headroom_ms": avg_headroom,
        "p95_headroom_ms": p95_headroom,
        "avg_utilization_pct": _utilization_pct(stage_total_avg, frame_budget_ms),
        "p95_utilization_pct": _utilization_pct(stage_total_p95, frame_budget_ms),
    }


def _bottleneck_summary(
    stages: dict[str, dict[str, float | int]],
) -> list[dict[str, float | str]]:
    total_avg = sum(float(values.get("avg_ms", 0.0)) for values in stages.values())
    total_p95 = sum(float(values.get("p95_ms", 0.0)) for values in stages.values())
    bottlenecks: list[dict[str, float | str]] = []
    for stage_name, values in stages.items():
        avg_ms = float(values.get("avg_ms", 0.0))
        p95_ms = float(values.get("p95_ms", 0.0))
        bottlenecks.append(
            {
                "stage": stage_name,
                "avg_ms": round(avg_ms, 4),
                "p95_ms": round(p95_ms, 4),
                "avg_share_pct": _share_pct(avg_ms, total_avg),
                "p95_share_pct": _share_pct(p95_ms, total_p95),
            }
        )
    return sorted(
        bottlenecks,
        key=lambda item: (float(item["avg_ms"]), float(item["p95_ms"])),
        reverse=True,
    )


def _compare_budget_summaries(
    baseline: dict[str, float],
    candidate: dict[str, float],
) -> dict[str, dict[str, float]]:
    return {
        key: _delta_block(
            float(baseline.get(key, 0.0)),
            float(candidate.get(key, 0.0)),
        )
        for key in (
            "stage_total_avg_ms",
            "stage_total_p95_ms",
            "estimated_stage_fps",
            "avg_headroom_ms",
            "p95_headroom_ms",
            "avg_utilization_pct",
            "p95_utilization_pct",
        )
    }


def _compare_numeric_dicts(
    baseline: dict[str, int],
    candidate: dict[str, int],
) -> dict[str, dict[str, int]]:
    return {
        key: {
            "baseline": int(baseline.get(key, 0)),
            "candidate": int(candidate.get(key, 0)),
            "delta": int(candidate.get(key, 0)) - int(baseline.get(key, 0)),
        }
        for key in sorted(set(baseline) | set(candidate))
    }


def _numeric_dict(value: dict[str, Any]) -> dict[str, int]:
    return {str(key): _as_int(item) for key, item in value.items()}


def _queue_capacity(queue_name: str, context: dict[str, Any]) -> float:
    if queue_name.startswith("capture_queue"):
        return _as_float(context.get("capture_queue_maxsize"))
    if queue_name.startswith("processed_queue"):
        return _as_float(context.get("processed_queue_maxsize"))
    return _as_float(context.get(f"{queue_name}_maxsize"))


def _delta_block(baseline: float, candidate: float) -> dict[str, float]:
    return {
        "baseline": round(baseline, 4),
        "candidate": round(candidate, 4),
        "delta": round(candidate - baseline, 4),
        "delta_pct": _percent_delta(baseline, candidate),
    }


def _percent_delta(baseline: float, candidate: float) -> float:
    if abs(baseline) <= 1e-9:
        return 0.0
    return round(((candidate - baseline) / baseline) * 100.0, 4)


def _target_fps(snapshot: dict[str, Any]) -> float:
    context = snapshot.get("context") if isinstance(snapshot.get("context"), dict) else {}
    for value in (
        context.get("target_fps"),
        context.get("fps"),
        snapshot.get("target_fps"),
    ):
        fps = _as_float(value)
        if fps > 0.0:
            return fps
    return 0.0


def _fps_from_ms(milliseconds: float) -> float:
    if milliseconds <= 1e-9:
        return 0.0
    return round(1000.0 / milliseconds, 4)


def _utilization_pct(milliseconds: float, frame_budget_ms: float) -> float:
    if frame_budget_ms <= 1e-9:
        return 0.0
    return round((milliseconds / frame_budget_ms) * 100.0, 4)


def _share_pct(value: float, total: float) -> float:
    if total <= 1e-9:
        return 0.0
    return round((value / total) * 100.0, 4)


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
