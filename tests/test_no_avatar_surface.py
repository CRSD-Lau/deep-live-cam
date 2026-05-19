import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_run_help_does_not_advertise_avatar_or_llm_modes():
    result = subprocess.run(
        [sys.executable, "run.py", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    help_text = result.stdout.lower()
    assert "avatar" not in help_text
    assert "vtuber" not in help_text
    assert "open-llm" not in help_text


def test_avatar_runtime_files_are_not_shipped():
    removed_paths = [
        ROOT / "docs" / "AVATAR_TRACKING.md",
        ROOT / "docs" / "OPEN_LLM_VTUBER.md",
        ROOT / "runtime" / "vtuber_bridge.py",
        ROOT / "tools" / "avatar_overlay",
        ROOT / "tools" / "avatar_overlay_server.py",
    ]

    assert [path for path in removed_paths if path.exists()] == []


def test_readme_no_longer_documents_avatar_mode():
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()

    assert "avatar camera" not in readme
    assert "open-llm" not in readme
    assert "vtuber" not in readme
