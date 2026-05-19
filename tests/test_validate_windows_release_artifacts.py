import zipfile
from pathlib import Path

from tools import validate_windows_release_artifacts as validator


def write_file(path, content="ok"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
