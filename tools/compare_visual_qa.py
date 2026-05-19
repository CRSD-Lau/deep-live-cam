"""Summarize or compare Deep-Live-Cam visual QA metadata exports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.visual_qa_report import (
    compare_visual_qa,
    format_visual_qa_comparison,
    format_visual_qa_summary,
    load_visual_qa_metadata,
    summarize_visual_qa,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize or compare visual/temporal QA metadata JSON files."
    )
    parser.add_argument("--input", help="single visual QA metadata JSON to summarize")
    parser.add_argument("--baseline", help="baseline visual QA metadata JSON")
    parser.add_argument("--candidate", help="candidate visual QA metadata JSON")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    parser.add_argument("--output", help="optional output report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.input and (args.baseline or args.candidate):
        print("--input cannot be combined with --baseline/--candidate", file=sys.stderr)
        return 2
    if args.input:
        result = summarize_visual_qa(load_visual_qa_metadata(args.input))
        text = (
            json.dumps(result, indent=2, sort_keys=True)
            if args.format == "json"
            else format_visual_qa_summary(result)
        )
        _emit(text, args.output)
        return 0
    if not args.baseline or not args.candidate:
        print("Use --input or both --baseline and --candidate", file=sys.stderr)
        return 2

    result = compare_visual_qa(
        load_visual_qa_metadata(args.baseline),
        load_visual_qa_metadata(args.candidate),
    )
    text = (
        json.dumps(result, indent=2, sort_keys=True)
        if args.format == "json"
        else format_visual_qa_comparison(result)
    )
    _emit(text, args.output)
    return 0


def _emit(text: str, output_path: str | None) -> None:
    if output_path:
        Path(output_path).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    raise SystemExit(main())
