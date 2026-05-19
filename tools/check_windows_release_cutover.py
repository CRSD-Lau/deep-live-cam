#!/usr/bin/env python3
"""Report whether the current worktree is ready for a Windows release cutover."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_RELEASE_PATHS = {
    ".github/workflows/windows-release.yml",
    ".gitignore",
    "CLEAN_VM_VERIFICATION.md",
    "CLEAN_RELEASE_WORKTREE_VERIFICATION.md",
    "COMPLIANCE.md",
    "DeepLiveCamStudio.pyw",
    "LEGAL_REVIEW.md",
    "MODEL_DOWNLOAD_VERIFICATION.md",
    "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
    "PROCESSING_VERIFICATION.md",
    "README.md",
    "RELEASE_CHECKLIST.md",
    "RELEASE_COMPLETION_AUDIT.md",
    "RELEASE_CUTOVER_PLAN.md",
    "RELEASE_CUTOVER_STATUS.md",
    "RELEASE_NOTES_TEMPLATE.md",
    "RELEASE_PUBLISH_HANDOFF.md",
    "RELEASE_REPORT.md",
    "RELEASE_SOURCE_PREP.md",
    "RELEASE_VERIFICATION.md",
    "THIRD_PARTY_NOTICES.md",
    "requirements.txt",
    "run.py",
    "tests/test_face_analyser_get_one_face.py",
    "tests/test_image_upload_formats.py",
    "tests/test_model_manager.py",
    "tests/test_validate_windows_release_artifacts.py",
    "tests/test_release_report.py",
    "tests/test_summarize_manual_release_gates.py",
    "tests/test_windows_release_scripts.py",
    "tests/test_windows_release_cutover.py",
    "tests/test_windows_release_verification.py",
    "tools/check_cuda_provider.py",
    "tools/check_obs_virtualcam.py",
    "tools/check_windows_release_cutover.py",
    "tools/collect_third_party_license_files.py",
    "tools/generate_python_dependency_licenses.py",
    "tools/generate_windows_bundle_manifest.py",
    "tools/generate_windows_release_verification.py",
    "tools/install_windows_desktop_app.ps1",
    "tools/prune_windows_dist.py",
    "tools/summarize_manual_release_gates.py",
    "tools/validate_windows_release_artifacts.py",
}

REQUIRED_RELEASE_PREFIXES = (
    "build/windows/",
    "docs/OBS_VIRTUAL_CAMERA.md",
    "LICENSES/",
    "modules/core.py",
    "modules/desktop_launcher.py",
    "modules/execution_providers.py",
    "modules/globals.py",
    "modules/model_manager.py",
    "modules/paths.py",
    "modules/processors/frame/_onnx_enhancer.py",
    "modules/processors/frame/core.py",
    "modules/processors/frame/face_enhancer.py",
    "modules/processors/frame/face_enhancer_gpen256.py",
    "modules/processors/frame/face_enhancer_gpen512.py",
    "modules/processors/frame/face_swapper.py",
    "modules/ui.py",
    "modules/utilities.py",
)

MIXED_SCOPE_PREFIXES = (
    ".superpowers/",
    "docs/ITERATION_LOG.md",
    "docs/superpowers/",
    "modules/benchmark_report.py",
    "modules/compositing/",
    "modules/diagnostics/",
    "modules/enhancement_registry.py",
    "modules/expression_regions.py",
    "modules/expression_stabilizer.py",
    "modules/expression_temporal.py",
    "modules/face_analyser.py",
    "modules/face_pose.py",
    "modules/live_queue.py",
    "modules/pipeline_metrics.py",
    "modules/processors/frame/face_masking.py",
    "modules/processors/frame/processor_dispatch.py",
    "modules/quality_profiles.py",
    "modules/temporal_smoothing.py",
    "modules/tracking/",
    "modules/visual_qa.py",
    "modules/visual_qa_report.py",
    "runtime/",
    "tests/test_benchmark_report.py",
    "tests/test_compositing_",
    "tests/test_desktop_launcher.py",
    "tests/test_diagnostic_overlays.py",
    "tests/test_enhancement_registry.py",
    "tests/test_execution_providers.py",
    "tests/test_expression_",
    "tests/test_face_masking_expression_regions.py",
    "tests/test_face_pose.py",
    "tests/test_face_swapper_expression_gate.py",
    "tests/test_face_swapper_lighting.py",
    "tests/test_face_swapper_mapping_faces.py",
    "tests/test_face_swapper_motion_feather.py",
    "tests/test_face_swapper_temporal_",
    "tests/test_face_track.py",
    "tests/test_live_queue.py",
    "tests/test_no_avatar_surface.py",
    "tests/test_pipeline_metrics.py",
    "tests/test_processor_dispatch.py",
    "tests/test_quality_profiles.py",
    "tests/test_temporal_smoothing.py",
    "tests/test_visual_qa",
    "tools/compare_benchmarks.py",
    "tools/compare_visual_qa.py",
    "tools/export_temporal_qa.py",
    "tools/export_visual_qa.py",
)

MANUAL_GATE_FILES = (
    "CLEAN_VM_VERIFICATION.md",
    "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
    "LEGAL_REVIEW.md",
)


class ManualGate:
    def __init__(self, path: str, status: str, open_items: int) -> None:
        self.path = path
        self.status = status
        self.open_items = open_items

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "status": self.status,
            "open_items": self.open_items,
            "passed": self.status == "PASS" and self.open_items == 0,
        }


class StatusEntry:
    def __init__(self, path: str, staged: bool, unstaged: bool) -> None:
        self.path = path
        self.staged = staged
        self.unstaged = unstaged


class CutoverStatus:
    def __init__(
        self,
        paths: list[str],
        release_paths: list[str],
        mixed_paths: list[str],
        unknown_paths: list[str],
        staged_release_paths: list[str],
        unstaged_release_paths: list[str],
        manual_gates: list[ManualGate],
        blockers: list[str],
        mixed_scope_is_blocking: bool,
    ) -> None:
        self.paths = paths
        self.release_paths = release_paths
        self.mixed_paths = mixed_paths
        self.unknown_paths = unknown_paths
        self.staged_release_paths = staged_release_paths
        self.unstaged_release_paths = unstaged_release_paths
        self.manual_gates = manual_gates
        self.blockers = blockers
        self.mixed_scope_is_blocking = mixed_scope_is_blocking

    def to_dict(self) -> dict[str, object]:
        return {
            "dirty_paths": self.paths,
            "release_paths": self.release_paths,
            "mixed_scope_paths": self.mixed_paths,
            "unknown_paths": self.unknown_paths,
            "staged_release_paths": self.staged_release_paths,
            "unstaged_release_paths": self.unstaged_release_paths,
            "manual_gates": [gate.to_dict() for gate in self.manual_gates],
            "blockers": self.blockers,
            "mixed_scope_is_blocking": self.mixed_scope_is_blocking,
            "ready": not self.blockers,
        }


def normalize(path: str) -> str:
    return path.strip().replace("\\", "/")


def parse_porcelain_line(line: str) -> str:
    path = line[3:] if len(line) > 3 else line
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[1]
    return normalize(path)


def parse_porcelain_entry(line: str) -> StatusEntry:
    path = parse_porcelain_line(line)
    index_status = line[0] if line else " "
    worktree_status = line[1] if len(line) > 1 else " "
    staged = index_status not in {" ", "?"}
    unstaged = worktree_status not in {" "} or index_status == "?"
    return StatusEntry(path=path, staged=staged, unstaged=unstaged)


def run_git(args: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout


def git_status_paths(repo_root: Path) -> list[str]:
    output = run_git(["status", "--porcelain", "--untracked-files=all"], repo_root)
    return [parse_porcelain_line(line) for line in output.splitlines() if line.strip()]


def git_status_entries(repo_root: Path) -> list[StatusEntry]:
    output = run_git(["status", "--porcelain", "--untracked-files=all"], repo_root)
    return [parse_porcelain_entry(line) for line in output.splitlines() if line.strip()]


def evidence_status(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^Status:\s*(\S+)", text, flags=re.MULTILINE | re.IGNORECASE)
    return match.group(1).upper() if match else "UNKNOWN"


def evidence_open_items(path: Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(r"(?m)^\s*-\s*\[\s\]", text))


def is_required_release_path(path: str) -> bool:
    return path in REQUIRED_RELEASE_PATHS or any(path.startswith(prefix) for prefix in REQUIRED_RELEASE_PREFIXES)


def is_mixed_scope_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in MIXED_SCOPE_PREFIXES)


def classify(paths: list[str]) -> tuple[list[str], list[str], list[str]]:
    release_paths: list[str] = []
    mixed_paths: list[str] = []
    unknown_paths: list[str] = []
    for path in sorted(set(paths)):
        if is_required_release_path(path):
            release_paths.append(path)
        elif is_mixed_scope_path(path):
            mixed_paths.append(path)
        else:
            unknown_paths.append(path)
    return release_paths, mixed_paths, unknown_paths


def print_group(title: str, paths: list[str], limit: int) -> None:
    print(f"\n## {title}: {len(paths)}")
    for path in paths[:limit]:
        print(f"- {path}")
    if len(paths) > limit:
        print(f"- ... {len(paths) - limit} more")


def render_group(title: str, paths: list[str], limit: int) -> list[str]:
    lines = [f"## {title}: {len(paths)}", ""]
    for path in paths[:limit]:
        lines.append(f"- `{path}`")
    if len(paths) > limit:
        lines.append(f"- ... {len(paths) - limit} more")
    lines.append("")
    return lines


def repo_relative_path(repo_root: Path, path: str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    try:
        return normalize(str(candidate.resolve().relative_to(repo_root.resolve())))
    except ValueError:
        return normalize(str(candidate))


def collect_status(
    repo_root: Path,
    allow_mixed_scope_dirty: bool = False,
    ignored_paths: set[str] | None = None,
) -> CutoverStatus:
    ignored_paths = ignored_paths or set()
    entries = [
        entry
        for entry in git_status_entries(repo_root)
        if entry.path not in ignored_paths
    ]
    paths = [entry.path for entry in entries]
    release_paths, mixed_paths, unknown_paths = classify(paths)
    release_path_set = set(release_paths)
    staged_release_paths = sorted({entry.path for entry in entries if entry.path in release_path_set and entry.staged})
    unstaged_release_paths = sorted({entry.path for entry in entries if entry.path in release_path_set and entry.unstaged})
    blockers: list[str] = []
    if release_paths:
        blockers.append("release-owned dirty paths must be committed or excluded before release cutover")
    if mixed_paths and not allow_mixed_scope_dirty:
        blockers.append("mixed-scope dirty paths still need an include/exclude decision")
    if unknown_paths:
        blockers.append("unknown dirty paths still need review")

    manual_gates: list[ManualGate] = []
    for relative_path in MANUAL_GATE_FILES:
        path = repo_root / relative_path
        status = evidence_status(path)
        open_items = evidence_open_items(path)
        manual_gates.append(ManualGate(relative_path, status, open_items))
        if status != "PASS" or open_items:
            blockers.append(f"{relative_path} is not complete")

    if paths and not allow_mixed_scope_dirty:
        blockers.append("working tree is not clean")
    elif release_paths or unknown_paths:
        blockers.append("working tree contains release-owned or unknown dirty paths")

    return CutoverStatus(
        paths,
        release_paths,
        mixed_paths,
        unknown_paths,
        staged_release_paths,
        unstaged_release_paths,
        manual_gates,
        blockers,
        mixed_scope_is_blocking=not allow_mixed_scope_dirty,
    )


def render_report(status: CutoverStatus, limit: int) -> str:
    lines = [
        "# Windows Release Cutover Status",
        "",
        "This report is generated by `tools/check_windows_release_cutover.py`.",
        "It separates release-owned changes from mixed-scope changes before the",
        "final clean Git-ref source archive is created.",
        "",
        f"Dirty paths: `{len(status.paths)}`",
        f"Staged release-owned paths: `{len(status.staged_release_paths)}`",
        f"Unstaged release-owned paths: `{len(status.unstaged_release_paths)}`",
        f"Mixed-scope dirty paths block verdict: `{'YES' if status.mixed_scope_is_blocking else 'NO'}`",
        "",
    ]
    lines.extend(render_group("Release-required or release-owned dirty paths", status.release_paths, limit))
    lines.extend(render_group("Staged release-owned paths", status.staged_release_paths, limit))
    lines.extend(render_group("Unstaged release-owned paths", status.unstaged_release_paths, limit))
    lines.extend(
        render_group(
            "Mixed-scope dirty paths requiring explicit include/exclude decision",
            status.mixed_paths,
            limit,
        )
    )
    lines.extend(render_group("Unknown dirty paths requiring review", status.unknown_paths, limit))
    lines.extend(["## Manual evidence gates", ""])
    for gate in status.manual_gates:
        lines.append(f"- `{gate.path}`: status=`{gate.status}`, open_items=`{gate.open_items}`")
    lines.extend(["", "## Verdict", ""])
    if status.blockers:
        for blocker in status.blockers:
            lines.append(f"- BLOCKED: {blocker}")
    else:
        lines.append("- READY: release-owned paths, unknown paths, and manual cutover evidence are clean")
        if status.mixed_paths and not status.mixed_scope_is_blocking:
            lines.append("- NOTE: mixed-scope dirty paths were reported but did not block this Git-ref release cutover")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Windows release cutover readiness.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--strict", action="store_true", help="Fail if any cutover blocker remains.")
    parser.add_argument(
        "--allow-mixed-scope-dirty",
        action="store_true",
        help=(
            "Report known mixed-scope dirty paths without treating them as blockers. "
            "Use only when release artifacts and source archive are produced from a clean Git ref."
        ),
    )
    parser.add_argument("--limit", type=int, default=80, help="Maximum paths to print per group.")
    parser.add_argument("--output", help="Write the cutover status markdown report to this path.")
    parser.add_argument("--json-output", help="Write the cutover status as JSON to this path.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    ignored_paths: set[str] = set()
    if args.output:
        ignored_paths.add(repo_relative_path(repo_root, args.output))
    if args.json_output:
        ignored_paths.add(repo_relative_path(repo_root, args.json_output))
    status = collect_status(
        repo_root,
        allow_mixed_scope_dirty=args.allow_mixed_scope_dirty,
        ignored_paths=ignored_paths,
    )

    report = render_report(status, args.limit)
    print(report)

    if args.output:
        output_path = (repo_root / args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")

    if args.json_output:
        json_output_path = (repo_root / args.json_output).resolve()
        json_output_path.parent.mkdir(parents=True, exist_ok=True)
        json_output_path.write_text(json.dumps(status.to_dict(), indent=2) + "\n", encoding="utf-8")

    if status.blockers:
        return 1 if args.strict else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
