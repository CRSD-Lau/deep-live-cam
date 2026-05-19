"""Export temporal QA artifacts for a rendered frame sequence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.visual_qa import export_temporal_qa


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create temporal flicker and edge-jitter heatmaps plus JSON "
            "frame-to-frame consistency metrics."
        )
    )
    parser.add_argument(
        "--frames",
        nargs="+",
        required=True,
        help="ordered frame/image paths to analyze",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="directory for temporal QA exports",
    )
    parser.add_argument(
        "--stem",
        default="temporal",
        help="filename stem for exported artifacts",
    )
    parser.add_argument(
        "--quality-mode",
        help="optional quality mode label stored in metadata",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frames = []
    for frame_path in args.frames:
        frame = cv2.imread(frame_path)
        if frame is None:
            print(f"Could not read frame image: {frame_path}", file=sys.stderr)
            return 2
        frames.append(frame)

    notes = {}
    if args.quality_mode:
        notes["quality_mode"] = args.quality_mode
    result = export_temporal_qa(
        frames,
        args.output_dir,
        stem=args.stem,
        notes=notes,
    )
    print(f"Temporal QA export written to {result.output_dir}")
    print(
        f"frames={result.metrics['frame_count']} "
        f"pairs={result.metrics['pair_count']} "
        f"MeanMAE={result.metrics['mean_pair_mae']:.4f} "
        f"P95MAE={result.metrics['p95_pair_mae']:.4f} "
        f"MeanEdgeMAE={result.metrics['mean_edge_mae']:.4f}"
    )
    for key, path in result.paths.items():
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
