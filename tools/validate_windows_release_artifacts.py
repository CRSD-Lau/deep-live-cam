#!/usr/bin/env python3
"""Validate Windows release artifacts before upload."""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path


FORBIDDEN_SUFFIXES = {".onnx", ".pth", ".safetensors"}
FORBIDDEN_DIRS = {"models", "checkpoints", "model-cache", "model_cache"}
REQUIRED_SOURCE_ENTRIES = (
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "COMPLIANCE.md",
    "Logo.png",
    "THIRD_PARTY_NOTICES.md",
    "RELEASE_CHECKLIST.md",
    "RELEASE_COMPLETION_AUDIT.md",
    "RELEASE_CUTOVER_PLAN.md",
    "RELEASE_CUTOVER_STATUS.md",
    "CLEAN_RELEASE_WORKTREE_VERIFICATION.md",
    "RELEASE_NOTES_TEMPLATE.md",
    "RELEASE_PUBLISH_HANDOFF.md",
    "RELEASE_REPORT.md",
    "RELEASE_SOURCE_PREP.md",
    "CLEAN_VM_VERIFICATION.md",
    "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
    "LEGAL_REVIEW.md",
    "MODEL_DOWNLOAD_VERIFICATION.md",
    "PROCESSING_VERIFICATION.md",
    "docs/OBS_VIRTUAL_CAMERA.md",
    "docs/DIRECTML_TESTING.md",
    "LICENSES/BUNDLED_BINARY_OBLIGATIONS.md",
    "LICENSES/MODEL_LICENSE_AUDIT.md",
    "LICENSES/PYTHON_DEPENDENCIES.md",
    "LICENSES/README.md",
    "LICENSES/WINDOWS_BUNDLE_MANIFEST.md",
    "LICENSES/THIRD_PARTY_LICENSES/README.md",
    "LICENSES/THIRD_PARTY_LICENSES/tensorflow-2.19.1/package/THIRD_PARTY_NOTICES.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-gpu-1.23.2/package/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-directml-1.23.0/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-directml-1.23.0/package/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opencv-python-4.10.0.84/package/LICENSE-3RD-PARTY.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnx-1.22.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opennsfw2-0.10.2/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/licenses/LicenseRef-Qt-Commercial.txt",
    "LICENSES/THIRD_PARTY_LICENSES/shiboken6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE",
    ".github/workflows/windows-release.yml",
    ".github/workflows/windows-directml-test.yml",
    "DeepLiveCamStudio.pyw",
    "build/windows/build_windows.ps1",
    "build/windows/assemble_release_assets.ps1",
    "build/windows/clean_build.ps1",
    "build/windows/package_installer.ps1",
    "build/windows/package_portable.ps1",
    "build/windows/package_source.ps1",
    "build/windows/prepare_release_staging.ps1",
    "build/windows/run_release_checks.ps1",
    "build/windows/test_environment.ps1",
    "build/windows/test_packaged_runtime.ps1",
    "build/windows/test_installer.ps1",
    "build/windows/verify_clean_vm_gate.ps1",
    "build/windows/verify_legal_review_gate.ps1",
    "build/windows/verify_obs_virtualcam_gate.ps1",
    "build/windows/deep_live_cam_studio.spec",
    "build/windows/installer.iss",
    "tools/check_cuda_provider.py",
    "tools/check_obs_virtualcam.py",
    "tools/check_windows_release_cutover.py",
    "tools/collect_third_party_license_files.py",
    "tools/generate_python_dependency_licenses.py",
    "tools/generate_windows_logo_assets.py",
    "tools/prune_windows_dist.py",
    "tools/generate_windows_bundle_manifest.py",
    "tools/generate_windows_release_verification.py",
    "tools/install_windows_desktop_app.ps1",
    "tools/setup_directml.ps1",
    "tools/validate_windows_release_artifacts.py",
    "tools/summarize_manual_release_gates.py",
    "requirements.txt",
    "requirements-directml.txt",
    "run-directml.bat",
    "run.py",
    "modules/core.py",
    "modules/globals.py",
    "modules/execution_providers.py",
    "modules/face_analyser.py",
    "modules/desktop_launcher.py",
    "modules/model_manager.py",
    "modules/paths.py",
    "modules/ui.py",
    "modules/utilities.py",
    "modules/processors/frame/_onnx_enhancer.py",
    "modules/processors/frame/core.py",
    "modules/processors/frame/face_enhancer.py",
    "modules/processors/frame/face_enhancer_gpen256.py",
    "modules/processors/frame/face_enhancer_gpen512.py",
    "modules/processors/frame/face_swapper.py",
    "tests/test_image_upload_formats.py",
    "tests/test_directml_support.py",
    "tests/test_execution_providers.py",
    "tests/test_model_manager.py",
    "tests/test_validate_windows_release_artifacts.py",
    "tests/test_release_report.py",
    "tests/test_summarize_manual_release_gates.py",
    "tests/test_windows_release_scripts.py",
    "tests/test_windows_release_cutover.py",
    "tests/test_windows_release_verification.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_sidecar_digest(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="ascii", errors="replace").strip().split()[0].upper()


def validate_sha256sums(assets_dir: Path, failures: list[str]) -> None:
    sums_path = assets_dir / "SHA256SUMS.txt"
    if not sums_path.exists():
        fail("release assets missing required document: SHA256SUMS.txt", failures)
        return

    lines = [
        line.strip()
        for line in sums_path.read_text(encoding="ascii", errors="replace").splitlines()
        if line.strip()
    ]
    expected_files = sorted(
        path.name
        for path in assets_dir.iterdir()
        if path.is_file() and path.name != "SHA256SUMS.txt"
    )
    seen_files: list[str] = []
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            fail(f"SHA256SUMS.txt contains malformed line: {line}", failures)
            continue
        digest, name = parts
        name = name.strip()
        path = assets_dir / name
        seen_files.append(name)
        if not path.exists() or not path.is_file():
            fail(f"SHA256SUMS.txt lists missing file: {name}", failures)
            continue
        if digest.upper() != sha256(path):
            fail(f"SHA256SUMS.txt digest mismatch for: {name}", failures)

    if sorted(seen_files) != expected_files:
        missing = sorted(set(expected_files) - set(seen_files))
        extra = sorted(set(seen_files) - set(expected_files))
        for name in missing:
            fail(f"SHA256SUMS.txt missing file: {name}", failures)
        for name in extra:
            fail(f"SHA256SUMS.txt lists unexpected file: {name}", failures)


def source_archive_has_forbidden_entries(path: Path) -> list[str]:
    forbidden: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            lower = name.lower()
            parts = set(lower.split("/"))
            if Path(lower).suffix in FORBIDDEN_SUFFIXES or parts.intersection(FORBIDDEN_DIRS):
                forbidden.append(name)
    return forbidden


def source_archive_missing_required_entries(path: Path, app_version: str) -> list[str]:
    prefix = f"DeepLiveCamStudio-{app_version}-source/"
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    return [entry for entry in REQUIRED_SOURCE_ENTRIES if f"{prefix}{entry}" not in names]


def _validate_directml_portable(
    assets_dir: Path, app_version: str, failures: list[str]
) -> tuple[Path | None, str]:
    """Validate the DirectML portable ZIP, hash, runtime entries, and model exclusion."""
    archive_path = assets_dir / f"DeepLiveCamStudio-{app_version}-DirectML-x64-portable.zip"
    hash_path = Path(str(archive_path) + ".sha256")
    if not archive_path.exists():
        fail(f"release assets missing DirectML portable archive: {archive_path.name}", failures)
        return None, ""

    digest = sha256(archive_path)
    if read_sidecar_digest(hash_path) != digest:
        fail(f"DirectML portable SHA-256 sidecar missing or mismatched: {hash_path.name}", failures)

    required_entries = {
        "DeepLiveCamStudio.exe",
        "DeepLiveCamStudioCLI.exe",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "_internal/sklearn/.libs/vcomp140.dll",
    }
    try:
        with zipfile.ZipFile(archive_path) as archive:
            names = {name.replace("\\", "/") for name in archive.namelist()}
        for entry in sorted(required_entries - names):
            fail(f"DirectML portable archive missing required entry: {entry}", failures)
        forbidden_entries = source_archive_has_forbidden_entries(archive_path)
    except zipfile.BadZipFile:
        fail(f"DirectML portable archive is not a valid zip: {archive_path.name}", failures)
        return archive_path, digest

    if forbidden_entries:
        for entry in forbidden_entries[:20]:
            print(f"[release-artifacts] forbidden DirectML portable entry: {entry}")
        fail("DirectML portable archive contains forbidden model/checkpoint entries", failures)

    return archive_path, digest


def source_manifest_text(path: Path) -> str:
    manifest = path.with_suffix(".manifest.md")
    if not manifest.exists():
        return ""
    return manifest.read_text(encoding="utf-8", errors="replace")


def select_source_archive(source_archives: list[Path], require_git_ref: bool) -> Path:
    candidates = source_archives
    if require_git_ref:
        git_ref_candidates = [
            source
            for source in source_archives
            if "Archive mode: `git-ref`" in source_manifest_text(source)
        ]
        if git_ref_candidates:
            candidates = git_ref_candidates
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, path.name))[-1]


