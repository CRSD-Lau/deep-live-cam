import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCKS = ROOT / "requirements-locks"


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8").lower()


def requirement_names(lock_text: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(r"(?m)^([a-z0-9_.-]+)==[^\s\\]+(?:\s*;[^\n\\]+)?\s*\\", lock_text)
    }


def test_release_locks_are_hashed_and_keep_onnx_runtimes_isolated():
    cuda = read("requirements-locks/windows-cuda-py311.lock")
    directml = read("requirements-locks/windows-directml-py311.lock")
    cuda_runtime = read("requirements-locks/windows-cuda-runtime-py311.lock")
    cuda_runtime_audit = read(
        "requirements-locks/windows-cuda-runtime-audit-py311.txt"
    )

    assert "onnxruntime-gpu==1.24.4" in cuda
    assert "onnxruntime-directml" not in cuda
    assert "torch==" not in cuda
    assert "setuptools==83.0.0" in cuda
    assert "onnxruntime-directml==1.23.0" in directml
    assert "onnxruntime-gpu" not in directml
    assert "setuptools==83.0.0" in directml
    assert "torch==2.11.0+cu128" in cuda_runtime
    assert "--hash=sha256:" in cuda_runtime
    assert cuda_runtime_audit.strip() == "torch==2.11.0"

    for lock_text in (cuda, directml):
        names = requirement_names(lock_text)
        assert names
        assert lock_text.count("--hash=sha256:") >= len(names)


def test_release_builds_install_only_hash_locked_profiles():
    build = read("build/windows/build_windows.ps1")
    directml_setup = read("tools/setup_directml.ps1")

    assert "requirements-locks\\windows-cuda-py311.lock" in build
    assert "requirements-locks\\windows-directml-py311.lock" in build
    assert "requirements-locks\\windows-cuda-runtime-py311.lock" in build
    assert build.count("--require-hashes") == 2
    assert "pyinstaller>=" not in build
    assert "pip\", \"install\", \"--upgrade\"" not in build
    assert "--require-hashes" in directml_setup
    assert "requirements-locks\\windows-directml-py311.lock" in directml_setup
    assert "python_dependencies_directml.md" in build


def test_dependency_sources_match_reviewed_release_versions():
    cuda = read("requirements.txt")
    directml = read("requirements-directml.txt")
    build = read("requirements-build-windows.txt")
    dev = read("requirements-dev.txt")

    assert "onnxruntime-gpu==1.24.4" in cuda
    assert "opennsfw2==0.18.0" in cuda
    assert "opennsfw2==0.18.0" in directml
    assert "pyside6>=6.11.1,<7" in cuda
    assert "pyside6>=6.11.1,<7" in directml
    assert "typing-extensions>=4.16.0" in cuda
    assert "typing-extensions>=4.16.0" in directml
    assert "tqdm>=4.70.0" in cuda
    assert "tqdm>=4.70.0" in directml
    assert "pyinstaller==6.22.2" in build
    assert "pyinstaller-hooks-contrib==2026.7" in build
    assert "pytest==9.1.1" in dev


def test_workflows_pin_python_and_validate_maintained_locks():
    ci = read(".github/workflows/ci.yml")
    release = read(".github/workflows/windows-release.yml")
    directml = read(".github/workflows/windows-directml-test.yml")
    dependabot = read(".github/dependabot.yml")

    for workflow in (ci, release, directml):
        assert 'python-version: "3.11.9"' in workflow
    assert "tools\\update_dependency_locks.ps1 -check" in ci
    assert "requirements-locks/windows-cuda-py311.lock" in ci
    assert "requirements-locks/windows-directml-py311.lock" in ci
    assert "--ignore-vuln pysec-2025-194" in ci
    assert "version-update:semver-major" in dependabot
    assert "windows-build-toolchain:" in dependabot
    assert "allow:" in dependabot
    for managed_dependency in (
        "pip-tools",
        "setuptools",
        "wheel",
        "pyinstaller",
        "pyinstaller-hooks-contrib",
        "bandit",
        "pip-audit",
        "pytest",
        "ruff",
    ):
        assert f"dependency-name: {managed_dependency}" in dependabot
    assert "dependency-name: pip" in dependabot
    assert '"26.2"' in dependabot
