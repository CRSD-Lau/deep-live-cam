import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stale_asset_dirs_are_not_tracked():
    assert not (ROOT / "media").exists()
    assert not (ROOT / "locales").exists()
    assert not (ROOT / "models" / "instructions.txt").exists()


def test_local_agent_scaffolding_is_not_tracked():
    assert not (ROOT / ".agents").exists()
    assert not (ROOT / ".specify").exists()
    assert not (ROOT / "AGENTS.md").exists()


def test_obsolete_entrypoints_are_not_tracked():
    for relative_path in (
        "benchmark_pipeline.py",
        "modules/run.py",
        "modules/tkinter_fix.py",
        "run-cuda.bat",
        "tkinter_fix.py",
    ):
        assert not (ROOT / relative_path).exists()


def test_directml_build_has_no_stale_issue_branch_trigger():
    workflow = (ROOT / ".github" / "workflows" / "windows-directml-test.yml").read_text(
        encoding="utf-8"
    )

    assert "codex/amd-directml-test" not in workflow
    assert "workflow_dispatch:" in workflow


def test_windows_packaging_does_not_bundle_removed_asset_dirs():
    spec = (ROOT / "build" / "windows" / "deep_live_cam_studio.spec").read_text(
        encoding="utf-8"
    )

    assert '("media", "media")' not in spec
    assert '("locales", "locales")' not in spec


def test_cli_no_longer_exposes_hidden_language_option():
    result = subprocess.run(
        [sys.executable, "run.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "--lang" not in result.stdout
