"""Exercise the production CUDA helper-install block with an offline tiny wheel."""

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(
    os.name != "nt" or not POWERSHELL,
    reason="The release helper requires Windows PowerShell and CPython 3.11.9",
)
PROBE_NAME = "dlc_cuda_helper_probe"


def clean_environment():
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "PIP_TARGET", "PIP_PREFIX", "PIP_USER"):
        environment.pop(name, None)
    environment.update({
        "PIP_CONFIG_FILE": os.devnull,
        "PIP_NO_INDEX": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    })
    return environment


def python_result(python, code):
    result = subprocess.run(
        [str(python), "-I", "-c", code], check=True, capture_output=True,
        text=True, env=clean_environment(), timeout=30,
    )
    return json.loads(result.stdout)


def distribution_snapshot(python):
    return python_result(
        python,
        "import importlib.metadata as m, json; "
        "print(json.dumps(sorted((d.metadata['Name'], d.version) for d in m.distributions())))",
    )


def tiny_wheel(directory):
    dist_info = PROBE_NAME + "-0.0.1.dist-info"
    entries = {
        PROBE_NAME + "/__init__.py": b"VALUE = 'installed in the helper only'\n",
        dist_info + "/METADATA": (
            f"Metadata-Version: 2.1\nName: {PROBE_NAME}\nVersion: 0.0.1\n"
            "Requires-Dist: deliberately-unavailable-dlc-probe-dependency==0.0.1\n\n"
        ).encode(),
        dist_info + "/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    records = []
    for name, payload in entries.items():
        sha = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
        records.append(f"{name},sha256={sha},{len(payload)}")
    records.append(dist_info + "/RECORD,,")
    entries[dist_info + "/RECORD"] = ("\n".join(records) + "\n").encode()
    wheel_path = directory / (PROBE_NAME + "-0.0.1-py3-none-any.whl")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload in entries.items():
            archive.writestr(name, payload)
    wheel_path.write_bytes(buffer.getvalue())
    return wheel_path


def run_helper_block(main_python, target, requirements, report):
    """Execute the actual install statements without building or downloading Torch."""
    script = r"""
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $env:DLC_TEST_BUILD_SCRIPT, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Build script did not parse.' }
$checked = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Invoke-Checked'
}, $true)
$blocks = @($ast.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.IfStatementAst] -and
    $node.Clauses[0].Item1.Extent.Text -eq '-not $IsDirectML' -and
    $node.Extent.Text.Contains('$CudaRuntimePythonVersion')
}, $true))
if ($null -eq $checked -or $blocks.Count -ne 1) {
    throw 'Cannot isolate the production CUDA helper installation block.'
}
. ([scriptblock]::Create($checked.Extent.Text))
$Python = $env:DLC_TEST_MAIN_PYTHON
$PythonExe = $Python
$CudaRuntimeVenv = $env:DLC_TEST_TARGET
$CudaRuntimePython = Join-Path $CudaRuntimeVenv 'Scripts\python.exe'
$CudaRuntimeRequirementsFile = $env:DLC_TEST_REQUIREMENTS
$IsDirectML = $false
. ([scriptblock]::Create($blocks[0].Extent.Text))
"""
    environment = clean_environment()
    environment.update({
        "DLC_TEST_BUILD_SCRIPT": str(ROOT / "build/windows/build_windows.ps1"),
        "DLC_TEST_MAIN_PYTHON": str(main_python),
        "DLC_TEST_TARGET": str(target),
        "DLC_TEST_REQUIREMENTS": str(requirements),
        "PIP_REPORT": str(report),
    })
    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-Command", script],
        capture_output=True, text=True, env=environment, timeout=90,
    )


@pytest.mark.parametrize("existing_helper", [False, True], ids=["fresh", "existing"])
def test_cuda_helper_uses_main_pip_and_preserves_environments(tmp_path, existing_helper):
    main_python = Path(os.environ.get("DLC_BUILD_TEST_PYTHON", sys.executable))
    target = tmp_path / "CUDA helper with spaces"
    target_python = target / "Scripts/python.exe"
    main_before = distribution_snapshot(main_python)
    main_pip = python_result(main_python, "import pip, json; print(json.dumps(pip.__version__))")
    if existing_helper:
        subprocess.run(
            [str(main_python), "-I", "-m", "venv", str(target)],
            check=True, capture_output=True, env=clean_environment(), timeout=60,
        )
        target_before = distribution_snapshot(target_python)
    else:
        target_before = []
    wheel = tiny_wheel(tmp_path)
    requirements = tmp_path / "runtime.lock"
    requirements.write_text(
        f"{wheel.as_uri()} --hash=sha256:{hashlib.sha256(wheel.read_bytes()).hexdigest()}\n",
        encoding="utf-8",
    )
    report = tmp_path / "install-report.json"

    result = run_helper_block(main_python, target, requirements, report)

    assert result.returncode == 0, result.stdout + result.stderr
    installed_report = json.loads(report.read_text(encoding="utf-8"))
    assert installed_report["pip_version"] == main_pip
    assert python_result(
        target_python,
        f"import {PROBE_NAME}, json; print(json.dumps({PROBE_NAME}.VALUE))",
    ) == "installed in the helper only"
    assert distribution_snapshot(target_python) == sorted(target_before + [[PROBE_NAME, "0.0.1"]])
    assert distribution_snapshot(main_python) == main_before
    if not existing_helper:
        assert python_result(
            target_python,
            "import importlib.util as u, json; "
            "print(json.dumps([u.find_spec('pip') is None, u.find_spec('setuptools') is None]))",
        ) == [True, True]


def test_cuda_helper_rejects_an_offline_wheel_with_wrong_hash(tmp_path):
    main_python = Path(os.environ.get("DLC_BUILD_TEST_PYTHON", sys.executable))
    main_before = distribution_snapshot(main_python)
    target = tmp_path / "CUDA helper rejected hash"
    wheel = tiny_wheel(tmp_path)
    requirements = tmp_path / "wrong-hash.lock"
    requirements.write_text(f"{wheel.as_uri()} --hash=sha256:{'0' * 64}\n", encoding="utf-8")

    result = run_helper_block(main_python, target, requirements, tmp_path / "failed-report.json")

    assert result.returncode != 0
    assert "DO NOT MATCH THE HASHES" in result.stdout + result.stderr
    assert distribution_snapshot(target / "Scripts/python.exe") == []
    assert distribution_snapshot(main_python) == main_before
