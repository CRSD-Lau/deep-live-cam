"""Protect public compression while allowing faster isolated installer checks."""

import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def inno_compiler():
    command = shutil.which("iscc.exe")
    if command:
        return command
    for variable in ("LOCALAPPDATA", "ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(variable)
        if not base:
            continue
        relative = "Programs/Inno Setup 6/ISCC.exe" if variable == "LOCALAPPDATA" else "Inno Setup 6/ISCC.exe"
        candidate = Path(base) / relative
        if candidate.is_file():
            return str(candidate)
    pytest.skip("Inno Setup is not available")


def test_fixture_override_is_restricted_to_isolated_candidate_compilation():
    installer = (ROOT / "build/windows/installer.iss").read_text(encoding="utf-8")
    assert "Compression={#InstallerCompression}\n" in installer
    assert "SolidCompression=yes\n" in installer
    script = (ROOT / "build/windows/test_installer.ps1").read_text(encoding="utf-8")
    candidate_command = next(
        line for line in script.splitlines()
        if line.lstrip().startswith("& $IsccPath") and "/DOutputBaseFilename=" in line
    )

    assert '"/DInstallerCompression=$FixtureCompression"' in candidate_command
    assert '"/DAppId=$TestDirectiveAppId"' in candidate_command
    assert '"/DAppIdRegistryValue=$TestAppId"' in candidate_command
    assert '[string]$FixtureCompression = "lzma2/fast"' in script
    assert '[ValidateSet("lzma2/fast", "lzma2/normal", "lzma2/max", "lzma2/ultra64")]' in script
    public_packager = (ROOT / "build/windows/package_installer.ps1").read_text(encoding="utf-8")
    assert "/DInstallerCompression=" not in public_packager


@pytest.mark.parametrize("override", [None, "lzma2/fast"])
def test_inno_compiles_public_default_and_fixture_override(tmp_path, override):
    """Compile the real script with a tiny payload; never launch an installer."""
    compiler = inno_compiler()
    payload = tmp_path / "payload"
    payload.mkdir()
    for name in ("DeepLiveCamStudio.exe", "DeepLiveCamStudioCLI.exe", "LICENSE"):
        (payload / name).write_text("Isolated compiler fixture\n", encoding="ascii")
    output = tmp_path / "output"
    output.mkdir()
    expected = override or "lzma2/ultra64"
    wrapper = tmp_path / "compression-check.iss"
    wrapper.write_text(
        f'#include "{(ROOT / "build/windows/installer.iss").as_posix()}"\n'
        f'#if InstallerCompression != "{expected}"\n'
        '#error Unexpected installer compression mode\n'
        '#endif\n',
        encoding="utf-8",
    )
    app_id = "{" + str(uuid.uuid4()).upper() + "}"
    command = [
        compiler,
        "/Qp",
        f"/DRepoRoot={ROOT}",
        f"/DDistDir={payload}",
        f"/DOutputDir={output}",
        "/DOutputBaseFilename=compression-fixture",
        f"/DAppId={{{app_id}",
        f"/DAppIdRegistryValue={app_id}",
    ]
    if override:
        command.append(f"/DInstallerCompression={override}")
    command.append(str(wrapper))
    completed = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (output / "compression-fixture.exe").stat().st_size > 0
