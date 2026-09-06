import io
import sys
import threading

import numpy as np
import pytest

import modules.globals
from modules.processors.frame import core


class FakeProgress:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.updates = []
        self.postfix = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def set_postfix(self, postfix):
        self.postfix = postfix

    def update(self, amount):
        self.updates.append(amount)


class FakeInput:
    def __init__(self, *, broken=False):
        self.broken = broken
        self.writes = []
        self.closed = False

    def write(self, payload):
        if self.broken:
            raise BrokenPipeError
        self.writes.append(payload)

    def close(self):
        self.closed = True


class FakeProcess:
    def __init__(self, *, stdout=None, stdin=None, stderr=b"", returncode=0):
        self.stdout = stdout
        self.stdin = stdin
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.killed = False
        self.waited = False

    def wait(self, timeout=None):
        self.waited = True
        return self.returncode

    def poll(self):
        return self.returncode if self.waited else None

    def kill(self):
        self.killed = True


def configure_pipeline_globals(monkeypatch):
    monkeypatch.setattr(modules.globals, "many_faces", True)
    monkeypatch.setattr(modules.globals, "execution_providers", ["CUDAExecutionProvider"])
    monkeypatch.setattr(modules.globals, "execution_threads", 2)
    monkeypatch.setattr(modules.globals, "benchmark_pipeline", False)
    monkeypatch.setattr(modules.globals, "visual_qa_output_dir", None, raising=False)