def fail(message: str, failures: list[str]) -> None:
    print(f"[release-artifacts] FAIL: {message}")
    failures.append(message)


def require_text(path: Path, phrase: str, description: str, failures: list[str]) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    if phrase not in text:
        fail(f"{path.name} does not reference current {description}: {phrase}", failures)


def validate_release_evidence_consistency(
    assets_dir: Path,
    installer_digest: str,
    source: Path,
    source_digest: str,
    failures: list[str],
) -> None:
    gate_docs_with_installer_hash = (
        "CLEAN_VM_VERIFICATION.md",
        "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
        "LEGAL_REVIEW.md",
        "CLEAN_VM_AUTOMATED_EVIDENCE.md",
        "LEGAL_REVIEW_EVIDENCE_PACKET.md",
    )
    for name in gate_docs_with_installer_hash:
        require_text(
            assets_dir / name,
            installer_digest,
            "installer SHA-256",
            failures,
        )

    legal_packet = assets_dir / "LEGAL_REVIEW_EVIDENCE_PACKET.md"
    require_text(legal_packet, source.name, "source archive name", failures)
    require_text(legal_packet, source_digest, "source archive SHA-256", failures)


def source_manifest_resolved_ref(manifest_text: str) -> str:
    for line in manifest_text.splitlines():
        if line.startswith("Git ref resolved:") and "`" in line:
            return line.split("`", 2)[1]
    return ""


