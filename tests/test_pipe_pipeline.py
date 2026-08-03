import io

import numpy as np

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

    def wait(self):
        self.waited = True
        return self.returncode

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
    assert reader.killed and writer.killed


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


def test_start_ffmpeg_pipes_cleans_reader_when_writer_start_fails(monkeypatch):
    reader = FakeProcess(stdout=io.BytesIO())
    calls = 0

    def fake_popen(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return reader
        raise OSError("writer unavailable")

    monkeypatch.setattr(core.subprocess, "Popen", fake_popen)

    started_reader, started_writer = core._start_ffmpeg_pipes(["reader"], ["writer"])

    assert started_reader is None
    assert started_writer is None
    assert reader.killed


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
