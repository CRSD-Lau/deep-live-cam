"""Exercise actual FFmpeg media I/O with generated, non-personal media."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest

import modules.globals
from modules import utilities
from modules.processors.frame import core


pytestmark = pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="FFmpeg and ffprobe are required for the media integration test",
)


def run_media_command(command):
    return subprocess.run(command, check=True, capture_output=True, timeout=30)


@pytest.mark.parametrize("with_audio", [True, False])
def test_pipe_export_and_audio_finalization(monkeypatch, tmp_path, with_audio):
    target = tmp_path / "input.mp4"
    output = tmp_path / "export.mp4"
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
        "-i", "testsrc2=size=96x64:rate=12:duration=1",
    ]
    if with_audio:
        command += ["-f", "lavfi", "-i", "sine=frequency=440:duration=1"]
    command += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-y", str(target)]
    run_media_command(command)
    output.write_bytes(b"old export")

    monkeypatch.setattr(modules.globals, "many_faces", True)
    monkeypatch.setattr(modules.globals, "execution_providers", ["CPUExecutionProvider"])
    monkeypatch.setattr(modules.globals, "execution_threads", 1)
    monkeypatch.setattr(modules.globals, "benchmark_pipeline", False)
    monkeypatch.setattr(modules.globals, "visual_qa_output_dir", None)
    monkeypatch.setattr(modules.globals, "keep_frames", False)
    utilities.create_temp(str(target))
    workspace = Path(utilities.get_temp_directory_path(str(target)))
    temporary_output = utilities.get_temp_output_path(str(target))
    try:
        assert core._run_pipe_pipeline(
            str(target), temporary_output, 12.0, None, [],
            96, 64, 96 * 64 * 3, 12, "libx264", ["-preset", "ultrafast"],
        )
        assert utilities.restore_audio(str(target), str(output))
        metadata = json.loads(run_media_command([
            "ffprobe", "-v", "error", "-count_frames", "-show_streams",
            "-show_format", "-of", "json", str(output),
        ]).stdout)
        video = next(stream for stream in metadata["streams"] if stream["codec_type"] == "video")
        assert (video["width"], video["height"]) == (96, 64)
        assert int(video["nb_read_frames"]) == 12
        assert float(video["duration"]) == pytest.approx(1.0, abs=0.1)
        assert any(stream["codec_type"] == "audio" for stream in metadata["streams"]) is with_audio
        # Decode the finalized file fully, beyond merely reading its container header.
        run_media_command(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"])
    finally:
        utilities.clean_temp(str(target))
    assert not workspace.exists()
