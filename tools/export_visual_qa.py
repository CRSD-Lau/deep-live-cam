"""Export visual QA artifacts for two render frames/images."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.visual_qa import export_visual_qa


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create before/after snapshots, a side-by-side comparison, "
            "difference heatmaps, edge maps, and JSON metrics."
        )
    )
    parser.add_argument("--before", required=True, help="path to baseline frame/image")
    parser.add_argument("--after", required=True, help="path to processed frame/image")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="directory for QA exports",
    )
    parser.add_argument(
        "--stem",
        default="comparison",
        help="filename stem for exported artifacts",
    )
    parser.add_argument(
        "--quality-mode",
        help="optional quality mode label stored in metadata",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    before = cv2.imread(args.before)
    after = cv2.imread(args.after)
    if before is None:
        print(f"Could not read --before image: {args.before}", file=sys.stderr)
        return 2
    if after is None:
        print(f"Could not read --after image: {args.after}", file=sys.stderr)
        return 2

    notes = {}
    if args.quality_mode:
        notes["quality_mode"] = args.quality_mode
    result = export_visual_qa(
        before,
        after,
        args.output_dir,
        stem=args.stem,
        notes=notes,
    )
    print(f"Visual QA export written to {result.output_dir}")
    print(
        f"MAE={result.metrics['mae']:.4f} "
        f"RMSE={result.metrics['rmse']:.4f} "
        f"LumaMAE={result.metrics['luma_mae']:.4f} "
        f"ChromaMAE={result.metrics['chroma_mae']:.4f} "
        f"EdgeMAE={result.metrics['edge_mae']:.4f}"
    )
    for key, path in result.paths.items():
        print(f"{key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
