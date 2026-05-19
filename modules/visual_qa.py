"""Visual QA export helpers for before/after render comparisons."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np


@dataclass(frozen=True)
class VisualQAExport:
    output_dir: Path
    paths: dict[str, Path]
    metrics: dict[str, Any]


@dataclass(frozen=True)
class TemporalQAExport:
    output_dir: Path
    paths: dict[str, Path]
    metrics: dict[str, Any]


def parse_frame_selection(value: str | None) -> set[int]:
    """Parse comma-separated zero-based frame indices."""
    if value is None:
        return set()
    if not value.strip():
        raise ValueError("frame selection cannot be blank")

    frame_indices: set[int] = set()
    for token in value.split(","):
        token = token.strip()
        if not token:
            raise ValueError("frame selection contains a blank index")
        try:
            frame_index = int(token)
        except ValueError as exc:
            raise ValueError(f"invalid frame index: {token}") from exc
        if frame_index < 0:
            raise ValueError(f"frame index must be zero or greater: {frame_index}")
        frame_indices.add(frame_index)
    return frame_indices


class VisualQACaptureSession:
    """Opt-in visual QA capture for selected pipeline frames."""

    def __init__(
        self,
        output_dir: str | Path,
        frame_indices: Iterable[int],
        *,
        stem: str = "frame",
        notes: dict[str, Any] | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.frame_indices = set(frame_indices)
        self.stem = stem
        self.notes = dict(notes or {})

    def should_capture(self, frame_index: int) -> bool:
        return frame_index in self.frame_indices

    def capture(
        self,
        frame_index: int,
        before_frame: np.ndarray,
        after_frame: np.ndarray,
    ) -> VisualQAExport:
        notes = dict(self.notes)
        notes["frame_index"] = frame_index
        return export_visual_qa(
            before_frame,
            after_frame,
            self.output_dir,
            stem=f"{self.stem}_{frame_index:06d}",
            notes=notes,
        )


class TemporalQACaptureSession:
    """Opt-in temporal QA capture for selected processed frames."""

    def __init__(
        self,
        output_dir: str | Path,
        frame_indices: Iterable[int],
        *,
        stem: str = "temporal",
        notes: dict[str, Any] | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.frame_indices = set(frame_indices)
        self.stem = stem
        self.notes = dict(notes or {})
        self._frames: list[np.ndarray] = []
        self._captured_frame_indices: list[int] = []

    @property
    def captured_frame_indices(self) -> list[int]:
        return list(self._captured_frame_indices)

    def should_capture(self, frame_index: int) -> bool:
        return frame_index in self.frame_indices

    def capture(self, frame_index: int, frame: np.ndarray) -> None:
        if not self.should_capture(frame_index):
            return
        self._frames.append(_as_bgr_uint8(frame))
        self._captured_frame_indices.append(frame_index)

    def export(self) -> TemporalQAExport | None:
        if not self._frames:
            return None
        notes = dict(self.notes)
        notes["frame_indices"] = sorted(self.frame_indices)
        notes["captured_frame_indices"] = self.captured_frame_indices
        return export_temporal_qa(
            self._frames,
            self.output_dir,
            stem=self.stem,
            notes=notes,
        )


def compute_image_metrics(before: np.ndarray, after: np.ndarray) -> dict[str, Any]:
    """Compute simple pixel-difference metrics after size-normalising frames."""
    before_u8 = _as_bgr_uint8(before)
    after_u8 = _resize_like(_as_bgr_uint8(after), before_u8)
    diff = after_u8.astype(np.int16) - before_u8.astype(np.int16)
    abs_diff = np.abs(diff)
    squared = diff.astype(np.float32) ** 2
    gray_abs_diff = cv2.cvtColor(abs_diff.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    lab_abs_diff = _lab_abs_diff(before_u8, after_u8)
    return {
        "before_shape": list(before_u8.shape),
        "after_shape": list(_as_bgr_uint8(after).shape),
        "comparison_shape": list(after_u8.shape),
        "mae": round(float(abs_diff.mean()), 4),
        "rmse": round(float(np.sqrt(squared.mean())), 4),
        "max_abs_diff": int(abs_diff.max()) if abs_diff.size else 0,
        "p95_abs_diff": _percentile(gray_abs_diff, 95),
        "p99_abs_diff": _percentile(gray_abs_diff, 99),
        "changed_pixel_ratio_5": _changed_pixel_ratio(gray_abs_diff, threshold=5),
        "changed_pixel_ratio_15": _changed_pixel_ratio(gray_abs_diff, threshold=15),
        "luma_mae": round(float(lab_abs_diff[:, :, 0].mean()), 4),
        "chroma_mae": round(float(lab_abs_diff[:, :, 1:].mean()), 4),
        "edge_mae": _edge_mae(before_u8, after_u8),
        "mean_abs_bgr": [
            round(float(value), 4)
            for value in abs_diff.reshape(-1, 3).mean(axis=0)
        ],
    }


def compute_temporal_consistency_metrics(
    frames: Iterable[np.ndarray],
) -> dict[str, Any]:
    """Compute frame-to-frame flicker and edge-jitter metrics for a sequence."""
    prepared = _prepare_frame_sequence(frames)
    pair_metrics: list[dict[str, Any]] = []
    for index, (before, after) in enumerate(zip(prepared, prepared[1:])):
        metrics = compute_image_metrics(before, after)
        pair_metrics.append(
            {
                "pair_index": index,
                "from_frame": index,
                "to_frame": index + 1,
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "luma_mae": metrics["luma_mae"],
                "chroma_mae": metrics["chroma_mae"],
                "edge_mae": metrics["edge_mae"],
                "changed_pixel_ratio_15": metrics["changed_pixel_ratio_15"],
            }
        )

    return {
        "frame_count": len(prepared),
        "pair_count": len(pair_metrics),
        "frame_shape": list(prepared[0].shape) if prepared else None,
        "mean_pair_mae": _metric_mean(pair_metrics, "mae"),
        "p95_pair_mae": _metric_percentile(pair_metrics, "mae", 95),
        "max_pair_mae": _metric_max(pair_metrics, "mae"),
        "mean_luma_mae": _metric_mean(pair_metrics, "luma_mae"),
        "mean_chroma_mae": _metric_mean(pair_metrics, "chroma_mae"),
        "mean_edge_mae": _metric_mean(pair_metrics, "edge_mae"),
        "p95_edge_mae": _metric_percentile(pair_metrics, "edge_mae", 95),
        "max_changed_pixel_ratio_15": _metric_max(
            pair_metrics,
            "changed_pixel_ratio_15",
        ),
        "pairs": pair_metrics,
    }


def create_side_by_side(
    before: np.ndarray,
    after: np.ndarray,
    *,
    before_label: str = "Before",
    after_label: str = "After",
    label_height: int = 34,
    separator_width: int = 6,
) -> np.ndarray:
    """Create a BGR before/after comparison panel."""
    before_u8 = _as_bgr_uint8(before)
    after_u8 = _fit_to_height(_as_bgr_uint8(after), before_u8.shape[0])
    separator = np.full(
        (before_u8.shape[0], separator_width, 3),
        18,
        dtype=np.uint8,
    )
    panel = np.hstack([before_u8, separator, after_u8])
    if label_height <= 0:
        return panel

    label_band = np.full((label_height, panel.shape[1], 3), 24, dtype=np.uint8)
    _draw_label(label_band, before_label, 10, label_height - 11)
    after_x = before_u8.shape[1] + separator_width + 10
    _draw_label(label_band, after_label, after_x, label_height - 11)
    return np.vstack([label_band, panel])


def create_difference_heatmap(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    """Create a BGR heatmap showing per-pixel absolute difference."""
    before_u8 = _as_bgr_uint8(before)
    after_u8 = _resize_like(_as_bgr_uint8(after), before_u8)
    gray = cv2.cvtColor(cv2.absdiff(before_u8, after_u8), cv2.COLOR_BGR2GRAY)
    if gray.max() > 0:
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    return cv2.applyColorMap(gray.astype(np.uint8), cv2.COLORMAP_INFERNO)


def create_edge_map(image: np.ndarray) -> np.ndarray:
    """Create a BGR visualization of frame edge magnitude."""
    edges = _edge_magnitude(_as_bgr_uint8(image))
    edge_u8 = _normalize_to_uint8(edges)
    return cv2.cvtColor(edge_u8, cv2.COLOR_GRAY2BGR)


def create_edge_difference_heatmap(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    """Create a BGR heatmap showing edge-energy changes between frames."""
    before_u8 = _as_bgr_uint8(before)
    after_u8 = _resize_like(_as_bgr_uint8(after), before_u8)
    edge_delta = np.abs(_edge_magnitude(after_u8) - _edge_magnitude(before_u8))
    return cv2.applyColorMap(_normalize_to_uint8(edge_delta), cv2.COLORMAP_TURBO)


def create_temporal_flicker_heatmap(frames: Iterable[np.ndarray]) -> np.ndarray:
    """Create an aggregate heatmap of frame-to-frame luma changes."""
    prepared = _prepare_frame_sequence(frames)
    if not prepared:
        raise ValueError("expected at least one frame")
    if len(prepared) == 1:
        return np.zeros_like(prepared[0])

    accumulator = np.zeros(prepared[0].shape[:2], dtype=np.float32)
    for before, after in zip(prepared, prepared[1:]):
        gray_delta = cv2.cvtColor(cv2.absdiff(before, after), cv2.COLOR_BGR2GRAY)
        accumulator += gray_delta.astype(np.float32)
    accumulator /= max(1, len(prepared) - 1)
    return cv2.applyColorMap(_normalize_to_uint8(accumulator), cv2.COLORMAP_INFERNO)


def create_temporal_edge_jitter_heatmap(frames: Iterable[np.ndarray]) -> np.ndarray:
    """Create an aggregate heatmap of frame-to-frame edge-energy changes."""
    prepared = _prepare_frame_sequence(frames)
    if not prepared:
        raise ValueError("expected at least one frame")
    if len(prepared) == 1:
        return np.zeros_like(prepared[0])

    accumulator = np.zeros(prepared[0].shape[:2], dtype=np.float32)
    for before, after in zip(prepared, prepared[1:]):
        accumulator += np.abs(_edge_magnitude(after) - _edge_magnitude(before))
    accumulator /= max(1, len(prepared) - 1)
    return cv2.applyColorMap(_normalize_to_uint8(accumulator), cv2.COLORMAP_TURBO)


def export_visual_qa(
    before: np.ndarray,
    after: np.ndarray,
    output_dir: str | Path,
    *,
    stem: str = "comparison",
    notes: dict[str, Any] | None = None,
) -> VisualQAExport:
    """Export snapshots, side-by-side panel, diff heatmap, and JSON metadata."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    before_u8 = _as_bgr_uint8(before)
    after_u8 = _as_bgr_uint8(after)
    side_by_side = create_side_by_side(before_u8, after_u8)
    heatmap = create_difference_heatmap(before_u8, after_u8)
    before_edge_map = create_edge_map(before_u8)
    after_edge_map = create_edge_map(after_u8)
    edge_difference_heatmap = create_edge_difference_heatmap(before_u8, after_u8)
    metrics = compute_image_metrics(before_u8, after_u8)

    paths = {
        "before": output_path / f"{stem}_before.png",
        "after": output_path / f"{stem}_after.png",
        "side_by_side": output_path / f"{stem}_side_by_side.png",
        "difference_heatmap": output_path / f"{stem}_difference_heatmap.png",
        "before_edges": output_path / f"{stem}_before_edges.png",
        "after_edges": output_path / f"{stem}_after_edges.png",
        "edge_difference_heatmap": output_path / f"{stem}_edge_difference_heatmap.png",
        "metadata": output_path / f"{stem}_metadata.json",
    }
    _write_image(paths["before"], before_u8)
    _write_image(paths["after"], after_u8)
    _write_image(paths["side_by_side"], side_by_side)
    _write_image(paths["difference_heatmap"], heatmap)
    _write_image(paths["before_edges"], before_edge_map)
    _write_image(paths["after_edges"], after_edge_map)
    _write_image(paths["edge_difference_heatmap"], edge_difference_heatmap)

    metadata = {
        "stem": stem,
        "files": {key: str(path) for key, path in paths.items() if key != "metadata"},
        "metrics": metrics,
        "notes": notes or {},
    }
    paths["metadata"].write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return VisualQAExport(output_path, paths, metrics)


