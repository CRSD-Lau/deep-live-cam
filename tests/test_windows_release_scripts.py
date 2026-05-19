import shutil
import subprocess
from pathlib import Path

import pytest


WINDOWS_RELEASE_SCRIPTS = (
    "build/windows/build_windows.ps1",
    "build/windows/clean_build.ps1",
    "build/windows/package_installer.ps1",
    "build/windows/package_source.ps1",
    "build/windows/prepare_release_staging.ps1",
    "build/windows/run_release_checks.ps1",
    "build/windows/test_environment.ps1",
    "build/windows/test_installer.ps1",
    "build/windows/test_packaged_runtime.ps1",
    "build/windows/verify_clean_vm_gate.ps1",
    "build/windows/verify_legal_review_gate.ps1",
    "build/windows/verify_obs_virtualcam_gate.ps1",
)


def powershell_executable():
    return shutil.which("pwsh") or shutil.which("powershell")


@pytest.mark.parametrize("script_path", WINDOWS_RELEASE_SCRIPTS)
def test_windows_release_powershell_scripts_parse(script_path):
    powershell = powershell_executable()
    if not powershell:
        pytest.skip("PowerShell is not available")

    resolved_script = str(Path(script_path).resolve()).replace("'", "''")
    parser_command = (
        f"$scriptPath = '{resolved_script}'; "
        "$errors = $null; "
        "$tokens = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        "$scriptPath, [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    completed = subprocess.run(
        [powershell, "-NoProfile", "-Command", parser_command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
