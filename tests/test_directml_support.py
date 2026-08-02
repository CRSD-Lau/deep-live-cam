from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_directml_requirements_use_the_vendor_neutral_runtime_only():
    requirements = read("requirements-directml.txt").lower()

    assert "onnxruntime-directml==1.23.0" in requirements
    assert "onnxruntime-gpu" not in requirements
    assert "onnx==1.22.0" in requirements
    assert "pillow==12.3.0" in requirements
    assert "insightface==0.7.3" in requirements


def test_directml_launcher_refuses_silent_cpu_fallback():
    launcher = read("run-directml.bat").lower()

    assert ".venv-directml\\scripts\\python.exe" in launcher
    assert "--execution-provider directml --strict" in launcher
    assert "if errorlevel 1" in launcher


def test_windows_build_has_an_isolated_directml_profile():
    build_script = read("build/windows/build_windows.ps1")
    spec = read("build/windows/deep_live_cam_studio.spec")

    assert 'ValidateSet("Cuda", "DirectML")' in build_script
    assert '"requirements-directml.txt"' in build_script
    assert '".venv-build-windows-directml"' in build_script
    assert '"DeepLiveCamStudio-DirectML"' in build_script
    assert 'ACCELERATOR != "cuda"' in spec
    assert 'BUNDLE_NAME = os.environ.get("DLC_BUNDLE_NAME"' in spec


def test_directml_branch_workflow_publishes_a_portable_artifact():
    workflow = read(".github/workflows/windows-directml-test.yml")
    packaged_runtime_test = read("build/windows/test_packaged_runtime.ps1")

    assert "-Accelerator DirectML" in workflow
    assert "dist/DeepLiveCamStudio-DirectML/**" in workflow
    assert "include-hidden-files: true" in workflow
    assert "retention-days: 14" in workflow
    assert r"_internal\sklearn\.libs\vcomp140.dll" in packaged_runtime_test


def test_release_workflow_publishes_a_verified_directml_zip():
    workflow = read(".github/workflows/windows-release.yml")
    portable_script = read("build/windows/package_portable.ps1")

    assert "build-directml:" in workflow
    assert "package_portable.ps1" in workflow
    assert "DeepLiveCamStudio-${{ inputs.app_version }}-DirectML-x64-portable.zip" in workflow
    assert "include-hidden-files: true" in workflow
    assert '"_internal/sklearn/.libs/vcomp140.dll"' in portable_script
    assert "ForbiddenModelEntries" in portable_script
    assert "-RequireAccelerator" in portable_script