def export_temporal_qa(
    frames: Iterable[np.ndarray],
    output_dir: str | Path,
    *,
    stem: str = "temporal",
    notes: dict[str, Any] | None = None,
) -> TemporalQAExport:
    """Export sequence-level flicker/jitter heatmaps and JSON metrics."""
    prepared = _prepare_frame_sequence(frames)
    if not prepared:
        raise ValueError("expected at least one frame")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    metrics = compute_temporal_consistency_metrics(prepared)
    paths = {
        "temporal_flicker_heatmap": output_path / f"{stem}_flicker_heatmap.png",
        "temporal_edge_jitter_heatmap": output_path / f"{stem}_edge_jitter_heatmap.png",
        "metadata": output_path / f"{stem}_temporal_metadata.json",
    }
    _write_image(paths["temporal_flicker_heatmap"], create_temporal_flicker_heatmap(prepared))
    _write_image(
        paths["temporal_edge_jitter_heatmap"],
        create_temporal_edge_jitter_heatmap(prepared),
    )

    metadata = {
        "stem": stem,
        "files": {key: str(path) for key, path in paths.items() if key != "metadata"},
        "metrics": metrics,
        "notes": notes or {},
    }
    paths["metadata"].write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return TemporalQAExport(output_path, paths, metrics)


