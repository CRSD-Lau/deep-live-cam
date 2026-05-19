"""Small runtime metrics helpers for live/video pipeline benchmarking."""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Iterator


@dataclass
class StageStats:
    count: int = 0
    total_seconds: float = 0.0
    min_seconds: float | None = None
    max_seconds: float | None = None
    recent_seconds: deque[float] = field(
        default_factory=lambda: deque(maxlen=512),
        repr=False,
    )

    def observe(self, seconds: float) -> None:
        seconds = max(0.0, float(seconds))
        self.count += 1
        self.total_seconds += seconds
        self.min_seconds = seconds if self.min_seconds is None else min(self.min_seconds, seconds)
        self.max_seconds = seconds if self.max_seconds is None else max(self.max_seconds, seconds)
        self.recent_seconds.append(seconds)

    @property
    def avg_ms(self) -> float:
        if self.count == 0:
            return 0.0
        return round((self.total_seconds / self.count) * 1000.0, 3)

    @property
    def min_ms(self) -> float:
        return round((self.min_seconds or 0.0) * 1000.0, 3)

    @property
    def max_ms(self) -> float:
        return round((self.max_seconds or 0.0) * 1000.0, 3)

    @property
    def p95_ms(self) -> float:
        return _percentile_seconds(self.recent_seconds, 95)

    @property
    def p99_ms(self) -> float:
        return _percentile_seconds(self.recent_seconds, 99)


@dataclass
class ValueStats:
    count: int = 0
    total: float = 0.0
    min_value: float | None = None
    max_value: float | None = None
    recent_values: deque[float] = field(
        default_factory=lambda: deque(maxlen=512),
        repr=False,
    )

    def observe(self, value: float) -> None:
        value = max(0.0, float(value))
        self.count += 1
        self.total += value
        self.min_value = value if self.min_value is None else min(self.min_value, value)
        self.max_value = value if self.max_value is None else max(self.max_value, value)
        self.recent_values.append(value)

    @property
    def avg(self) -> float:
        if self.count == 0:
            return 0.0
        return round(self.total / self.count, 3)

    @property
    def min(self) -> float:
        return round(self.min_value or 0.0, 3)

    @property
    def max(self) -> float:
        return round(self.max_value or 0.0, 3)

    @property
    def p95(self) -> float:
        return _percentile_values(self.recent_values, 95)

    @property
    def p99(self) -> float:
        return _percentile_values(self.recent_values, 99)


class PipelineMetrics:
    def __init__(self, name: str) -> None:
        self.name = name
        self.started_at = time.perf_counter()
        self.last_report_at = self.started_at
        self.frames = 0
        self.dropped_frames = 0
        self._drop_lock = threading.Lock()
        self._drop_reasons: dict[str, int] = {}
        self._stages: dict[str, StageStats] = {}
        self._queues: dict[str, ValueStats] = {}

    def observe(self, stage: str, seconds: float) -> None:
        self._stages.setdefault(stage, StageStats()).observe(seconds)

    def observe_queue_depth(self, name: str, depth: int | float) -> None:
        self._queues.setdefault(name, ValueStats()).observe(depth)

    @contextmanager
    def track(self, stage: str) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self.observe(stage, time.perf_counter() - started)

    def frame_complete(self) -> None:
        self.frames += 1

    def drop_frames(self, reason: str, count: int) -> None:
        count = max(0, int(count))
        if count == 0:
            return
        reason = str(reason or "unspecified")
        with self._drop_lock:
            self.dropped_frames += count
            self._drop_reasons[reason] = self._drop_reasons.get(reason, 0) + count

    def drop_frame(self, reason: str = "unspecified") -> None:
        self.drop_frames(reason, 1)

    @property
    def elapsed_seconds(self) -> float:
        return max(time.perf_counter() - self.started_at, 1e-9)

    @property
    def fps(self) -> float:
        return self.frames / self.elapsed_seconds

    def should_report(self, interval_seconds: float) -> bool:
        return time.perf_counter() - self.last_report_at >= max(0.5, interval_seconds)

    def mark_reported(self) -> None:
        self.last_report_at = time.perf_counter()

    def stage_snapshot(self) -> dict[str, dict[str, float | int]]:
        return {
            name: {
                "count": stats.count,
                "avg_ms": stats.avg_ms,
                "min_ms": stats.min_ms,
                "max_ms": stats.max_ms,
                "p95_ms": stats.p95_ms,
                "p99_ms": stats.p99_ms,
                "sample_count": len(stats.recent_seconds),
            }
            for name, stats in sorted(self._stages.items())
        }

    def drop_summary(self) -> tuple[int, dict[str, int]]:
        with self._drop_lock:
            return self.dropped_frames, dict(sorted(self._drop_reasons.items()))

    def drop_snapshot(self) -> dict[str, int]:
        return self.drop_summary()[1]

    def queue_snapshot(self) -> dict[str, dict[str, float | int]]:
        return {
            name: {
                "count": stats.count,
                "avg_depth": stats.avg,
                "min_depth": stats.min,
                "max_depth": stats.max,
                "p95_depth": stats.p95,
                "p99_depth": stats.p99,
                "sample_count": len(stats.recent_values),
            }
            for name, stats in sorted(self._queues.items())
        }


