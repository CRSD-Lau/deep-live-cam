"""Visual QA metadata loading, summarization, and comparison helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_visual_qa_metadata(path: str | Path) -> dict[str, Any]:
    """Load a visual or temporal QA metadata JSON file."""
    metadata_path = Path(path)
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid visual QA JSON in {metadata_path}") from exc
    if not isinstance(metadata, dict):
        raise ValueError(f"Visual QA metadata in {metadata_path} is not an object")
    if not isinstance(metadata.get("metrics"), dict):
        raise ValueError(f"Visual QA metadata in {metadata_path} has no metrics object")
    return metadata


def summarize_visual_qa(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return a compact summary of single-frame or temporal QA metadata."""
    metrics = metadata.get("metrics") or {}
    notes = metadata.get("notes") or {}
    return {
        "stem": metadata.get("stem"),
        "kind": _metadata_kind(metrics),
        "metrics": _numeric_metrics(metrics),
        "notes": notes if isinstance(notes, dict) else {},
        "files": metadata.get("files") or {},
    }


def compare_visual_qa(
    baseline_metadata: dict[str, Any],
    candidate_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Compare two QA metadata objects using numeric lower-is-better metrics."""
    baseline = summarize_visual_qa(baseline_metadata)
    candidate = summarize_visual_qa(candidate_metadata)
    shared_keys = [
        key
        for key in sorted(set(baseline["metrics"]) & set(candidate["metrics"]))
        if _metric_direction(key) != "neutral"
    ]
    metric_deltas = {
        key: _delta_block(
            baseline["metrics"][key],
            candidate["metrics"][key],
            direction=_metric_direction(key),
        )
        for key in shared_keys
    }
    return {
        "baseline": baseline,
        "candidate": candidate,
        "kind": (
            baseline["kind"]
            if baseline["kind"] == candidate["kind"]
            else "mixed"
        ),
        "metrics": metric_deltas,
        "summary": _comparison_summary(metric_deltas),
        "improvements": _rank_metric_changes(metric_deltas, improved=True),
        "regressions": _rank_metric_changes(metric_deltas, improved=False),
    }


def format_visual_qa_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"Visual QA {summary.get('stem') or 'metadata'} ({summary.get('kind')})",
    ]
    notes = summary.get("notes") or {}
    if notes.get("quality_mode"):
        lines.append(f"- quality mode: {notes['quality_mode']}")
    if notes.get("frame_index") is not None:
        lines.append(f"- frame index: {notes['frame_index']}")
    if notes.get("captured_frame_indices"):
        lines.append(
            "- captured frames: "
            + ", ".join(map(str, notes["captured_frame_indices"]))
        )
    lines.append("Metrics:")
    for key, value in sorted((summary.get("metrics") or {}).items()):
        lines.append(f"- {key}: {value:.4f}")
    return "\n".join(lines)


def format_visual_qa_comparison(comparison: dict[str, Any]) -> str:
    baseline = comparison["baseline"]
    candidate = comparison["candidate"]
    lines = [
        "Visual QA Comparison",
        f"- baseline: {baseline.get('stem') or 'metadata'} ({baseline.get('kind')})",
        f"- candidate: {candidate.get('stem') or 'metadata'} ({candidate.get('kind')})",
    ]
    metrics = comparison.get("metrics") or {}
    summary = comparison.get("summary") or {}
    if summary:
        lines.append(
            "- metrics: "
            f"{summary.get('improved', 0)} improved, "
            f"{summary.get('regressed', 0)} regressed, "
            f"{summary.get('unchanged', 0)} unchanged"
        )
        lines.append(
            f"- net improvement score: "
            f"{summary.get('net_improvement_score', 0.0):+.4f}"
        )
    if comparison.get("regressions"):
        lines.append("Regressions:")
        for item in comparison["regressions"][:5]:
            lines.append(
                f"- {item['metric']}: improvement="
                f"{item['improvement']:+.4f} "
                f"({item['improvement_pct']:+.2f}%)"
            )
    if comparison.get("improvements"):
        lines.append("Top Improvements:")
        for item in comparison["improvements"][:5]:
            lines.append(
                f"- {item['metric']}: improvement="
                f"{item['improvement']:+.4f} "
                f"({item['improvement_pct']:+.2f}%)"
            )
    if metrics:
        lines.append("Metric Delta (lower is better):")
        for key, values in sorted(metrics.items()):
            lines.append(
                f"- {key}: {values['baseline']:.4f} -> "
                f"{values['candidate']:.4f} "
                f"({values['delta']:+.4f}, "
                f"improvement={values['improvement']:+.4f}, "
                f"{values['improvement_pct']:+.2f}%)"
            )
    return "\n".join(lines)


def _metadata_kind(metrics: dict[str, Any]) -> str:
    if "pair_count" in metrics or "mean_pair_mae" in metrics:
        return "temporal"
    return "frame"


def _numeric_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    return {
        str(key): float(value)
        for key, value in metrics.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def _comparison_summary(
    metric_deltas: dict[str, dict[str, float | str]],
) -> dict[str, float | int]:
    improved = 0
    regressed = 0
    unchanged = 0
    scores: list[float] = []
    for values in metric_deltas.values():
        improvement = float(values["improvement"])
        if improvement > 0.0:
            improved += 1
        elif improvement < 0.0:
            regressed += 1
        else:
            unchanged += 1
        scores.append(float(values["improvement_pct"]))
    return {
        "shared_metrics": len(metric_deltas),
        "improved": improved,
        "regressed": regressed,
        "unchanged": unchanged,
        "net_improvement_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
    }


def _rank_metric_changes(
    metric_deltas: dict[str, dict[str, float | str]],
    *,
    improved: bool,
) -> list[dict[str, float | str]]:
    ranked: list[dict[str, float | str]] = []
    for metric, values in metric_deltas.items():
        improvement = float(values["improvement"])
        if improved and improvement <= 0.0:
            continue
        if not improved and improvement >= 0.0:
            continue
        ranked.append(
            {
                "metric": metric,
                "improvement": round(improvement, 4),
                "improvement_pct": round(float(values["improvement_pct"]), 4),
                "baseline": round(float(values["baseline"]), 4),
                "candidate": round(float(values["candidate"]), 4),
            }
        )
    return sorted(
        ranked,
        key=lambda item: abs(float(item["improvement_pct"])),
        reverse=True,
    )


def _delta_block(
    baseline: float,
    candidate: float,
    *,
    direction: str,
) -> dict[str, float | str]:
    delta = candidate - baseline
    improvement = candidate - baseline if direction == "higher_is_better" else baseline - candidate
    return {
        "baseline": round(baseline, 4),
        "candidate": round(candidate, 4),
        "delta": round(delta, 4),
        "delta_pct": _percent_delta(baseline, candidate),
        "improvement": round(improvement, 4),
        "improvement_pct": _percent_delta(baseline, baseline + improvement),
        "direction": direction,
    }


def _percent_delta(baseline: float, candidate: float) -> float:
    if abs(baseline) <= 1e-9:
        return 0.0
    return round(((candidate - baseline) / baseline) * 100.0, 4)


def _metric_direction(metric: str) -> str:
    if metric in {
        "frame_count",
        "pair_count",
        "sample_count",
    }:
        return "neutral"
    return "lower_is_better"
