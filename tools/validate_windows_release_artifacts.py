#!/usr/bin/env python3
"""Validate Windows release artifacts before upload."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from dataclasses import dataclass, replace
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
    "docs/DEPENDENCY_LOCKS.md",
    "LICENSES/BUNDLED_BINARY_OBLIGATIONS.md",
    "LICENSES/MODEL_LICENSE_AUDIT.md",
    "LICENSES/PYTHON_DEPENDENCIES.md",
    "LICENSES/PYTHON_DEPENDENCIES_DIRECTML.md",
    "LICENSES/README.md",
    "LICENSES/WINDOWS_BUNDLE_MANIFEST.md",
    "LICENSES/THIRD_PARTY_LICENSES/README.md",
    "LICENSES/THIRD_PARTY_LICENSES/tensorflow-2.19.1/package/THIRD_PARTY_NOTICES.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-gpu-1.24.4/package/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/torch-2.11.0_cu128/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/torch-2.11.0_cu128/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/torch-2.11.0_cu128/NOTICE",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-directml-1.23.0/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-directml-1.23.0/package/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opencv-python-4.10.0.84/package/LICENSE-3RD-PARTY.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnx-1.22.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opennsfw2-0.18.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/licenses/LicenseRef-Qt-Commercial.txt",
    "LICENSES/THIRD_PARTY_LICENSES/shiboken6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
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
    "build/windows/test_legacy_installer.iss",
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
    "tools/update_dependency_locks.ps1",
    "tools/validate_windows_release_artifacts.py",
    "tools/summarize_manual_release_gates.py",
    "requirements.txt",
    "requirements-directml.txt",
    "requirements-build-windows.txt",
    "requirements-build-windows-cuda.txt",
    "requirements-lock-tools.txt",
    "requirements-locks/windows-cuda-py311.lock",
    "requirements-locks/windows-cuda-runtime-py311.lock",
    "requirements-locks/windows-cuda-runtime-audit-py311.txt",
    "requirements-locks/windows-directml-py311.lock",
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
    "tests/test_dependency_locks.py",
    "tests/test_execution_providers.py",
    "tests/test_model_manager.py",
    "tests/test_validate_windows_release_artifacts.py",
    "tests/test_release_report.py",
    "tests/test_summarize_manual_release_gates.py",
    "tests/test_windows_release_scripts.py",
    "tests/test_windows_release_cutover.py",
    "tests/test_windows_release_verification.py",
)

REQUIRED_RELEASE_DOCUMENTS = (
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
    "COMPLIANCE.md",
    "THIRD_PARTY_NOTICES.md",
    "BUNDLED_BINARY_OBLIGATIONS.md",
    "MODEL_LICENSE_AUDIT.md",
    "PYTHON_DEPENDENCIES.md",
    "PYTHON_DEPENDENCIES_DIRECTML.md",
    "WINDOWS_BUNDLE_MANIFEST.md",
)


@dataclass(frozen=True)
class ValidationResult:
    """One named release validation check and its exact failure messages."""

    name: str
    failures: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass(frozen=True)
class ReleaseAssetContext:
    assets_dir: Path
    installer: Path
    installer_hash: Path
    installer_digest: str
    source: Path
    source_hash: Path
    source_manifest: Path
    source_digest: str
    manifest_text: str
    resolved_ref: str
    directml_archive: Path | None = None
    directml_digest: str = ""


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
    evidence_docs_with_installer_hash = (
        "CLEAN_VM_AUTOMATED_EVIDENCE.md",
        "LEGAL_REVIEW_EVIDENCE_PACKET.md",
    )
    for name in evidence_docs_with_installer_hash:
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


def _result(name: str, failures: list[str]) -> ValidationResult:
    return ValidationResult(name=name, failures=tuple(failures))


def _build_release_asset_context(
    assets_dir: Path, app_version: str
) -> tuple[ReleaseAssetContext | None, ValidationResult]:
    failures: list[str] = []
    source_archives = sorted(assets_dir.glob(f"DeepLiveCamStudio-{app_version}-source-*.zip"))
    if len(source_archives) != 1:
        fail(
            f"release assets must contain exactly one source archive, found {len(source_archives)}",
            failures,
        )
        return None, _result("source-archive-selection", failures)

    installer = assets_dir / f"DeepLiveCamStudio-{app_version}-x64-setup.exe"
    source = source_archives[0]
    source_manifest = source.with_suffix(".manifest.md")
    manifest_text = (
        source_manifest.read_text(encoding="utf-8", errors="replace")
        if source_manifest.exists()
        else ""
    )
    context = ReleaseAssetContext(
        assets_dir=assets_dir,
        installer=installer,
        installer_hash=installer.with_suffix(installer.suffix + ".sha256"),
        installer_digest=sha256(installer) if installer.exists() else "",
        source=source,
        source_hash=Path(str(source) + ".sha256"),
        source_manifest=source_manifest,
        source_digest=sha256(source),
        manifest_text=manifest_text,
        resolved_ref=source_manifest_resolved_ref(manifest_text),
    )
    return context, _result("source-archive-selection", failures)


def _check_installer(context: ReleaseAssetContext) -> ValidationResult:
    failures: list[str] = []
    if not context.installer.exists():
        fail(f"release assets missing installer: {context.installer.name}", failures)
    elif read_sidecar_digest(context.installer_hash) != context.installer_digest:
        fail(
            f"release assets installer hash missing or mismatched: {context.installer_hash.name}",
            failures,
        )
    return _result("installer", failures)


def _check_source_archive(
    context: ReleaseAssetContext, require_git_ref: bool
) -> ValidationResult:
    failures: list[str] = []
    if read_sidecar_digest(context.source_hash) != context.source_digest:
        fail(
            f"release assets source hash missing or mismatched: {context.source_hash.name}",
            failures,
        )
    if not context.manifest_text:
        fail(
            f"release assets source manifest missing: {context.source_manifest.name}",
            failures,
        )
    elif require_git_ref and "Archive mode: `git-ref`" not in context.manifest_text:
        fail("release assets source manifest is not git-ref mode", failures)

    try:
        forbidden_entries = source_archive_has_forbidden_entries(context.source)
    except zipfile.BadZipFile:
        fail(
            f"release assets source archive is not a valid zip: {context.source.name}",
            failures,
        )
        forbidden_entries = []
    if forbidden_entries:
        for entry in forbidden_entries[:20]:
            print(f"[release-artifacts] forbidden release asset source entry: {entry}")
        fail(
            "release assets source archive contains forbidden model/checkpoint entries",
            failures,
        )
    return _result("source-archive", failures)


def _check_forbidden_asset_files(context: ReleaseAssetContext) -> ValidationResult:
    failures: list[str] = []
    forbidden_files = [
        path.name
        for path in context.assets_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES
    ]
    if forbidden_files:
        for name in forbidden_files[:20]:
            print(f"[release-artifacts] forbidden release asset file: {name}")
        fail(
            "release assets directory contains forbidden model/checkpoint files",
            failures,
        )
    return _result("model-exclusion", failures)


def _check_required_documents(context: ReleaseAssetContext) -> ValidationResult:
    failures: list[str] = []
    for doc in REQUIRED_RELEASE_DOCUMENTS:
        if not (context.assets_dir / doc).exists():
            fail(f"release assets missing required document: {doc}", failures)
    return _result("required-documents", failures)


def _check_directml_portable(
    context: ReleaseAssetContext, app_version: str, required: bool
) -> tuple[ReleaseAssetContext, ValidationResult]:
    failures: list[str] = []
    if not required:
        return context, _result("directml-portable", failures)
    archive, digest = _validate_directml_portable(
        context.assets_dir, app_version, failures
    )
    return (
        replace(context, directml_archive=archive, directml_digest=digest),
        _result("directml-portable", failures),
    )


def _check_sha256_manifest(context: ReleaseAssetContext) -> ValidationResult:
    failures: list[str] = []
    validate_sha256sums(context.assets_dir, failures)
    return _result("sha256-manifest", failures)


def _check_evidence_consistency(context: ReleaseAssetContext) -> ValidationResult:
    failures: list[str] = []
    if context.installer.exists():
        validate_release_evidence_consistency(
            assets_dir=context.assets_dir,
            installer_digest=context.installer_digest,
            source=context.source,
            source_digest=context.source_digest,
            failures=failures,
        )
    return _result("evidence-consistency", failures)


def _check_manual_gate_summary(context: ReleaseAssetContext) -> ValidationResult:
    failures: list[str] = []
    summary = context.assets_dir / "MANUAL_RELEASE_GATES.md"
    if not summary.exists():
        return _result("manual-gate-summary", failures)
    summary_text = summary.read_text(encoding="utf-8", errors="replace")
    for phrase in (
        "# Manual Windows Release Gate Summary",
        "`CLEAN_VM_VERIFICATION.md`",
        "`OBS_VIRTUAL_CAMERA_VERIFICATION.md`",
        "`LEGAL_REVIEW.md`",
        "## Open Items",
    ):
        if phrase not in summary_text:
            fail(f"MANUAL_RELEASE_GATES.md missing phrase: {phrase}", failures)
    return _result("manual-gate-summary", failures)


def _check_release_asset_manifest(context: ReleaseAssetContext) -> ValidationResult:
    failures: list[str] = []
    manifest = context.assets_dir / "RELEASE_ASSETS.md"
    if not manifest.exists():
        return _result("release-asset-manifest", failures)
    text = manifest.read_text(encoding="utf-8", errors="replace")
    listed_paths = [
        context.installer,
        context.installer_hash,
        context.source,
        context.source_hash,
        context.source_manifest,
    ]
    if context.directml_archive:
        listed_paths.extend(
            (
                context.directml_archive,
                Path(str(context.directml_archive) + ".sha256"),
            )
        )
    for path in listed_paths:
        if f"`{path.name}`" not in text:
            fail(f"RELEASE_ASSETS.md does not list: {path.name}", failures)
    for doc in REQUIRED_RELEASE_DOCUMENTS:
        if f"`{doc}`" not in text:
            fail(f"RELEASE_ASSETS.md does not list required document: {doc}", failures)
    if "Do not upload model/checkpoint files" not in text:
        fail("RELEASE_ASSETS.md missing model/checkpoint upload warning", failures)
    if context.resolved_ref and f"Source ref: `{context.resolved_ref}`" not in text:
        fail("RELEASE_ASSETS.md source ref does not match source manifest", failures)
    return _result("release-asset-manifest", failures)


def _release_notes_expected_phrases(context: ReleaseAssetContext) -> tuple[str, ...]:
    phrases = (
        f"`{context.installer.name}`",
        f"`{context.installer_digest}`",
        f"`{context.source.name}`",
        f"`{context.source_digest}`",
        "Deep-Live-Cam is licensed under AGPL-3.0",
        "The installer intentionally does not include model/checkpoint files",
        "This release candidate is not publish-approved",
        "Completed local evidence is included in the uploaded release documents:",
        "Remaining publish blockers:",
        "Authorized legal review for dependency, model-license, and redistribution obligations.",
    )
    if context.directml_archive:
        phrases += (
            f"`{context.directml_archive.name}`",
            f"`{context.directml_digest}`",
        )
    return phrases


def _check_release_notes(context: ReleaseAssetContext) -> ValidationResult:
    failures: list[str] = []
    release_notes = context.assets_dir / "RELEASE_NOTES.md"
    if not release_notes.exists():
        return _result("release-notes", failures)
    text = release_notes.read_text(encoding="utf-8", errors="replace")
    for phrase in _release_notes_expected_phrases(context):
        if phrase not in text:
            fail(f"RELEASE_NOTES.md missing phrase: {phrase}", failures)
    if context.resolved_ref and f"`{context.resolved_ref}`" not in text:
        fail("RELEASE_NOTES.md source ref does not match source manifest", failures)
    if "listed in the uploaded `RELEASE_ASSETS.md`" in text:
        fail("RELEASE_NOTES.md still contains manifest cross-reference placeholders", failures)
    if "This release candidate is not publish-approved until these checks are complete and documented:" in text:
        fail(
            "RELEASE_NOTES.md uses stale pre-publish wording that does not separate completed evidence from remaining blockers",
            failures,
        )
    return _result("release-notes", failures)


def evaluate_release_asset_checks(
    assets_dir: Path,
    app_version: str,
    require_git_ref: bool,
    require_directml_portable: bool,
) -> tuple[ValidationResult, ...]:
    """Evaluate curated release assets as stable, named validation checks."""
    if not assets_dir.exists():
        failures: list[str] = []
        fail(f"missing release assets directory: {assets_dir}", failures)
        return (_result("release-assets-directory", failures),)

    context, selection = _build_release_asset_context(assets_dir, app_version)
    if context is None:
        return (selection,)
    context, directml = _check_directml_portable(
        context, app_version, require_directml_portable
    )
    return (
        selection,
        _check_installer(context),
        _check_source_archive(context, require_git_ref),
        _check_forbidden_asset_files(context),
        _check_required_documents(context),
        directml,
        _check_sha256_manifest(context),
        _check_evidence_consistency(context),
        _check_manual_gate_summary(context),
        _check_release_asset_manifest(context),
        _check_release_notes(context),
    )


def validate_release_assets_dir(
    assets_dir: Path,
    app_version: str,
    require_git_ref: bool,
    require_directml_portable: bool,
    failures: list[str],
) -> None:
    for result in evaluate_release_asset_checks(
        assets_dir,
        app_version,
        require_git_ref,
        require_directml_portable,
    ):
        failures.extend(result.failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Windows release artifact set.")
    parser.add_argument("--output-dir", default="build/windows/installer", help="Installer output directory.")
    parser.add_argument("--release-assets-dir", help="Optional curated GitHub Release asset directory to validate.")
    parser.add_argument("--app-version", default="2.2.3", help="Application version.")
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