def _as_bgr_uint8(image: np.ndarray) -> np.ndarray:
    if image is None or not hasattr(image, "shape"):
        raise ValueError("expected an image array")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError(f"expected BGR/BGRA image, got shape {image.shape}")
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    if image.dtype == np.uint8:
        return image.copy()
    return np.clip(image, 0, 255).astype(np.uint8)


def _fit_to_height(image: np.ndarray, height: int) -> np.ndarray:
    if image.shape[0] == height:
        return image.copy()
    scale = height / image.shape[0]
    width = max(1, int(round(image.shape[1] * scale)))
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def _resize_like(image: np.ndarray, reference: np.ndarray) -> np.ndarray:
    if image.shape[:2] == reference.shape[:2]:
        return image.copy()
    return cv2.resize(
        image,
        (reference.shape[1], reference.shape[0]),
        interpolation=cv2.INTER_AREA,
    )


def _prepare_frame_sequence(frames: Iterable[np.ndarray]) -> list[np.ndarray]:
    prepared: list[np.ndarray] = []
    reference: np.ndarray | None = None
    for frame in frames:
        frame_u8 = _as_bgr_uint8(frame)
        if reference is None:
            reference = frame_u8
            prepared.append(frame_u8)
        else:
            prepared.append(_resize_like(frame_u8, reference))
    return prepared


