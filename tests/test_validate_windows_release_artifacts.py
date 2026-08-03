import zipfile
from pathlib import Path

from tools import validate_windows_release_artifacts as validator


def version_args(*args):
    return ["--app-version", "2.1.7", *args]


def write_file(path, content="ok"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


MANUAL_GATE_SUMMARY = """# Manual Windows Release Gate Summary

## Status

- BLOCKED: `CLEAN_VM_VERIFICATION.md` status=`PENDING` open_items=`10`
- BLOCKED: `OBS_VIRTUAL_CAMERA_VERIFICATION.md` status=`PENDING` open_items=`6`
- BLOCKED: `LEGAL_REVIEW.md` status=`PENDING` open_items=`13`

## Open Items

- still pending
"""


def write_artifacts(tmp_path, extra_source_entry_name=None, omit_required_entry=None):
    output_dir = tmp_path / "build" / "windows" / "installer"
    installer = output_dir / "DeepLiveCamStudio-2.1.7-x64-setup.exe"
    installer.parent.mkdir(parents=True, exist_ok=True)
    installer.write_bytes(b"installer")
    write_file(installer.with_suffix(installer.suffix + ".sha256"), f"{validator.sha256(installer)}  {installer.name}\n")

    source = output_dir / "DeepLiveCamStudio-2.1.7-source-testref.zip"
    with zipfile.ZipFile(source, "w") as archive:
        for entry in validator.REQUIRED_SOURCE_ENTRIES:
            if entry == omit_required_entry:
                continue
            archive.writestr(f"DeepLiveCamStudio-2.1.7-source/{entry}", "source")
        if extra_source_entry_name:
            archive.writestr(extra_source_entry_name, "source")
    write_file(source.with_suffix(source.suffix + ".sha256"), f"{validator.sha256(source)}  {source.name}\n")
    required_manifest_lines = "\n".join(f"- [x] `{entry}`" for entry in validator.REQUIRED_SOURCE_ENTRIES if entry != omit_required_entry)
    write_file(
        source.with_suffix(".manifest.md"),
        f"Archive mode: `git-ref`\nGit ref resolved: `testrefresolved`\n{required_manifest_lines}\n- [x] No `.onnx`, `.pth`, `.safetensors`, `models/`, `checkpoints/`, or model-cache entries were found.\n",
    )
    write_file(
        tmp_path / "RELEASE_VERIFICATION.md",
        "Local installer automation passed:\nPublic-release source archive from clean Git ref:\nReady to publish without remaining manual gates:\n",
    )
    return installer, source


def write_release_assets(tmp_path):
    installer, source = write_artifacts(tmp_path)
    assets_dir = tmp_path / "build" / "windows" / "release-assets" / "2.1.7"
    assets_dir.mkdir(parents=True)
    files = [
        installer,
        installer.with_suffix(installer.suffix + ".sha256"),
        source,
        source.with_suffix(source.suffix + ".sha256"),
        source.with_suffix(".manifest.md"),
    ]
    for path in files:
        (assets_dir / path.name).write_bytes(path.read_bytes())
    for doc in (
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
        "CLEAN_VM_AUTOMATED_EVIDENCE.md",
        "OBS_VIRTUAL_CAMERA_AUTOMATED_EVIDENCE.md",
        "LEGAL_REVIEW_EVIDENCE_PACKET.md",
    ):
        content = MANUAL_GATE_SUMMARY if doc == "MANUAL_RELEASE_GATES.md" else "doc"
        if doc == "CLEAN_VM_AUTOMATED_EVIDENCE.md":
            content = f"Installer SHA-256: `{validator.sha256(installer)}`\n"
        if doc == "LEGAL_REVIEW_EVIDENCE_PACKET.md":
            content = "\n".join(
                (
                    f"- Installer SHA-256: `{validator.sha256(installer)}`",
                    f"- Source archive: `{source.name}`",
                    f"- Source archive SHA-256: `{validator.sha256(source)}`",
                )
            )
        write_file(assets_dir / doc, content)
    write_file(
        assets_dir / "RELEASE_NOTES.md",
        "\n".join(
            (
                f"`{installer.name}`",
                f"`{validator.sha256(installer)}`",
                f"`{source.name}`",
                f"`{validator.sha256(source)}`",
                "`testrefresolved`",
                "Deep-Live-Cam is licensed under AGPL-3.0",
                "The installer intentionally does not include model/checkpoint files",
                "This release candidate is not publish-approved",
                "Completed local evidence is included in the uploaded release documents:",
                "Remaining publish blockers:",
                "Authorized legal review for dependency, model-license, and redistribution obligations.",
            )
        ),
    )
    upload_lines = "\n".join(f"- `{path.name}`" for path in files)
    doc_upload_lines = "\n".join(
        f"- `{doc}`"
        for doc in (
            "COMPLIANCE.md",
            "MANUAL_RELEASE_GATES.md",
            "RELEASE_ASSETS.md",
            "SHA256SUMS.txt",
            "RELEASE_CHECKLIST.md",
            "RELEASE_COMPLETION_AUDIT.md",
            "RELEASE_CUTOVER_PLAN.md",
            "RELEASE_CUTOVER_STATUS.md",
            "CLEAN_RELEASE_WORKTREE_VERIFICATION.md",
            "README.md",
            "CHANGELOG.md",
            "LICENSE",
            "RELEASE_NOTES.md",
            "RELEASE_NOTES_TEMPLATE.md",
            "RELEASE_PUBLISH_HANDOFF.md",
            "RELEASE_SOURCE_PREP.md",
            "RELEASE_REPORT.md",
            "CLEAN_VM_VERIFICATION.md",
            "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
            "LEGAL_REVIEW.md",
            "MODEL_DOWNLOAD_VERIFICATION.md",
            "PROCESSING_VERIFICATION.md",
            "RELEASE_VERIFICATION.md",
            "THIRD_PARTY_NOTICES.md",
            "BUNDLED_BINARY_OBLIGATIONS.md",
            "MODEL_LICENSE_AUDIT.md",
            "PYTHON_DEPENDENCIES.md",
            "PYTHON_DEPENDENCIES_DIRECTML.md",
            "WINDOWS_BUNDLE_MANIFEST.md",
            "CLEAN_VM_AUTOMATED_EVIDENCE.md",
            "OBS_VIRTUAL_CAMERA_AUTOMATED_EVIDENCE.md",
            "LEGAL_REVIEW_EVIDENCE_PACKET.md",
        )
    )
    write_file(
        assets_dir / "RELEASE_ASSETS.md",
        f"Source ref: `testrefresolved`\n{upload_lines}\n{doc_upload_lines}\nDo not upload model/checkpoint files unless approved.\n",
    )
    sums_lines = []
    for path in sorted(assets_dir.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            sums_lines.append(f"{validator.sha256(path)}  {path.name}")
    write_file(assets_dir / "SHA256SUMS.txt", "\n".join(sums_lines) + "\n")
    return assets_dir


def parse_package_source_required_entries():
    script = Path("build/windows/package_source.ps1").read_text(encoding="utf-8")
    start = script.index("$RequiredEntries = @(")
    end = script.index(")", start)
    entries = []
    for line in script[start:end].splitlines():
        stripped = line.strip()
        if stripped.startswith('"') and stripped.rstrip(",").endswith('"'):
            entries.append(stripped.rstrip(",").strip('"'))
    return tuple(entries)


def test_validator_required_source_entries_match_package_source_script():
    assert validator.REQUIRED_SOURCE_ENTRIES == parse_package_source_required_entries()


def write_directml_portable(assets_dir, *, omit_entry=None, extra_entry=None):
    archive_path = assets_dir / "DeepLiveCamStudio-2.1.7-DirectML-x64-portable.zip"
    required_entries = (
        "DeepLiveCamStudio.exe",
        "DeepLiveCamStudioCLI.exe",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "_internal/sklearn/.libs/vcomp140.dll",
    )
    with zipfile.ZipFile(archive_path, "w") as archive:
        for entry in required_entries:
            if entry != omit_entry:
                archive.writestr(entry, "portable")
        if extra_entry:
            archive.writestr(extra_entry, "forbidden")
    write_file(
        Path(str(archive_path) + ".sha256"),
        f"{validator.sha256(archive_path)}  {archive_path.name}\n",
    )
    return archive_path


def refresh_sha256sums(assets_dir):
    sums_lines = []
    for path in sorted(assets_dir.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            sums_lines.append(f"{validator.sha256(path)}  {path.name}")
    write_file(assets_dir / "SHA256SUMS.txt", "\n".join(sums_lines) + "\n")


def test_directml_portable_validator_accepts_complete_archive(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    archive_path = write_directml_portable(assets_dir)
    failures = []

    validated_path, digest = validator._validate_directml_portable(
        assets_dir, "2.1.7", failures
    )

    assert failures == []
    assert validated_path == archive_path
    assert digest == validator.sha256(archive_path)


def test_directml_portable_validator_requires_hidden_runtime_dll(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    write_directml_portable(
        assets_dir, omit_entry="_internal/sklearn/.libs/vcomp140.dll"
    )
    failures = []

    validator._validate_directml_portable(assets_dir, "2.1.7", failures)

    assert any("vcomp140.dll" in failure for failure in failures)


def test_directml_portable_validator_rejects_model_weights(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    write_directml_portable(assets_dir, extra_entry="models/inswapper_128.onnx")
    failures = []

    validator._validate_directml_portable(assets_dir, "2.1.7", failures)

    assert any("forbidden model/checkpoint" in failure for failure in failures)


def test_named_release_asset_checks_pass_for_complete_cuda_assets(tmp_path):
    assets_dir = write_release_assets(tmp_path)

    results = validator.evaluate_release_asset_checks(
        assets_dir,
        "2.1.7",
        require_git_ref=True,
        require_directml_portable=False,
    )

    assert [result.name for result in results] == [
        "source-archive-selection",
        "installer",
        "source-archive",
        "model-exclusion",
        "required-documents",
        "directml-portable",
        "sha256-manifest",
        "evidence-consistency",
        "manual-gate-summary",
        "release-asset-manifest",
        "release-notes",
    ]
    assert all(result.passed for result in results)


def test_named_release_asset_checks_pass_for_combined_directml_assets(tmp_path):
    assets_dir = write_release_assets(tmp_path)
    directml_archive = write_directml_portable(assets_dir)
    directml_hash = Path(str(directml_archive) + ".sha256")
    with (assets_dir / "RELEASE_ASSETS.md").open("a", encoding="utf-8") as handle:
        handle.write(f"- `{directml_archive.name}`\n- `{directml_hash.name}`\n")
    with (assets_dir / "RELEASE_NOTES.md").open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n`{directml_archive.name}`\n`{validator.sha256(directml_archive)}`\n"
        )
    refresh_sha256sums(assets_dir)

    results = validator.evaluate_release_asset_checks(
        assets_dir,
        "2.1.7",
        require_git_ref=True,
        require_directml_portable=True,
    )

    assert all(result.passed for result in results)


def test_named_release_asset_check_attributes_manual_gate_failures(tmp_path):
    assets_dir = write_release_assets(tmp_path)
    write_file(assets_dir / "MANUAL_RELEASE_GATES.md", "placeholder\n")
    refresh_sha256sums(assets_dir)

    results = validator.evaluate_release_asset_checks(
        assets_dir,
        "2.1.7",
        require_git_ref=True,
        require_directml_portable=False,
    )

    failed = {result.name: result.failures for result in results if not result.passed}
    assert failed.keys() == {"manual-gate-summary"}
    assert failed["manual-gate-summary"] == (
        "MANUAL_RELEASE_GATES.md missing phrase: # Manual Windows Release Gate Summary",
        "MANUAL_RELEASE_GATES.md missing phrase: `CLEAN_VM_VERIFICATION.md`",
        "MANUAL_RELEASE_GATES.md missing phrase: `OBS_VIRTUAL_CAMERA_VERIFICATION.md`",
        "MANUAL_RELEASE_GATES.md missing phrase: `LEGAL_REVIEW.md`",
        "MANUAL_RELEASE_GATES.md missing phrase: ## Open Items",
    )


def test_validate_release_artifacts_accepts_complete_artifact_set(tmp_path, monkeypatch):
    write_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args()) == 0


def test_validate_release_artifacts_rejects_forbidden_source_entries(tmp_path, monkeypatch):
    write_artifacts(tmp_path, extra_source_entry_name="DeepLiveCamStudio-2.1.7-source/models/model.onnx")
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args()) == 1


def test_validate_release_artifacts_rejects_missing_required_source_entries(tmp_path, monkeypatch):
    write_artifacts(tmp_path, omit_required_entry="RELEASE_COMPLETION_AUDIT.md")
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args()) == 1


def test_validate_release_artifacts_prefers_git_ref_source_when_required(tmp_path, monkeypatch):
    write_artifacts(tmp_path)
    output_dir = tmp_path / "build" / "windows" / "installer"
    git_ref_source = output_dir / "DeepLiveCamStudio-2.1.7-source-testref.zip"
    draft_source = output_dir / "DeepLiveCamStudio-2.1.7-source-worktree-testref.zip"
    draft_source.write_bytes(git_ref_source.read_bytes())
    write_file(draft_source.with_suffix(draft_source.suffix + ".sha256"), f"{validator.sha256(draft_source)}  {draft_source.name}\n")
    write_file(
        draft_source.with_suffix(".manifest.md"),
        git_ref_source.with_suffix(".manifest.md").read_text(encoding="utf-8").replace(
            "Archive mode: `git-ref`", "Archive mode: `draft-working-tree`"
        ),
    )
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source")) == 0


def test_validate_release_artifacts_accepts_curated_release_assets(tmp_path, monkeypatch):
    write_release_assets(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 0


def test_validate_release_artifacts_accepts_headless_candidate_without_optional_manual_evidence(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    optional_evidence = (
        "CLEAN_VM_AUTOMATED_EVIDENCE.md",
        "OBS_VIRTUAL_CAMERA_AUTOMATED_EVIDENCE.md",
        "LEGAL_REVIEW_EVIDENCE_PACKET.md",
    )
    manifest = assets_dir / "RELEASE_ASSETS.md"
    manifest_text = manifest.read_text(encoding="utf-8")
    for name in optional_evidence:
        (assets_dir / name).unlink()
        manifest_text = manifest_text.replace(f"- `{name}`\n", "")
    manifest.write_text(manifest_text, encoding="utf-8")

    sums_lines = []
    for path in sorted(assets_dir.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            sums_lines.append(f"{validator.sha256(path)}  {path.name}")
    write_file(assets_dir / "SHA256SUMS.txt", "\n".join(sums_lines) + "\n")
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 0


def test_validate_release_artifacts_rejects_stale_extra_source_archive_in_assets(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    source = assets_dir / "DeepLiveCamStudio-2.1.7-source-testref.zip"
    stale_source = assets_dir / "DeepLiveCamStudio-2.1.7-source-stale.zip"
    stale_source.write_bytes(source.read_bytes())
    write_file(stale_source.with_suffix(stale_source.suffix + ".sha256"), f"{validator.sha256(stale_source)}  {stale_source.name}\n")
    write_file(stale_source.with_suffix(".manifest.md"), source.with_suffix(".manifest.md").read_text(encoding="utf-8"))
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 1


def test_validate_release_artifacts_rejects_blank_manual_gate_summary(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    write_file(assets_dir / "MANUAL_RELEASE_GATES.md", "placeholder\n")
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 1


def test_validate_release_artifacts_rejects_required_doc_missing_from_manifest(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    manifest = assets_dir / "RELEASE_ASSETS.md"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("- `COMPLIANCE.md`\n", ""),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 1


def test_validate_release_artifacts_rejects_bad_sha256sums(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    sums = assets_dir / "SHA256SUMS.txt"
    sums.write_text(
        sums.read_text(encoding="ascii").replace("RELEASE_ASSETS.md", "MISSING.md"),
        encoding="ascii",
    )
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 1


def test_validate_release_artifacts_rejects_stale_clean_vm_evidence_hash(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    write_file(assets_dir / "CLEAN_VM_AUTOMATED_EVIDENCE.md", "Installer SHA-256: `STALE`\n")
    sums_lines = []
    for path in sorted(assets_dir.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            sums_lines.append(f"{validator.sha256(path)}  {path.name}")
    write_file(assets_dir / "SHA256SUMS.txt", "\n".join(sums_lines) + "\n")
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 1


def test_validate_release_artifacts_rejects_stale_legal_evidence_source(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    installer = assets_dir / "DeepLiveCamStudio-2.1.7-x64-setup.exe"
    write_file(
        assets_dir / "LEGAL_REVIEW_EVIDENCE_PACKET.md",
        "\n".join(
            (
                f"- Installer SHA-256: `{validator.sha256(installer)}`",
                "- Source archive: `DeepLiveCamStudio-2.1.7-source-old.zip`",
                "- Source archive SHA-256: `OLDHASH`",
            )
        ),
    )
    sums_lines = []
    for path in sorted(assets_dir.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            sums_lines.append(f"{validator.sha256(path)}  {path.name}")
    write_file(assets_dir / "SHA256SUMS.txt", "\n".join(sums_lines) + "\n")
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 1


def test_validate_release_artifacts_rejects_stale_release_notes_source_ref(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    release_notes = assets_dir / "RELEASE_NOTES.md"
    release_notes.write_text(
        release_notes.read_text(encoding="utf-8").replace("`testrefresolved`", "`oldref`"),
        encoding="utf-8",
    )
    sums_lines = []
    for path in sorted(assets_dir.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            sums_lines.append(f"{validator.sha256(path)}  {path.name}")
    write_file(assets_dir / "SHA256SUMS.txt", "\n".join(sums_lines) + "\n")
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 1


def test_validate_release_artifacts_rejects_stale_release_assets_source_ref(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    asset_manifest = assets_dir / "RELEASE_ASSETS.md"
    asset_manifest.write_text(
        asset_manifest.read_text(encoding="utf-8").replace("`testrefresolved`", "`oldref`"),
        encoding="utf-8",
    )
    sums_lines = []
    for path in sorted(assets_dir.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            sums_lines.append(f"{validator.sha256(path)}  {path.name}")
    write_file(assets_dir / "SHA256SUMS.txt", "\n".join(sums_lines) + "\n")
    monkeypatch.chdir(tmp_path)

    assert validator.main(version_args("--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.7")) == 1