def test_pipe_pipeline_preserves_frame_order_and_progress(monkeypatch):
    configure_pipeline_globals(monkeypatch)
    first = np.full((1, 2, 3), 10, dtype=np.uint8)
    second = np.full((1, 2, 3), 20, dtype=np.uint8)
    reader = FakeProcess(stdout=io.BytesIO(first.tobytes() + second.tobytes()))
    writer_input = FakeInput()
    writer = FakeProcess(stdin=writer_input)
    processes = iter((reader, writer))
    commands = []
    progress = FakeProgress()

    def fake_popen(command, **_kwargs):
        commands.append(command)
        return next(processes)

    processed_values = []

    def fake_process(_processor, _source, frame, target_face):
        assert target_face is None
        processed_values.append(int(frame[0, 0, 0]))
        return frame + 1

    monkeypatch.setattr(core.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(core, "process_frame_with_target", fake_process)
    monkeypatch.setattr(core, "tqdm", lambda **_kwargs: progress)
    monkeypatch.setattr(core.os.path, "isfile", lambda _path: True)
    processor = type("Processor", (), {"NAME": "test-processor"})()

    success = core._run_pipe_pipeline(
        "input.mp4",
        "output.mp4",
        30.0,
        object(),
        [processor],
        2,
        1,
        first.nbytes,
        2,
        "libx264",
        ["-preset", "medium"],
    )

    assert success
    assert processed_values == [10, 20]
    assert [np.frombuffer(payload, dtype=np.uint8)[0] for payload in writer_input.writes] == [11, 21]
    assert progress.updates == [1, 1]
    assert progress.postfix["execution_providers"] == ["CUDAExecutionProvider"]
    assert commands[0][-1] == "-"
    assert commands[1][-1] == "output.mp4"
    assert reader.waited and writer.waited
    assert not reader.killed and not writer.killed
    assert reader.stdout.closed and writer.stdin.closed
    assert reader._ffmpeg_stderr.closed and writer._ffmpeg_stderr.closed


def test_pipe_pipeline_broken_writer_cleans_up_processes(monkeypatch):
    configure_pipeline_globals(monkeypatch)
    frame = np.zeros((1, 1, 3), dtype=np.uint8)
    reader = FakeProcess(stdout=io.BytesIO(frame.tobytes()))
    writer = FakeProcess(stdin=FakeInput(broken=True))
    processes = iter((reader, writer))
    monkeypatch.setattr(core.subprocess, "Popen", lambda *_args, **_kwargs: next(processes))
    monkeypatch.setattr(core, "process_frame_with_target", lambda _fp, _source, value, _target: value)
    monkeypatch.setattr(core, "tqdm", lambda **_kwargs: FakeProgress())
    processor = type("Processor", (), {"NAME": "test-processor"})()

    success = core._run_pipe_pipeline(
        "input.mp4", "output.mp4", 30.0, object(), [processor],
        1, 1, frame.nbytes, 1, "libx264", [],
    )

    assert not success
    assert reader.killed and writer.killed
    assert reader.waited and writer.waited
    assert reader.stdout.closed and writer.stdin.closed
    assert reader._ffmpeg_stderr.closed and writer._ffmpeg_stderr.closed


def test_start_ffmpeg_pipes_cleans_reader_when_writer_start_fails(monkeypatch):
    reader = FakeProcess(stdout=io.BytesIO())
    calls = 0
    capture_files = []
    real_temporary_file = core.tempfile.TemporaryFile

    def track_capture():
        capture = real_temporary_file()
        capture_files.append(capture)
        return capture

    def fake_popen(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return reader
        raise OSError("writer unavailable")

    monkeypatch.setattr(core.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(core.tempfile, "TemporaryFile", track_capture)

    started_reader, started_writer = core._start_ffmpeg_pipes(["reader"], ["writer"])

    assert started_reader is None
    assert started_writer is None
    assert reader.killed
    assert reader.waited
    assert reader.stdout.closed and reader.stderr.closed
    assert reader._ffmpeg_stderr.closed
    assert len(capture_files) == 2
    assert all(capture.closed for capture in capture_files)


def test_video_metrics_records_selected_provider_configuration(monkeypatch):
    monkeypatch.setattr(modules.globals, "benchmark_pipeline", True)
    monkeypatch.setattr(modules.globals, "benchmark_output_path", None)
    monkeypatch.setattr(modules.globals, "quality_mode", "balanced", raising=False)
    monkeypatch.setattr(
        modules.globals,
        "execution_providers",
        ["DmlExecutionProvider", "CPUExecutionProvider"],
    )
    monkeypatch.setattr(core, "provider_config_summary", lambda providers: {"selected": providers[0]})
    processor = type("Processor", (), {"NAME": "DLC.FACE-SWAPPER"})()

    metrics, writer, context = core._video_metrics(
        "input.mp4", "libx264", 24.0, 1920, 1080, [processor]
    )

    assert metrics.name == "video"
    assert writer is None
    assert context["execution_providers"] == [
        "DmlExecutionProvider",
        "CPUExecutionProvider",
    ]
    assert context["execution_provider_config"] == {"selected": "DmlExecutionProvider"}


def run_small_pipeline(monkeypatch, reader, writer):
    configure_pipeline_globals(monkeypatch)
    processes = iter((reader, writer))
    monkeypatch.setattr(core.subprocess, "Popen", lambda *_args, **_kwargs: next(processes))
    monkeypatch.setattr(core, "tqdm", lambda **_kwargs: FakeProgress())
    monkeypatch.setattr(core.os.path, "isfile", lambda _path: True)
    return core._run_pipe_pipeline(
        "input.mp4", "output.mp4", 30.0, None, [],
        1, 1, 3, 1, "libx264", [],
    )


def test_pipe_pipeline_rejects_decoder_failure_after_valid_frame(monkeypatch):
    reader = FakeProcess(stdout=io.BytesIO(b"\x01\x02\x03"), returncode=1)
    writer = FakeProcess(stdin=FakeInput())

    assert not run_small_pipeline(monkeypatch, reader, writer)
    assert reader.waited and writer.waited


def test_pipe_pipeline_rejects_encoder_failure_after_valid_frame(monkeypatch):
    reader = FakeProcess(stdout=io.BytesIO(b"\x01\x02\x03"))
    writer = FakeProcess(stdin=FakeInput(), returncode=1)

    assert not run_small_pipeline(monkeypatch, reader, writer)
    assert reader.waited and writer.waited
    assert reader.stdout.closed and writer.stdin.closed


def test_start_ffmpeg_pipes_cleans_reader_when_second_capture_fails(monkeypatch):
    reader = FakeProcess(stdout=io.BytesIO())
    real_temporary_file = core.tempfile.TemporaryFile
    capture = real_temporary_file()
    calls = 0

    def failed_capture():
        nonlocal calls
        calls += 1
        if calls == 1:
            return capture
        raise OSError("Temporary storage unavailable")

    monkeypatch.setattr(core.tempfile, "TemporaryFile", failed_capture)
    monkeypatch.setattr(core.subprocess, "Popen", lambda *_args, **_kwargs: reader)

    assert core._start_ffmpeg_pipes(["reader"], ["writer"]) == (None, None)
    assert reader.killed and reader.waited
    assert reader.stdout.closed
    assert capture.closed


def test_pipe_pipeline_rejects_truncated_final_frame(monkeypatch):
    reader = FakeProcess(stdout=io.BytesIO(b"\x01\x02\x03\x04"))
    writer = FakeProcess(stdin=FakeInput())

    assert not run_small_pipeline(monkeypatch, reader, writer)
    assert reader.waited and writer.waited
    assert reader.stdout.closed and writer.stdin.closed


@pytest.mark.parametrize("decoder_exit", [0, 7])
def test_real_subprocess_stderr_does_not_block_pipeline(
    monkeypatch, tmp_path, capsys, decoder_exit,
):
    configure_pipeline_globals(monkeypatch)
    output = tmp_path / "encoded.bin"
    reader_script = (
        "import sys; "
        "sys.stderr.buffer.write(b'r' * (2 * 1024 * 1024)); "
        "sys.stderr.buffer.write(b'\\nDecoder diagnostic tail\\n'); "
        "sys.stderr.flush(); "
        "sys.stdout.buffer.write(bytes([1, 2, 3])); "
        "sys.stdout.flush(); "
        f"sys.exit({decoder_exit})"
    )
    writer_script = (
        "import sys; from pathlib import Path; "
        "sys.stderr.buffer.write(b'w' * (2 * 1024 * 1024)); "
        "sys.stderr.flush(); "
        "Path(sys.argv[1]).write_bytes(sys.stdin.buffer.read())"
    )
    monkeypatch.setattr(
        core, "_ffmpeg_pipe_commands",
        lambda *_args: (
            [sys.executable, "-c", reader_script],
            [sys.executable, "-c", writer_script, str(output)],
        ),
    )
    monkeypatch.setattr(core, "tqdm", lambda **_kwargs: FakeProgress())
    started_processes = []
    real_popen = core.subprocess.Popen

    def track_process(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        started_processes.append(process)
        return process

    monkeypatch.setattr(core.subprocess, "Popen", track_process)
    timed_out = threading.Event()

    def abort_hung_pipeline():
        timed_out.set()
        for process in started_processes:
            if process.poll() is None:
                process.kill()

    watchdog = threading.Timer(15, abort_hung_pipeline)
    watchdog.daemon = True
    watchdog.start()
    try:
        success = core._run_pipe_pipeline(
            "unused.mp4", str(output), 30.0, None, [],
            1, 1, 3, 1, "libx264", [],
        )
    finally:
        watchdog.cancel()
        watchdog.join(timeout=1)
        core._kill_pipe_processes(*started_processes)

    assert not timed_out.is_set(), "FFmpeg diagnostic output blocked frame I/O"
    assert success is (decoder_exit == 0)
    assert output.read_bytes() == bytes([1, 2, 3])
    assert len(started_processes) == 2
    assert all(process.poll() is not None for process in started_processes)
    assert all(process._ffmpeg_stderr.closed for process in started_processes)
    assert started_processes[0].stdout.closed
    assert started_processes[1].stdin.closed
    logs = capsys.readouterr().out
    if decoder_exit:
        assert "Decoder diagnostic tail" in logs
        assert "decoder exited with status 7" in logs
    assert len(logs) < 66 * 1024


def test_read_pipe_frame_accumulates_short_reads():
    class ChunkedStream(io.BytesIO):
        def read(self, size=-1):
            return super().read(min(size, 2))

    reader = FakeProcess(stdout=ChunkedStream(bytes(range(6))))
    frame = core._read_pipe_frame(reader, 6, 2, 1, None)

    assert frame is not None
    assert frame.tobytes() == bytes(range(6))
    assert core._read_pipe_frame(reader, 6, 2, 1, None) is None


@pytest.mark.parametrize("setup_function", ["_video_metrics", "_visual_qa_sessions"])
def test_pipe_pipeline_setup_failure_reaps_processes(monkeypatch, setup_function):
    reader = FakeProcess(stdout=io.BytesIO(b"\x01\x02\x03"))
    writer = FakeProcess(stdin=FakeInput())

    def failed_setup(*_args, **_kwargs):
        raise OSError("QA destination is unavailable")

    monkeypatch.setattr(core, setup_function, failed_setup)

    assert not run_small_pipeline(monkeypatch, reader, writer)
    assert reader.killed and writer.killed
    assert reader.waited and writer.waited
    assert reader.stdout.closed and writer.stdin.closed