def _lab_abs_diff(before_u8: np.ndarray, after_u8: np.ndarray) -> np.ndarray:
    before_lab = cv2.cvtColor(before_u8, cv2.COLOR_BGR2LAB).astype(np.int16)
    after_lab = cv2.cvtColor(after_u8, cv2.COLOR_BGR2LAB).astype(np.int16)
    return np.abs(after_lab - before_lab)


def _edge_mae(before_u8: np.ndarray, after_u8: np.ndarray) -> float:
    before_edges = _edge_magnitude(before_u8)
    after_edges = _edge_magnitude(after_u8)
    return round(float(np.abs(after_edges - before_edges).mean()), 4)


def _edge_magnitude(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    return cv2.magnitude(grad_x, grad_y)


def _normalize_to_uint8(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return np.zeros(values.shape, dtype=np.uint8)
    max_value = float(values.max())
    if max_value <= 1e-6:
        return np.zeros(values.shape, dtype=np.uint8)
    return np.clip(values * (255.0 / max_value), 0, 255).astype(np.uint8)


def _changed_pixel_ratio(gray_abs_diff: np.ndarray, *, threshold: int) -> float:
    if gray_abs_diff.size == 0:
        return 0.0
    ratio = np.count_nonzero(gray_abs_diff > int(threshold)) / gray_abs_diff.size
    return round(float(ratio), 6)


def _percentile(values: np.ndarray, percentile: float) -> float:
    if values.size == 0:
        return 0.0
    return round(float(np.percentile(values, percentile)), 4)


def _metric_values(records: list[dict[str, Any]], key: str) -> np.ndarray:
    if not records:
        return np.array([], dtype=np.float32)
    return np.array([float(record[key]) for record in records], dtype=np.float32)


def _metric_mean(records: list[dict[str, Any]], key: str) -> float:
    values = _metric_values(records, key)
    if values.size == 0:
        return 0.0
    return round(float(values.mean()), 4)


def _metric_max(records: list[dict[str, Any]], key: str) -> float:
    values = _metric_values(records, key)
    if values.size == 0:
        return 0.0
    return round(float(values.max()), 4)


def _metric_percentile(
    records: list[dict[str, Any]],
    key: str,
    percentile: float,
) -> float:
    values = _metric_values(records, key)
    return _percentile(values, percentile)


def _draw_label(image: np.ndarray, label: str, x: int, y: int) -> None:
    cv2.putText(
        image,
        label,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (230, 230, 230),
        1,
        cv2.LINE_AA,
    )


def _write_image(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image):
        raise OSError(f"failed to write image: {path}")
