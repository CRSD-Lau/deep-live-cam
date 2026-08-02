import shutil
import subprocess
from pathlib import Path

import pytest

from tools.collect_third_party_license_files import high_attention_packages


WINDOWS_RELEASE_SCRIPTS = (
    "build/windows/build_windows.ps1",
    "build/windows/assemble_release_assets.ps1",
    "build/windows/clean_build.ps1",
    "build/windows/package_installer.ps1",
    "build/windows/package_portable.ps1",
    "build/windows/package_source.ps1",
    "build/windows/prepare_release_staging.ps1",
    "build/windows/run_release_checks.ps1",
    "build/windows/test_environment.ps1",
    "build/windows/test_installer.ps1",
    "build/windows/test_packaged_runtime.ps1",
    "build/windows/verify_clean_vm_gate.ps1",
    "build/windows/verify_legal_review_gate.ps1",
    "build/windows/verify_obs_virtualcam_gate.ps1",
    "tools/setup_directml.ps1",
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


def test_packaged_runtime_clears_handled_model_consent_exit_code():
    script = Path("build/windows/test_packaged_runtime.ps1").read_text(encoding="utf-8")

    assert "$global:LASTEXITCODE = 0" in script


def test_cuda_build_uses_pinned_runtime_wheel_and_requires_every_dll():
    requirements = Path("requirements-build-windows-cuda.txt").read_text(encoding="utf-8")
    build_script = Path("build/windows/build_windows.ps1").read_text(encoding="utf-8")
    spec = Path("build/windows/deep_live_cam_studio.spec").read_text(encoding="utf-8")
    runtime_test = Path("build/windows/test_packaged_runtime.ps1").read_text(encoding="utf-8")

    assert "torch==2.11.0+cu128" in requirements
    assert "https://download.pytorch.org/whl/cu128" in requirements
    assert '"--no-cache-dir", "--no-deps"' in build_script
    assert '"-r", $CudaRuntimeRequirementsFile' in build_script
    assert "CUDA release build is missing required PyTorch runtime DLLs" in spec
    for name in ("cublasLt64_12.dll", "cudnn64_9.dll", "cusparse64_12.dll"):
        assert name in spec
        assert name in runtime_test


def test_cuda_license_collection_includes_pytorch_but_directml_does_not():
    assert "torch" in high_attention_packages("onnxruntime-gpu")
    assert "torch" not in high_attention_packages("onnxruntime-directml")


def test_processing_evidence_describes_the_self_contained_cuda_release():
    evidence = Path("PROCESSING_VERIFICATION.md").read_text(encoding="utf-8")

    assert "does not currently bundle NVIDIA CUDA" not in evidence
    assert "without an external CUDA Toolkit" in evidence
    assert "--check-execution-provider" in evidence


def test_windows_build_uses_release_venv_unless_existing_environment_is_explicit():
    script = Path("build/windows/build_windows.ps1").read_text(encoding="utf-8")

    assert '$Venv = if ($UseExistingVenv) { $ExistingVenv } else { $BuildVenv }' in script
    assert "-UseExistingVenv was requested" in script


def test_clean_build_covers_both_accelerator_outputs():
    script = Path("build/windows/clean_build.ps1").read_text(encoding="utf-8")

    for expected_path in (
        "pyinstaller-work-directml",
        "build\\windows\\portable",
        "dist\\DeepLiveCamStudio-DirectML",
    ):
        assert expected_path in script


def test_source_packaging_peels_annotated_tags_to_commits():
    script = Path("build/windows/package_source.ps1").read_text(encoding="utf-8")

    assert '$CommitRef = "$GitRef^{commit}"' in script
    assert "git rev-parse --verify $CommitRef" in script
    assert "$LASTEXITCODE -ne 0" in script
