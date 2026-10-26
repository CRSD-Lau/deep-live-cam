"""Exercise the real assembler and validator before an expensive binary build."""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from modules.metadata import version as VERSION
from tools import validate_windows_release_artifacts as validator


ROOT = Path(__file__).resolve().parents[1]
REF = "a" * 40


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fixture_repository(tmp_path, directml):
    repo = tmp_path / "fixture-repo"
    for path in [*ROOT.glob("*.md"), ROOT / "LICENSE", *ROOT.glob("LICENSES/*.md")]:
        target = repo / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    for name in ("tools/validate_windows_release_artifacts.py", "tools/summarize_manual_release_gates.py",
                 "build/windows/assemble_release_assets.ps1", "modules/metadata.py"):
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    write(repo / "RELEASE_VERIFICATION.md", "Local installer automation passed: NO (non-executable fixture)\n"
          "Public-release source archive from clean Git ref: NO (fixture)\n"
          "Ready to publish without remaining manual gates: NO\n")
    installer = repo / f"build/windows/installer/DeepLiveCamStudio-{VERSION}-x64-setup.exe"
    installer.parent.mkdir(parents=True)
    installer.write_bytes(b"NON-EXECUTABLE ASSEMBLY TEST FIXTURE")
    write(Path(str(installer) + ".sha256"), validator.sha256(installer))
    source = installer.parent / f"DeepLiveCamStudio-{VERSION}-source-{REF[:12]}.zip"
    with zipfile.ZipFile(source, "w") as archive:
        for entry in validator.REQUIRED_SOURCE_ENTRIES:
            archive.writestr(f"DeepLiveCamStudio-{VERSION}-source/{entry}", b"source fixture")
    write(Path(str(source) + ".sha256"), validator.sha256(source))
    write(source.with_suffix(".manifest.md"), f"Archive mode: `git-ref`\nGit ref resolved: `{REF}`\n" +
          "\n".join(f"- [x] `{entry}`" for entry in validator.REQUIRED_SOURCE_ENTRIES) +
          "\n- [x] No `.onnx`, `.pth`, `.safetensors`, `models/`, `checkpoints/`, or model-cache entries were found.\n")
    if directml:
        portable = repo / f"portable/DeepLiveCamStudio-{VERSION}-DirectML-x64-portable.zip"
        portable.parent.mkdir()
        with zipfile.ZipFile(portable, "w") as archive:
            for entry in ("DeepLiveCamStudio.exe", "DeepLiveCamStudioCLI.exe", "README.md", "CHANGELOG.md",
                          "LICENSE", "_internal/sklearn/.libs/vcomp140.dll",
                          "LICENSES/THIRD_PARTY_LICENSES/pillow-13.0.0/licenses/LICENSE",
                          "LICENSES/THIRD_PARTY_LICENSES/certifi-2026.10.23/licenses/LICENSE",
                          "LICENSES/THIRD_PARTY_LICENSES/filelock-4.2.4/licenses/LICENSE"):
                archive.writestr(entry, b"NON-EXECUTABLE PORTABLE FIXTURE")
            archive.writestr("LICENSES/PYTHON_DEPENDENCIES_DIRECTML.md", "FRESH DIRECTML INVENTORY FIXTURE")
        write(Path(str(portable) + ".sha256"), validator.sha256(portable))
    return repo


@pytest.mark.parametrize("directml", [False, True])
def test_current_pending_template_passes_real_assembly_and_all_release_validators(tmp_path, directml):
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        pytest.skip("PowerShell required to execute the actual release assembler")
    repo = fixture_repository(tmp_path, directml)
    args = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            str(repo / "build/windows/assemble_release_assets.ps1"), "-AppVersion", VERSION,
            "-Python", sys.executable, "-RequireGitRefSource"]
    if directml:
        args += ["-PortableDir", str(repo / "portable")]
    result = subprocess.run(args, cwd=repo, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assets = repo / f"build/windows/release-assets/{VERSION}"
    validated = subprocess.run(
        [sys.executable, str(ROOT / "tools/validate_windows_release_artifacts.py"), "--repo-root", str(repo),
         "--output-dir", "build/windows/installer", "--release-assets-dir", str(assets),
         "--app-version", VERSION, "--require-git-ref-source"] +
        (["--require-directml-portable"] if directml else []), capture_output=True, text=True,
    )
    assert validated.returncode == 0, validated.stdout + validated.stderr
    text = (assets / "RELEASE_NOTES.md").read_text(encoding="utf-8-sig")
    assert f"`{REF}`" in text and "This release candidate is not publish-approved" in text
    assert "listed in the uploaded `RELEASE_ASSETS.md`" not in text
    assert "{{DIRECTML" not in text and "Remaining publish blockers:" in text
    gates = (assets / "MANUAL_RELEASE_GATES.md").read_text(encoding="utf-8-sig")
    assert "BLOCKED" in gates and "PENDING" in gates
    if directml:
        assert (assets / "PYTHON_DEPENDENCIES_DIRECTML.md").read_text() == "FRESH DIRECTML INVENTORY FIXTURE"