def validate_release_assets_dir(
    assets_dir: Path,
    app_version: str,
    require_git_ref: bool,
    require_directml_portable: bool,
    failures: list[str],
) -> None:
    if not assets_dir.exists():
        fail(f"missing release assets directory: {assets_dir}", failures)
        return

    installer = assets_dir / f"DeepLiveCamStudio-{app_version}-x64-setup.exe"
    installer_hash = installer.with_suffix(installer.suffix + ".sha256")
    if not installer.exists():
        fail(f"release assets missing installer: {installer.name}", failures)
    elif read_sidecar_digest(installer_hash) != sha256(installer):
        fail(f"release assets installer hash missing or mismatched: {installer_hash.name}", failures)

    source_archives = sorted(assets_dir.glob(f"DeepLiveCamStudio-{app_version}-source-*.zip"))
    if len(source_archives) != 1:
        fail(f"release assets must contain exactly one source archive, found {len(source_archives)}", failures)
        return

    source = source_archives[0]
    source_hash = Path(str(source) + ".sha256")
    source_manifest = source.with_suffix(".manifest.md")
    if read_sidecar_digest(source_hash) != sha256(source):
        fail(f"release assets source hash missing or mismatched: {source_hash.name}", failures)
    source_digest = sha256(source)
    manifest_text = source_manifest.read_text(encoding="utf-8", errors="replace") if source_manifest.exists() else ""
    resolved_ref = source_manifest_resolved_ref(manifest_text)
    if not manifest_text:
        fail(f"release assets source manifest missing: {source_manifest.name}", failures)
    elif require_git_ref and "Archive mode: `git-ref`" not in manifest_text:
        fail("release assets source manifest is not git-ref mode", failures)

    try:
        forbidden_entries = source_archive_has_forbidden_entries(source)
    except zipfile.BadZipFile:
        fail(f"release assets source archive is not a valid zip: {source.name}", failures)
        forbidden_entries = []
    if forbidden_entries:
        for entry in forbidden_entries[:20]:
            print(f"[release-artifacts] forbidden release asset source entry: {entry}")
        fail("release assets source archive contains forbidden model/checkpoint entries", failures)

    forbidden_asset_files = [
        path.name
        for path in assets_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if forbidden_asset_files:
        for name in forbidden_asset_files[:20]:
            print(f"[release-artifacts] forbidden release asset file: {name}")
        fail("release assets directory contains forbidden model/checkpoint files", failures)

    required_docs = (
        "RELEASE_ASSETS.md",
        "SHA256SUMS.txt",
        "RELEASE_NOTES.md",
        "RELEASE_NOTES_TEMPLATE.md",
        "RELEASE_PUBLISH_HANDOFF.md",
        "RELEASE_SOURCE_PREP.md",
        "RELEASE_VERIFICATION.md",
        "RELEASE_CHECKLIST.md",
        "RELEASE_COMPLETION_AUDIT.md",
        "RELEASE_CUTOVER_PLAN.md",
        "RELEASE_CUTOVER_STATUS.md",
        "CLEAN_RELEASE_WORKTREE_VERIFICATION.md",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "RELEASE_REPORT.md",
        "CLEAN_VM_VERIFICATION.md",
        "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
        "LEGAL_REVIEW.md",
        "MODEL_DOWNLOAD_VERIFICATION.md",
        "PROCESSING_VERIFICATION.md",
        "MANUAL_RELEASE_GATES.md",
        "CLEAN_VM_AUTOMATED_EVIDENCE.md",
        "OBS_VIRTUAL_CAMERA_AUTOMATED_EVIDENCE.md",
        "LEGAL_REVIEW_EVIDENCE_PACKET.md",
        "COMPLIANCE.md",
        "THIRD_PARTY_NOTICES.md",
        "BUNDLED_BINARY_OBLIGATIONS.md",
        "MODEL_LICENSE_AUDIT.md",
        "PYTHON_DEPENDENCIES.md",
        "WINDOWS_BUNDLE_MANIFEST.md",
    )
    for doc in required_docs:
        if not (assets_dir / doc).exists():
            fail(f"release assets missing required document: {doc}", failures)

    directml_archive = None
    directml_digest = ""
    if require_directml_portable:
        directml_archive, directml_digest = _validate_directml_portable(
            assets_dir, app_version, failures
        )
    validate_sha256sums(assets_dir, failures)
    if installer.exists() and source.exists():
        validate_release_evidence_consistency(
            assets_dir=assets_dir,
            installer_digest=sha256(installer),
            source=source,
            source_digest=source_digest,
            failures=failures,
        )

    manual_gate_summary = assets_dir / "MANUAL_RELEASE_GATES.md"
    if manual_gate_summary.exists():
        manual_gate_text = manual_gate_summary.read_text(encoding="utf-8", errors="replace")
        required_gate_phrases = (
            "# Manual Windows Release Gate Summary",
            "`CLEAN_VM_VERIFICATION.md`",
            "`OBS_VIRTUAL_CAMERA_VERIFICATION.md`",
            "`LEGAL_REVIEW.md`",
            "## Open Items",
        )
        for phrase in required_gate_phrases:
            if phrase not in manual_gate_text:
                fail(f"MANUAL_RELEASE_GATES.md missing phrase: {phrase}", failures)

    asset_manifest = assets_dir / "RELEASE_ASSETS.md"
    if asset_manifest.exists():
        asset_manifest_text = asset_manifest.read_text(encoding="utf-8", errors="replace")
        for path in [installer, installer_hash, source, source_hash, source_manifest]:
            if f"`{path.name}`" not in asset_manifest_text:
                fail(f"RELEASE_ASSETS.md does not list: {path.name}", failures)
        if directml_archive:
            for path in [directml_archive, Path(str(directml_archive) + ".sha256")]:
                if f"`{path.name}`" not in asset_manifest_text:
                    fail(f"RELEASE_ASSETS.md does not list: {path.name}", failures)
        for doc in required_docs:
            if f"`{doc}`" not in asset_manifest_text:
                fail(f"RELEASE_ASSETS.md does not list required document: {doc}", failures)
        if "Do not upload model/checkpoint files" not in asset_manifest_text:
            fail("RELEASE_ASSETS.md missing model/checkpoint upload warning", failures)
        if resolved_ref and f"Source ref: `{resolved_ref}`" not in asset_manifest_text:
            fail("RELEASE_ASSETS.md source ref does not match source manifest", failures)

    release_notes = assets_dir / "RELEASE_NOTES.md"
    if release_notes.exists():
        release_notes_text = release_notes.read_text(encoding="utf-8", errors="replace")
        expected_phrases = (
            f"`{installer.name}`",
            f"`{sha256(installer)}`",
            f"`{source.name}`",
            f"`{sha256(source)}`",
            "Deep-Live-Cam is licensed under AGPL-3.0",
            "The installer intentionally does not include model/checkpoint files",
            "This release candidate is not publish-approved",
            "Completed local evidence is included in the uploaded release documents:",
            "Remaining publish blockers:",
            "Authorized legal review for dependency, model-license, and redistribution obligations.",
        )
        if directml_archive:
            expected_phrases += (
                f"`{directml_archive.name}`",
                f"`{directml_digest}`",
            )
        for phrase in expected_phrases:
            if phrase not in release_notes_text:
                fail(f"RELEASE_NOTES.md missing phrase: {phrase}", failures)
        if resolved_ref and f"`{resolved_ref}`" not in release_notes_text:
            fail("RELEASE_NOTES.md source ref does not match source manifest", failures)
        if "listed in the uploaded `RELEASE_ASSETS.md`" in release_notes_text:
            fail("RELEASE_NOTES.md still contains manifest cross-reference placeholders", failures)
        if "This release candidate is not publish-approved until these checks are complete and documented:" in release_notes_text:
            fail("RELEASE_NOTES.md uses stale pre-publish wording that does not separate completed evidence from remaining blockers", failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Windows release artifact set.")
    parser.add_argument("--output-dir", default="build/windows/installer", help="Installer output directory.")
    parser.add_argument("--release-assets-dir", help="Optional curated GitHub Release asset directory to validate.")
    parser.add_argument("--app-version", default="2.2.0", help="Application version.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing RELEASE_VERIFICATION.md.")
    parser.add_argument(
        "--require-git-ref-source",
        action="store_true",
        help="Require source archive manifest mode to be git-ref instead of allowing draft-working-tree.",
    )
    parser.add_argument(
        "--require-directml-portable",
        action="store_true",
        help="Require and validate the versioned DirectML portable release ZIP.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    failures: list[str] = []

    installer = output_dir / f"DeepLiveCamStudio-{args.app_version}-x64-setup.exe"
    installer_hash = installer.with_suffix(installer.suffix + ".sha256")
    if not installer.exists():
        fail(f"missing installer: {installer}", failures)
    elif read_sidecar_digest(installer_hash) != sha256(installer):
        fail(f"installer SHA-256 sidecar missing or mismatched: {installer_hash}", failures)
    else:
        print(f"[release-artifacts] installer hash ok: {installer.name}")

    source_archives = sorted(output_dir.glob(f"DeepLiveCamStudio-{args.app_version}-source-*.zip"))
    if not source_archives:
        fail("missing corresponding-source archive", failures)
        latest_source = None
    else:
        latest_source = select_source_archive(source_archives, args.require_git_ref_source)
        source_hash = Path(str(latest_source) + ".sha256")
        source_manifest = latest_source.with_suffix(".manifest.md")
        if read_sidecar_digest(source_hash) != sha256(latest_source):
            fail(f"source SHA-256 sidecar missing or mismatched: {source_hash}", failures)
        else:
            print(f"[release-artifacts] source hash ok: {latest_source.name}")

        if not source_manifest.exists():
            fail(f"missing source manifest: {source_manifest}", failures)
        else:
            manifest_text = source_manifest.read_text(encoding="utf-8", errors="replace")
            if args.require_git_ref_source and "Archive mode: `git-ref`" not in manifest_text:
                fail("source archive manifest is not git-ref mode", failures)
            if "No `.onnx`, `.pth`, `.safetensors`" not in manifest_text:
                fail("source manifest does not record forbidden model/checkpoint scan", failures)
            for entry in REQUIRED_SOURCE_ENTRIES:
                if f"- [x] `{entry}`" not in manifest_text:
                    fail(f"source manifest missing required entry check: {entry}", failures)

        try:
            forbidden_entries = source_archive_has_forbidden_entries(latest_source)
            missing_entries = source_archive_missing_required_entries(latest_source, args.app_version)
        except zipfile.BadZipFile:
            fail(f"source archive is not a valid zip: {latest_source}", failures)
            forbidden_entries = []
            missing_entries = []
        if forbidden_entries:
            for entry in forbidden_entries[:20]:
                print(f"[release-artifacts] forbidden source entry: {entry}")
            fail("source archive contains forbidden model/checkpoint entries", failures)
        if missing_entries:
            for entry in missing_entries[:20]:
                print(f"[release-artifacts] missing source entry: {entry}")
            fail("source archive is missing required corresponding-source entries", failures)

    release_verification = repo_root / "RELEASE_VERIFICATION.md"
    if not release_verification.exists():
        fail("missing RELEASE_VERIFICATION.md", failures)
    else:
        verification_text = release_verification.read_text(encoding="utf-8", errors="replace")
        required_phrases = (
            "Local installer automation passed:",
            "Public-release source archive from clean Git ref:",
            "Ready to publish without remaining manual gates:",
        )
        for phrase in required_phrases:
            if phrase not in verification_text:
                fail(f"RELEASE_VERIFICATION.md missing phrase: {phrase}", failures)

    if args.release_assets_dir:
        validate_release_assets_dir(
            assets_dir=(repo_root / args.release_assets_dir).resolve(),
            app_version=args.app_version,
            require_git_ref=args.require_git_ref_source,
            require_directml_portable=args.require_directml_portable,
            failures=failures,
        )

    if failures:
        print(f"[release-artifacts] {len(failures)} validation failure(s).")
        return 1

    print("[release-artifacts] artifact validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
