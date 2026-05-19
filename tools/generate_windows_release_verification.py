#!/usr/bin/env python3
"""Generate a concise Windows release verification summary."""

from __future__ import annotations

import argparse
import datetime as _datetime
import hashlib
import subprocess
import zipfile
from pathlib import Path


MANUAL_GATES = (
    "Clean Windows x64 VM install without admin rights",
    "Real model download with user consent and checksum verification",
    "CPU fallback processing with downloaded models",
    "CUDA processing with downloaded models on a supported NVIDIA machine",
    "OBS Virtual Camera workflow with OBS installed and virtual camera enabled",
    "Final legal review for model licenses, pyvirtualcam metadata, LGPL/GPL obligations, and Inno Setup commercial-use position",
)

MANUAL_GATE_EVIDENCE = {
    "Clean Windows x64 VM install without admin rights": "CLEAN_VM_VERIFICATION.md",
    "OBS Virtual Camera workflow with OBS installed and virtual camera enabled": "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
    "Final legal review for model licenses, pyvirtualcam metadata, LGPL/GPL obligations, and Inno Setup commercial-use position": "LEGAL_REVIEW.md",
}


REQUIRED_DIST_FILES = (
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "COMPLIANCE.md",
    "RELEASE_CHECKLIST.md",
    "RELEASE_REPORT.md",
    "RELEASE_SOURCE_PREP.md",
    "MODEL_DOWNLOAD_VERIFICATION.md",
    "PROCESSING_VERIFICATION.md",
    "docs/OBS_VIRTUAL_CAMERA.md",
    "LICENSES/BUNDLED_BINARY_OBLIGATIONS.md",
    "LICENSES/MODEL_LICENSE_AUDIT.md",
    "LICENSES/PYTHON_DEPENDENCIES.md",
    "LICENSES/THIRD_PARTY_LICENSES/README.md",
    "LICENSES/THIRD_PARTY_LICENSES/tensorflow-2.19.1/package/THIRD_PARTY_NOTICES.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-gpu-1.23.2/package/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opencv-python-4.10.0.84/package/LICENSE-3RD-PARTY.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnx-1.18.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opennsfw2-0.10.2/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/licenses/LicenseRef-Qt-Commercial.txt",
    "LICENSES/THIRD_PARTY_LICENSES/shiboken6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE",
    "LICENSES/WINDOWS_BUNDLE_MANIFEST.md",
)


MODEL_DOWNLOAD_VERIFICATION = "MODEL_DOWNLOAD_VERIFICATION.md"
PROCESSING_VERIFICATION = "PROCESSING_VERIFICATION.md"
CUTOVER_STATUS = "RELEASE_CUTOVER_STATUS.md"


