import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stale_asset_dirs_are_not_tracked():
    assert not (ROOT / "media").exists()
    assert not (ROOT / "locales").exists()
    assert not (ROOT / "models" / "instructions.txt").exists()


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
