"""Summarize or compare Deep-Live-Cam benchmark JSONL exports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.benchmark_report import (
    compare_benchmarks,
    format_benchmark_comparison,
    format_benchmark_summary,
    load_benchmark_jsonl,
    summarize_benchmark,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize or compare --benchmark-output JSONL files."
    )
    parser.add_argument("--input", help="single benchmark JSONL file to summarize")
    parser.add_argument("--baseline", help="baseline benchmark JSONL file")
    parser.add_argument("--candidate", help="candidate benchmark JSONL file")
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
        result = summarize_benchmark(load_benchmark_jsonl(args.input))
        text = (
            json.dumps(result, indent=2, sort_keys=True)
            if args.format == "json"
            else format_benchmark_summary(result)
        )
        _emit(text, args.output)
        return 0
    if not args.baseline or not args.candidate:
        print("Use --input or both --baseline and --candidate", file=sys.stderr)
        return 2

    result = compare_benchmarks(
        load_benchmark_jsonl(args.baseline),
        load_benchmark_jsonl(args.candidate),
    )
    text = (
        json.dumps(result, indent=2, sort_keys=True)
        if args.format == "json"
        else format_benchmark_comparison(result)
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
