import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


WORKFLOW = Path(".github/workflows/windows-release.yml")
RESOLVED_REF = "${{ needs.resolve-source.outputs.sha }}"


def release_workflow():
    return yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def resolver_script():
    return next(
        step["run"]
        for step in release_workflow()["jobs"]["resolve-source"]["steps"]
        if step.get("id") == "source"
    )


def test_both_release_profiles_and_source_archive_share_one_resolved_commit():
    workflow = release_workflow()
    resolver = workflow["jobs"]["resolve-source"]
    assert resolver["outputs"]["sha"] == "${{ steps.source.outputs.sha }}"
    source_checkout = next(step for step in resolver["steps"] if "actions/checkout@" in step.get("uses", ""))
    assert source_checkout["with"]["ref"] == "${{ inputs.git_ref || github.sha }}"

    for job_name in ("build-windows", "build-directml"):
        job = workflow["jobs"][job_name]
        assert "resolve-source" in job["needs"]
        checkouts = [step for step in job["steps"] if "actions/checkout@" in step.get("uses", "")]
        assert len(checkouts) == 1
        assert checkouts[0]["with"]["ref"] == RESOLVED_REF

    cuda_job = workflow["jobs"]["build-windows"]
    assert cuda_job["env"]["SOURCE_COMMIT"] == RESOLVED_REF
    packaging = next(step["run"] for step in cuda_job["steps"] if "run_release_checks.ps1" in step.get("run", ""))
    assert "-GitRef $env:SOURCE_COMMIT" in packaging


def test_workflow_inputs_are_data_and_hosted_publish_guard_is_preserved():
    workflow = release_workflow()
    assert workflow["on"]["workflow_dispatch"]["inputs"]["app_version"]["default"] == "2.2.4"
    assert workflow["env"]["APP_VERSION"] == "${{ inputs.app_version }}"
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            assert "${{" not in step.get("run", ""), "workflow inputs must never be interpolated into executable scripts"
    guard = next(
        step["run"]
        for step in workflow["jobs"]["build-windows"]["steps"]
        if step["name"] == "Guard against accidental publish approval"
    )
    assert '"--require-publish-ready"' in guard
    assert "$strict.ExitCode -eq 0" in guard
    assert "Hosted CI unexpectedly marked this build publish-ready" in guard


@pytest.fixture
def release_source(tmp_path):
    if not shutil.which("git"):
        pytest.skip("Git is unavailable")
    (tmp_path / "modules").mkdir()
    (tmp_path / "modules" / "metadata.py").write_text(
        "version = '2.2.4'\nraise RuntimeError('metadata must be parsed, not executed')\n",
        encoding="utf-8",
    )
    for args in (
        ["init", "-q"],
        ["add", "modules/metadata.py"],
        ["-c", "user.name=Neil Mitchell", "-c", "user.email=fixture@example.test", "commit", "-qm", "release fixture"],
    ):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def run_resolver(source, version):
    output = source / "job-output.txt"
    completed = subprocess.run(
        [sys.executable, "-c", resolver_script()],
        cwd=source,
        env={**os.environ, "APP_VERSION": version, "GITHUB_OUTPUT": str(output)},
        text=True,
        capture_output=True,
    )
    return completed, output


def test_resolver_outputs_actual_checkout_sha_only_after_version_matches(release_source):
    expected = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=release_source, text=True
    ).strip()

    completed, output = run_resolver(release_source, "2.2.4")

    assert completed.returncode == 0, completed.stderr
    assert output.read_text(encoding="utf-8") == f"sha={expected}\n"
    assert expected in completed.stdout


@pytest.mark.parametrize("version", ["2.2.3", "", '2.2.4"; Write-Output injected', "2.2.4\nsha=incorrect"])
def test_resolver_rejects_mismatched_or_malformed_version_before_build(release_source, version):
    completed, output = run_resolver(release_source, version)

    assert completed.returncode != 0
    assert not output.exists()
    assert "version" in completed.stderr.lower()


def test_workflow_powershell_steps_parse(tmp_path):
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if not powershell:
        pytest.skip("PowerShell is unavailable")
    scripts = [
        step["run"]
        for job in release_workflow()["jobs"].values()
        for step in job["steps"]
        if "run" in step and step.get("shell") != "python"
    ]
    for index, script in enumerate(scripts):
        (tmp_path / f"step-{index}.ps1").write_text(script, encoding="utf-8")
    command = (
        "$failed = $false; "
        "Get-ChildItem -LiteralPath $env:WORKFLOW_TEST_SCRIPTS -Filter '*.ps1' | ForEach-Object { "
        "$errors = $null; $tokens = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count) { $errors | ForEach-Object { Write-Error $_ }; $failed = $true } }; "
        "if ($failed) { exit 1 }"
    )
    completed = subprocess.run(
        [powershell, "-NoProfile", "-Command", command],
        env={**os.environ, "WORKFLOW_TEST_SCRIPTS": str(tmp_path)},
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
