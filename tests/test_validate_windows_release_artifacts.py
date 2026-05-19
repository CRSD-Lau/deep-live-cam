import zipfile
from pathlib import Path

from tools import validate_windows_release_artifacts as validator


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
    installer = output_dir / "DeepLiveCamStudio-2.1.5-x64-setup.exe"
    installer.parent.mkdir(parents=True, exist_ok=True)
    installer.write_bytes(b"installer")
    write_file(installer.with_suffix(installer.suffix + ".sha256"), f"{validator.sha256(installer)}  {installer.name}\n")

    source = output_dir / "DeepLiveCamStudio-2.1.5-source-testref.zip"
    with zipfile.ZipFile(source, "w") as archive:
        for entry in validator.REQUIRED_SOURCE_ENTRIES:
            if entry == omit_required_entry:
                continue
            archive.writestr(f"DeepLiveCamStudio-2.1.5-source/{entry}", "source")
        if extra_source_entry_name:
            archive.writestr(extra_source_entry_name, "source")
    write_file(source.with_suffix(source.suffix + ".sha256"), f"{validator.sha256(source)}  {source.name}\n")
    required_manifest_lines = "\n".join(f"- [x] `{entry}`" for entry in validator.REQUIRED_SOURCE_ENTRIES if entry != omit_required_entry)
    write_file(
        source.with_suffix(".manifest.md"),
        f"Archive mode: `git-ref`\n{required_manifest_lines}\n- [x] No `.onnx`, `.pth`, `.safetensors`, `models/`, `checkpoints/`, or model-cache entries were found.\n",
    )
    write_file(
        tmp_path / "RELEASE_VERIFICATION.md",
        "Local installer automation passed:\nPublic-release source archive from clean Git ref:\nReady to publish without remaining manual gates:\n",
    )
    return installer, source


def write_release_assets(tmp_path):
    installer, source = write_artifacts(tmp_path)
    assets_dir = tmp_path / "build" / "windows" / "release-assets" / "2.1.5"
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
        "RELEASE_VERIFICATION.md",
        "RELEASE_CHECKLIST.md",
        "RELEASE_COMPLETION_AUDIT.md",
        "RELEASE_CUTOVER_PLAN.md",
        "RELEASE_CUTOVER_STATUS.md",
        "CLEAN_RELEASE_WORKTREE_VERIFICATION.md",
        "README.md",
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
        "WINDOWS_BUNDLE_MANIFEST.md",
    ):
        content = MANUAL_GATE_SUMMARY if doc == "MANUAL_RELEASE_GATES.md" else "doc"
        write_file(assets_dir / doc, content)
    write_file(
        assets_dir / "RELEASE_NOTES.md",
        "\n".join(
            (
                f"`{installer.name}`",
                f"`{validator.sha256(installer)}`",
                f"`{source.name}`",
                f"`{validator.sha256(source)}`",
                "Deep-Live-Cam is licensed under AGPL-3.0",
                "The installer intentionally does not include model/checkpoint files",
                "This release candidate is not publish-approved",
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
            "LICENSE",
            "RELEASE_NOTES.md",
            "RELEASE_NOTES_TEMPLATE.md",
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
            "WINDOWS_BUNDLE_MANIFEST.md",
        )
    )
    write_file(
        assets_dir / "RELEASE_ASSETS.md",
        f"{upload_lines}\n{doc_upload_lines}\nDo not upload model/checkpoint files unless approved.\n",
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


def test_validate_release_artifacts_accepts_complete_artifact_set(tmp_path, monkeypatch):
    write_artifacts(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert validator.main([]) == 0


def test_validate_release_artifacts_rejects_forbidden_source_entries(tmp_path, monkeypatch):
    write_artifacts(tmp_path, extra_source_entry_name="DeepLiveCamStudio-2.1.5-source/models/model.onnx")
    monkeypatch.chdir(tmp_path)

    assert validator.main([]) == 1


def test_validate_release_artifacts_rejects_missing_required_source_entries(tmp_path, monkeypatch):
    write_artifacts(tmp_path, omit_required_entry="RELEASE_COMPLETION_AUDIT.md")
    monkeypatch.chdir(tmp_path)

    assert validator.main([]) == 1


def test_validate_release_artifacts_prefers_git_ref_source_when_required(tmp_path, monkeypatch):
    write_artifacts(tmp_path)
    output_dir = tmp_path / "build" / "windows" / "installer"
    git_ref_source = output_dir / "DeepLiveCamStudio-2.1.5-source-testref.zip"
    draft_source = output_dir / "DeepLiveCamStudio-2.1.5-source-worktree-testref.zip"
    draft_source.write_bytes(git_ref_source.read_bytes())
    write_file(draft_source.with_suffix(draft_source.suffix + ".sha256"), f"{validator.sha256(draft_source)}  {draft_source.name}\n")
    write_file(
        draft_source.with_suffix(".manifest.md"),
        git_ref_source.with_suffix(".manifest.md").read_text(encoding="utf-8").replace(
            "Archive mode: `git-ref`", "Archive mode: `draft-working-tree`"
        ),
    )
    monkeypatch.chdir(tmp_path)

    assert validator.main(["--require-git-ref-source"]) == 0


def test_validate_release_artifacts_accepts_curated_release_assets(tmp_path, monkeypatch):
    write_release_assets(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert validator.main(["--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.5"]) == 0


def test_validate_release_artifacts_rejects_stale_extra_source_archive_in_assets(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    source = assets_dir / "DeepLiveCamStudio-2.1.5-source-testref.zip"
    stale_source = assets_dir / "DeepLiveCamStudio-2.1.5-source-stale.zip"
    stale_source.write_bytes(source.read_bytes())
    write_file(stale_source.with_suffix(stale_source.suffix + ".sha256"), f"{validator.sha256(stale_source)}  {stale_source.name}\n")
    write_file(stale_source.with_suffix(".manifest.md"), source.with_suffix(".manifest.md").read_text(encoding="utf-8"))
    monkeypatch.chdir(tmp_path)

    assert validator.main(["--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.5"]) == 1


def test_validate_release_artifacts_rejects_blank_manual_gate_summary(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    write_file(assets_dir / "MANUAL_RELEASE_GATES.md", "placeholder\n")
    monkeypatch.chdir(tmp_path)

    assert validator.main(["--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.5"]) == 1


def test_validate_release_artifacts_rejects_required_doc_missing_from_manifest(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    manifest = assets_dir / "RELEASE_ASSETS.md"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("- `COMPLIANCE.md`\n", ""),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert validator.main(["--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.5"]) == 1


def test_validate_release_artifacts_rejects_bad_sha256sums(tmp_path, monkeypatch):
    assets_dir = write_release_assets(tmp_path)
    sums = assets_dir / "SHA256SUMS.txt"
    sums.write_text(
        sums.read_text(encoding="ascii").replace("RELEASE_ASSETS.md", "MISSING.md"),
        encoding="ascii",
    )
    monkeypatch.chdir(tmp_path)

    assert validator.main(["--require-git-ref-source", "--release-assets-dir", "build/windows/release-assets/2.1.5"]) == 1