def metrics_snapshot(
    metrics: PipelineMetrics,
    *,
    event: str = "snapshot",
    include_vram: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable benchmark snapshot."""
    dropped_frames, drop_reasons = metrics.drop_summary()
    snapshot: dict[str, Any] = {
        "event": event,
        "name": metrics.name,
        "timestamp_unix": round(time.time(), 6),
        "elapsed_seconds": round(metrics.elapsed_seconds, 6),
        "frames": metrics.frames,
        "fps": round(metrics.fps, 4),
        "dropped_frames": dropped_frames,
        "drop_reasons": drop_reasons,
        "stages": metrics.stage_snapshot(),
        "queues": metrics.queue_snapshot(),
    }
    if include_vram:
        vram = gpu_memory_snapshot_mb()
        if vram:
            snapshot["vram_mb"] = vram
    if extra:
        snapshot["context"] = _json_safe(extra)
    return snapshot


class MetricsJsonlWriter:
    """Append benchmark snapshots as JSONL records."""

    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)
        if self.output_path.parent != Path("."):
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        metrics: PipelineMetrics,
        *,
        event: str = "snapshot",
        include_vram: bool = True,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = metrics_snapshot(
            metrics,
            event=event,
            include_vram=include_vram,
            extra=extra,
        )
        with self.output_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(snapshot, sort_keys=True) + "\n")
        return snapshot


def safe_write_metrics_snapshot(
    writer: MetricsJsonlWriter | None,
    metrics: PipelineMetrics,
    *,
    event: str,
    extra: dict[str, Any] | None = None,
) -> None:
    if writer is None:
        return
    try:
        writer.write(metrics, event=event, extra=extra)
    except Exception as exc:
        print(f"[benchmark:{metrics.name}] failed to write JSONL snapshot: {exc}", flush=True)


def gpu_memory_snapshot_mb() -> dict[str, int]:
    try:
        import torch

        if not torch.cuda.is_available():
            return {}
        return {
            "cuda_allocated": int(torch.cuda.memory_allocated() / (1024 * 1024)),
            "cuda_reserved": int(torch.cuda.memory_reserved() / (1024 * 1024)),
            "cuda_max_allocated": int(torch.cuda.max_memory_allocated() / (1024 * 1024)),
        }
    except Exception:
        return {}


def format_metrics(metrics: PipelineMetrics, *, include_vram: bool = True) -> str:
    dropped_frames, drop_reasons = metrics.drop_summary()
    stage_parts = [
        f"{name}={values['avg_ms']:.2f}ms p95={values['p95_ms']:.2f}ms"
        for name, values in metrics.stage_snapshot().items()
    ]
    queue_parts = [
        f"{name}=avg {values['avg_depth']:.2f} max {values['max_depth']:.0f}"
        for name, values in metrics.queue_snapshot().items()
    ]
    parts = [
        f"[benchmark:{metrics.name}]",
        f"frames={metrics.frames}",
        f"fps={metrics.fps:.2f}",
    ]
    if dropped_frames:
        dropped = f"dropped={dropped_frames}"
        if drop_reasons:
            dropped += " (" + ", ".join(
                f"{reason}={count}" for reason, count in drop_reasons.items()
            ) + ")"
        parts.append(dropped)
    if stage_parts:
        parts.append("stages: " + ", ".join(stage_parts))
    if queue_parts:
        parts.append("queues: " + ", ".join(queue_parts))
    if include_vram:
        vram = gpu_memory_snapshot_mb()
        if vram:
            parts.append(
                "vram: "
                + ", ".join(f"{key}={value}MB" for key, value in vram.items())
            )
    return " | ".join(parts)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _percentile_seconds(values: deque[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * (float(percentile) / 100.0)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    value = ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction
    return round(value * 1000.0, 3)


def _percentile_values(values: deque[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * (float(percentile) / 100.0)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    value = ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction
    return round(value, 3)
