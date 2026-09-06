#!/usr/bin/env python3
"""Summarize manual Windows release gates and latest evidence packets."""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path


GATES = (
    (
        "Clean Windows VM",
        "CLEAN_VM_VERIFICATION.md",
        "build/windows/manual-evidence/clean-vm",
    ),
    (
        "OBS Virtual Camera",
        "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
        "build/windows/manual-evidence/obs-virtualcam",
    ),
    (
        "Legal Review",
        "LEGAL_REVIEW.md",
        "build/windows/manual-evidence/legal-review",
    ),
    ("Real model download", "MODEL_DOWNLOAD_VERIFICATION.md", ""),
    ("CPU/CUDA processing", "PROCESSING_VERIFICATION.md", ""),
)


@dataclass(frozen=True)
class GateSummary:
    name: str
    path: str
    status: str
    open_items: list[str]
    latest_evidence: str
    release_version: str = ""
    app_version: str = ""

    @property
    def failures(self) -> list[str]:
        return gate_failures(
            self.status, self.release_version, self.app_version, len(self.open_items)
        )

    @property
    def passed(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": self.path,
            "status": self.status,
            "open_items": self.open_items,
            "open_item_count": len(self.open_items),
            "latest_evidence": self.latest_evidence,
            "release_version": self.release_version,
            "app_version": self.app_version,
            "failures": self.failures,
            "passed": self.passed,
        }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def evidence_field(text: str, field: str) -> str:
    """Require one unambiguous top-level field, rather than old copied verdicts."""
    values = re.findall(
        rf"^{re.escape(field)}:[ \t]*([^\r\n]*)$",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    return values[0].strip() if len(values) == 1 else ""


def gate_status(text: str, exists: bool) -> str:
    if not exists:
        return "MISSING"
    return evidence_field(text, "Status").upper() or "UNKNOWN"


def gate_release_version(text: str) -> str:
    value = evidence_field(text, "Release")
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1].strip()
    return value


def gate_failures(
    status: str, release_version: str, app_version: str, open_item_count: int,
) -> list[str]:
    failures = []
    if status != "PASS":
        failures.append(f"status is `{status}`; expected explicit `PASS`.")
    if open_item_count:
        failures.append(f"has {open_item_count} open checklist item(s).")
    if not app_version:
        failures.append(
            "requested app version is missing; provide --app-version or "
            "a literal version in modules/metadata.py."
        )
    elif not release_version:
        failures.append(f"Release version is missing or ambiguous; expected `{app_version}`.")
    elif release_version != app_version:
        failures.append(
            f"Release version `{release_version}` does not match "
            f"requested app version `{app_version}`."
        )
    return failures


def infer_app_version(repo_root: Path) -> str:
    """Read the declared version without importing or executing repository code."""
    try:
        tree = ast.parse(read_text(repo_root / "modules/metadata.py"))
        declarations = [
            node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "version" for target in node.targets)
        ]
    except (OSError, SyntaxError):
        return ""
    if (
        len(declarations) != 1
        or not isinstance(declarations[0], ast.Constant)
        or not isinstance(declarations[0].value, str)
    ):
        return ""
    return declarations[0].value.strip()


def open_checklist_items(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        checklist_prefix = r"^\s*(?:[-+*]|\d+[.)])\s+\[\s\]\s*"
        if re.match(checklist_prefix, line):
            items.append(re.sub(checklist_prefix, "", line).strip())
    return items


def latest_evidence(repo_root: Path, evidence_dir: str) -> str:
    if not evidence_dir:
        return ""
    directory = repo_root / evidence_dir
    if not directory.exists():
        return ""
    candidates = [path for path in directory.glob("*.md") if path.is_file()]
    if not candidates:
        return ""
    latest = max(candidates, key=lambda path: (path.stat().st_mtime, path.name))
    return latest.relative_to(repo_root).as_posix()


def collect(repo_root: Path, app_version: str | None = None) -> list[GateSummary]:
    app_version = infer_app_version(repo_root) if app_version is None else app_version.strip()
    summaries: list[GateSummary] = []
    for name, gate_path, evidence_dir in GATES:
        path = repo_root / gate_path
        text = read_text(path)
        summaries.append(
            GateSummary(
                name=name,
                path=gate_path,
                status=gate_status(text, path.is_file()),
                open_items=open_checklist_items(text),
                latest_evidence=latest_evidence(repo_root, evidence_dir),
                release_version=gate_release_version(text),
                app_version=app_version,
            )
        )
    return summaries


def render_markdown(summaries: list[GateSummary]) -> str:
    lines = [
        "# Manual Windows Release Gate Summary",
        "",
        "This report is generated by `tools/summarize_manual_release_gates.py`.",
        "It does not approve the release; it shows which human gates still need",
        "completion before publishing.",
        "",
        f"Requested app version: `{summaries[0].app_version or 'MISSING'}`" if summaries else "Requested app version: `MISSING`",
        "",
        "## Status",
        "",
    ]
    for summary in summaries:
        marker = "PASS" if summary.passed else "BLOCKED"
        evidence = summary.latest_evidence or "none found"
        lines.append(f"- {marker}: `{summary.path}` status=`{summary.status}` release=`{summary.release_version or 'MISSING'}` open_items=`{len(summary.open_items)}` latest_evidence=`{evidence}`")
        for failure in summary.failures:
            lines.append(f"  - {failure}")

    lines.extend(["", "## Open Items", ""])
    any_open = False
    for summary in summaries:
        if summary.open_items:
            any_open = True
            lines.append(f"### {summary.name}")
            lines.append("")
            for item in summary.open_items:
                lines.append(f"- {item}")
            lines.append("")
    if not any_open:
        lines.append("- None.")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize manual Windows release gates.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--app-version", help="Required release version; defaults to the literal version in modules/metadata.py.")
    parser.add_argument("--output", help="Write markdown summary to this path.")
    parser.add_argument("--json-output", help="Write JSON summary to this path.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless every gate is PASS for the requested release with no open checklist items.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    summaries = collect(repo_root, args.app_version)
    markdown = render_markdown(summaries)
    print(markdown)

    if args.output:
        output = (repo_root / args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")

    if args.json_output:
        payload = {
            "app_version": summaries[0].app_version,
            "ready": all(summary.passed for summary in summaries),
            "gates": [summary.to_dict() for summary in summaries],
        }
        json_output = (repo_root / args.json_output).resolve()
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.strict and not all(summary.passed for summary in summaries):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