FORBIDDEN_SUFFIXES = {".onnx", ".pth", ".safetensors"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def run_git(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def checkbox(ok: bool) -> str:
    return "x" if ok else " "


def yes_no(ok: bool) -> str:
    return "YES" if ok else "NO"


def evidence_status(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.strip().lower().startswith("status:"):
            return line.split(":", 1)[1].strip().upper() or "UNKNOWN"
    return "UNKNOWN"


def evidence_open_items(path: Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    return sum(1 for line in text.splitlines() if line.lstrip().startswith("- [ ]"))


def evidence_passed(path: Path) -> bool:
    return evidence_status(path) == "PASS" and evidence_open_items(path) == 0


def parse_cutover_status(path: Path) -> dict[str, int | bool]:
    if not path.exists():
        return {
            "exists": False,
            "dirty_paths": -1,
            "release_owned": -1,
            "staged_release_owned": -1,
            "unstaged_release_owned": -1,
            "mixed_scope": -1,
            "unknown": -1,
            "mixed_scope_blocking": True,
            "blocked": True,
        }
    text = path.read_text(encoding="utf-8", errors="replace")

    def count(pattern: str) -> int:
        import re

        match = re.search(pattern, text)
        return int(match.group(1)) if match else -1

    return {
        "exists": True,
        "dirty_paths": count(r"Dirty paths:\s*`?(\d+)`?"),
        "staged_release_owned": count(r"Staged release-owned paths:\s*`?(\d+)`?"),
        "unstaged_release_owned": count(r"Unstaged release-owned paths:\s*`?(\d+)`?"),
        "release_owned": count(r"Release-required or release-owned dirty paths:\s*(\d+)"),
        "mixed_scope": count(r"Mixed-scope dirty paths requiring explicit include/exclude decision:\s*(\d+)"),
        "unknown": count(r"Unknown dirty paths requiring review:\s*(\d+)"),
        "mixed_scope_blocking": "Mixed-scope dirty paths block verdict: `NO`" not in text,
        "blocked": "BLOCKED:" in text,
    }


def find_source_archives(output_dir: Path, app_version: str) -> list[Path]:
    return sorted(output_dir.glob(f"DeepLiveCamStudio-{app_version}-source-*.zip"))


def archive_has_forbidden_models(archive: Path) -> bool:
    with zipfile.ZipFile(archive) as zf:
        for name in zf.namelist():
            lower = name.lower()
            if Path(lower).suffix in FORBIDDEN_SUFFIXES:
                return True
            if any(part in {"models", "checkpoints", "model-cache", "model_cache"} for part in lower.split("/")):
                return True
    return False


def source_archive_mode(manifest: Path | None) -> str:
    if not manifest or not manifest.exists():
        return ""
    text = manifest.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if line.startswith("Archive mode:"):
            return line.split("`", 2)[1] if "`" in line else line.split(":", 1)[1].strip()
    return ""


def source_manifest_text(source_archive: Path) -> str:
    manifest = source_archive.with_suffix(".manifest.md")
    if not manifest.exists():
        return ""
    return manifest.read_text(encoding="utf-8", errors="replace")


def select_source_archive(source_archives: list[Path]) -> Path | None:
    if not source_archives:
        return None
    git_ref_archives = [
        source
        for source in source_archives
        if "Archive mode: `git-ref`" in source_manifest_text(source)
    ]
    candidates = git_ref_archives or source_archives
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, path.name))[-1]


def generate(repo_root: Path, dist_dir: Path, output_dir: Path, app_version: str) -> tuple[str, bool, list[str]]:
    now = _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0).isoformat()
    installer = output_dir / f"DeepLiveCamStudio-{app_version}-x64-setup.exe"
    installer_hash = installer.with_suffix(installer.suffix + ".sha256")
    manifest = dist_dir / "LICENSES" / "WINDOWS_BUNDLE_MANIFEST.md"
    source_archives = find_source_archives(output_dir, app_version)
    latest_source = select_source_archive(source_archives)
    latest_source_hash = Path(str(latest_source) + ".sha256") if latest_source else None
    latest_source_manifest = latest_source.with_suffix(".manifest.md") if latest_source else None

    git_head = run_git(["rev-parse", "HEAD"], repo_root) or "UNKNOWN"
    git_status = run_git(["status", "--porcelain"], repo_root)
    dirty = bool(git_status)

    required_dist_status = [(path, (dist_dir / path).exists()) for path in REQUIRED_DIST_FILES]
    model_download_verification = repo_root / MODEL_DOWNLOAD_VERIFICATION
    processing_verification = repo_root / PROCESSING_VERIFICATION
    cutover_status_path = repo_root / CUTOVER_STATUS
    cutover_status = parse_cutover_status(cutover_status_path)
    manual_evidence_status = {
        gate: (
            repo_root / relative_path,
            evidence_status(repo_root / relative_path),
            evidence_open_items(repo_root / relative_path),
        )
        for gate, relative_path in MANUAL_GATE_EVIDENCE.items()
    }
    forbidden_dist = [
        path
        for path in dist_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES
    ] if dist_dir.exists() else []

    manifest_text = manifest.read_text(encoding="utf-8", errors="replace") if manifest.exists() else ""
    manifest_clean_models = "Forbidden model/checkpoint files found: 0" in manifest_text

    installer_ok = installer.exists()
    installer_hash_ok = False
    installer_digest = ""
    if installer_ok:
        installer_digest = sha256(installer)
        if installer_hash.exists():
            sidecar_digest = installer_hash.read_text(encoding="ascii", errors="replace").strip().split()[0].upper()
            installer_hash_ok = sidecar_digest == installer_digest

    source_archive_ok = bool(latest_source and latest_source.exists())
    source_hash_ok = False
    if latest_source and latest_source.exists() and latest_source_hash and latest_source_hash.exists():
        source_sidecar_digest = latest_source_hash.read_text(encoding="ascii", errors="replace").strip().split()[0].upper()
        source_hash_ok = source_sidecar_digest == sha256(latest_source)
    source_manifest_ok = bool(latest_source_manifest and latest_source_manifest.exists())
    source_mode = source_archive_mode(latest_source_manifest)
    source_is_clean_git_ref = source_mode == "git-ref"
    source_clean_models = False
    if latest_source:
        try:
            source_clean_models = not archive_has_forbidden_models(latest_source)
        except (FileNotFoundError, zipfile.BadZipFile):
            source_clean_models = False

    required_dist_ok = all(present for _, present in required_dist_status)
    automated_installer_ok = (
        installer_ok
        and installer_hash_ok
        and manifest.exists()
        and manifest_clean_models
        and not forbidden_dist
        and required_dist_ok
    )
    draft_traceability_ok = source_archive_ok and source_hash_ok and source_manifest_ok and source_clean_models
    public_source_ok = draft_traceability_ok and source_is_clean_git_ref
    manual_gates_done = {
        gate: (
            (gate.startswith("Real model download") and model_download_verification.exists())
            or (gate.startswith("CPU fallback processing") and processing_verification.exists())
            or (gate.startswith("CUDA processing") and processing_verification.exists())
            or (gate in manual_evidence_status and evidence_passed(manual_evidence_status[gate][0]))
        )
        for gate in MANUAL_GATES
    }
    all_manual_gates_done = all(manual_gates_done.values())
    cutover_ready = bool(cutover_status["exists"]) and not bool(cutover_status["blocked"])
    publishable_by_automation = automated_installer_ok and public_source_ok and all_manual_gates_done and cutover_ready
    publish_blockers: list[str] = []
    if not automated_installer_ok:
        publish_blockers.append("Local installer automation evidence is incomplete or failed.")
    release_owned_dirty = int(cutover_status["release_owned"]) if cutover_status["exists"] else -1
    unknown_dirty = int(cutover_status["unknown"]) if cutover_status["exists"] else -1
    if dirty and source_mode != "git-ref":
        publish_blockers.append("Working tree is dirty; create the release source archive from a clean release tag or commit.")
    elif dirty and (release_owned_dirty != 0 or unknown_dirty != 0):
        publish_blockers.append("Working tree contains release-owned or unknown dirty paths.")
    if not draft_traceability_ok:
        publish_blockers.append("Corresponding-source archive, hash sidecar, manifest, or forbidden-file scan is incomplete.")
    elif source_mode != "git-ref":
        publish_blockers.append(f"Corresponding-source archive mode is `{source_mode or 'UNKNOWN'}`, not `git-ref`.")
    if not cutover_status["exists"]:
        publish_blockers.append("RELEASE_CUTOVER_STATUS.md is missing.")
    elif cutover_status["blocked"]:
        publish_blockers.append("RELEASE_CUTOVER_STATUS.md reports unresolved cutover blockers.")
    for gate, gate_done in manual_gates_done.items():
        if not gate_done:
            if gate in manual_evidence_status:
                path, status, open_items = manual_evidence_status[gate]
                publish_blockers.append(
                    f"{path.name} is `{status}` with {open_items} open checklist item(s)."
                )
            else:
                publish_blockers.append(f"{gate} evidence is missing.")

    lines = [
        "# Windows Release Verification",
        "",
        f"Generated: {now}",
        f"App version: `{app_version}`",
        f"Git HEAD: `{git_head}`",
        "",
        "This file records local release evidence for the Windows installer. It is not a legal opinion and does not replace the manual checks in `RELEASE_CHECKLIST.md`.",
        "",
        "## Release Verdict",
        "",
        f"- Local installer automation passed: **{yes_no(automated_installer_ok)}**",
        f"- Draft source traceability available: **{yes_no(draft_traceability_ok)}**",
        f"- Real model download/checksum verification recorded: **{yes_no(model_download_verification.exists())}**",
        f"- Packaged CPU/CUDA processing verification recorded: **{yes_no(processing_verification.exists())}**",
        f"- Public-release source archive from clean Git ref: **{yes_no(public_source_ok)}**",
        f"- Release cutover status clean: **{yes_no(cutover_ready)}**",
        f"- Manual gate evidence complete: **{yes_no(all_manual_gates_done)}**",
        f"- Ready to publish without remaining manual gates: **{yes_no(publishable_by_automation)}**",
        "",
        "Current status: the installer and Git-ref source archive are locally verified, but this is not yet a publishable GitHub Release until the manual checklist gates are completed.",
        "",
        "## Automated Evidence",
        "",
        f"- [{checkbox(installer_ok)}] Installer exists: `{installer}`",
        f"- [{checkbox(installer_hash_ok)}] Installer SHA-256 sidecar matches",
    ]
    if installer_digest:
        lines.append(f"  - SHA-256: `{installer_digest}`")
    if installer_ok:
        lines.append(f"  - Installer bytes: `{installer.stat().st_size}`")

    lines.extend(
        [
            f"- [{checkbox(manifest.exists())}] Windows bundle manifest exists: `{manifest}`",
            f"- [{checkbox(manifest_clean_models and not forbidden_dist)}] Packaged payload contains no forbidden model/checkpoint files",
            f"- [{checkbox(source_is_clean_git_ref)}] Public-release source archive was created from a Git ref",
            f"- [{checkbox(source_archive_ok)}] Corresponding-source archive exists",
            f"- [{checkbox(source_hash_ok)}] Corresponding-source SHA-256 sidecar matches",
            f"- [{checkbox(source_manifest_ok)}] Corresponding-source manifest exists",
            f"- [{checkbox(source_clean_models)}] Corresponding-source archive contains no forbidden model/checkpoint entries",
            f"- [{checkbox(source_is_clean_git_ref)}] Public-release source archive was created from a clean Git ref",
            f"- [{checkbox(model_download_verification.exists())}] Real model download/checksum verification exists: `{model_download_verification}`",
            f"- [{checkbox(processing_verification.exists())}] Packaged processing verification exists: `{processing_verification}`",
            "",
            "## Required Installed Release Files",
            "",
        ]
    )

    for path, present in required_dist_status:
        lines.append(f"- [{checkbox(present)}] `{path}`")

    lines.extend(["", "## Source Archive", ""])
    if latest_source:
        lines.append(f"- Latest source archive: `{latest_source}`")
        if source_mode:
            lines.append(f"- Source archive mode: `{source_mode}`")
        if latest_source_hash and latest_source_hash.exists():
            lines.append(f"- Source archive hash sidecar: `{latest_source_hash}`")
        if latest_source_manifest and latest_source_manifest.exists():
            lines.append(f"- Source archive manifest: `{latest_source_manifest}`")
        if source_mode == "draft-working-tree":
            lines.append("- Draft worktree source archives are useful for local traceability, but public GitHub Releases still require a clean tagged source archive.")
    else:
        lines.append("- No corresponding-source archive was found in the installer output directory.")
        lines.append("- Run `build/windows/package_source.ps1` against the exact release tag or commit before publishing, or pass `-FromWorkingTree` only for draft local traceability.")

    lines.extend(["", "## Cutover Status", ""])
    if cutover_status["exists"]:
        lines.append(f"- Cutover status report: `{cutover_status_path}`")
        lines.append(f"- Dirty paths: `{cutover_status['dirty_paths']}`")
        lines.append(f"- Release-owned dirty paths: `{cutover_status['release_owned']}`")
        lines.append(f"- Staged release-owned paths: `{cutover_status['staged_release_owned']}`")
        lines.append(f"- Unstaged release-owned paths: `{cutover_status['unstaged_release_owned']}`")
        lines.append(f"- Mixed-scope dirty paths: `{cutover_status['mixed_scope']}`")
        lines.append(f"- Mixed-scope dirty paths block verdict: **{yes_no(bool(cutover_status['mixed_scope_blocking']))}**")
        lines.append(f"- Unknown dirty paths: `{cutover_status['unknown']}`")
        lines.append(f"- Cutover report blocked: **{yes_no(bool(cutover_status['blocked']))}**")
    else:
        lines.append("- Cutover status report is missing. Run `tools/check_windows_release_cutover.py --output RELEASE_CUTOVER_STATUS.md` before publishing.")

    lines.extend(["", "## Manual Gates Still Required", ""])
    for gate in MANUAL_GATES:
        gate_done = manual_gates_done[gate]
        lines.append(f"- [{checkbox(gate_done)}] {gate}")

    lines.extend(["", "## Manual Gate Evidence Files", ""])
    for gate, (path, status, open_items) in manual_evidence_status.items():
        passed = evidence_passed(path)
        lines.append(f"- [{checkbox(passed)}] `{path.name}` for {gate}: `{status}`")
        if path.exists():
            lines.append(f"  - Open checklist items: `{open_items}`")

    lines.extend(["", "## Blocking Publish Checks", ""])
    if publish_blockers:
        for blocker in publish_blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- None. Automated evidence says this release is publish-ready.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- A dirty working tree is expected during local development. A public AGPL binary release should be paired with the exact Git-ref source archive listed in the release assets, and release-owned or unknown dirty paths must not be included accidentally.",
            "- Model files are intentionally excluded from the installer and should be downloaded only after user consent and checksum verification.",
            "",
        ]
    )
    return "\n".join(lines), publishable_by_automation, publish_blockers


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Windows release verification evidence.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--dist", default="dist/DeepLiveCamStudio", help="Packaged dist directory.")
    parser.add_argument("--output-dir", default="build/windows/installer", help="Installer output directory.")
    parser.add_argument("--app-version", default="2.1.5", help="Application version.")
    parser.add_argument("--output", default="RELEASE_VERIFICATION.md", help="Verification summary output path.")
    parser.add_argument(
        "--require-publish-ready",
        action="store_true",
        help="Exit non-zero unless installer, clean source archive, and manual gate evidence are all complete.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    text, publishable, publish_blockers = generate(
        repo_root=repo_root,
        dist_dir=(repo_root / args.dist).resolve(),
        output_dir=(repo_root / args.output_dir).resolve(),
        app_version=args.app_version,
    )
    output = (repo_root / args.output).resolve()
    output.write_text(text, encoding="utf-8")
    print(f"Wrote {output}")
    if args.require_publish_ready and not publishable:
        print("Release is not publish-ready. See RELEASE_VERIFICATION.md for failed gates.")
        for blocker in publish_blockers:
            print(f"- {blocker}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
