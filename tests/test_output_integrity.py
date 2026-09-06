from pathlib import Path
import stat
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

import modules.globals
from modules import core, utilities, face_analyser
from modules.processors.frame import core as frame_core
from modules.processors.frame import (
    face_enhancer, face_enhancer_gpen256, face_enhancer_gpen512, face_swapper,
)


@pytest.fixture(autouse=True)
def private_workspaces(monkeypatch, tmp_path):
    monkeypatch.setattr(utilities, "_TEMP_WORKSPACES", {})
    monkeypatch.setattr(modules.globals, "keep_frames", False)
    original_mkdtemp = utilities.tempfile.mkdtemp
    root = tmp_path / "workspaces"
    root.mkdir()
    monkeypatch.setattr(
        utilities.tempfile, "mkdtemp",
        lambda **kwargs: original_mkdtemp(dir=root, **kwargs),
    )


def configure_render(monkeypatch, target, destination, processors):
    monkeypatch.setattr(modules.globals, "target_path", str(target))
    monkeypatch.setattr(modules.globals, "source_path", "source.png")
    monkeypatch.setattr(modules.globals, "output_path", str(destination))
    monkeypatch.setattr(modules.globals, "headless", True)
    monkeypatch.setattr(modules.globals, "nsfw_filter", False)
    monkeypatch.setattr(modules.globals, "map_faces", False)
    monkeypatch.setattr(modules.globals, "keep_fps", False)
    monkeypatch.setattr(modules.globals, "keep_audio", False)
    monkeypatch.setattr(frame_core, "get_frame_processors_modules", lambda _: processors)
    monkeypatch.setattr(core, "release_resources", lambda: None)


def processor(process_image=lambda *_: True, process_video=lambda *_: None):
    return SimpleNamespace(
        NAME="test processor", pre_start=lambda: True,
        process_image=process_image, process_video=process_video,
    )


def image_files(tmp_path):
    target = tmp_path / "input.png"
    destination = tmp_path / "output.png"
    assert cv2.imwrite(str(target), np.full((4, 4, 3), 30, dtype=np.uint8))
    destination.write_bytes(b"previous export")
    return target, destination


def test_image_copy_failure_aborts_before_processor_and_preserves_export(monkeypatch, tmp_path):
    target, destination = image_files(tmp_path)
    calls = []
    configure_render(monkeypatch, target, destination, [processor(lambda *_: calls.append(True))])

    def fail_copy(*_):
        raise OSError("disk full")

    monkeypatch.setattr(core.shutil, "copyfile", fail_copy)
    assert core.start() is False
    assert calls == []
    assert destination.read_bytes() == b"previous export"
    assert list(tmp_path.glob(".output-*")) == []


@pytest.mark.parametrize("outcome", [False, None, "exception", "unreadable"])
def test_image_failure_after_first_processor_preserves_export(monkeypatch, tmp_path, outcome):
    target, destination = image_files(tmp_path)
    calls = []

    def first(_source, _target, output):
        calls.append("first")
        return cv2.imwrite(output, np.full((4, 4, 3), 90, dtype=np.uint8))

    def second(_source, _target, output):
        calls.append("second")
        if outcome == "exception":
            raise OSError("encoder error")
        if outcome == "unreadable":
            Path(output).write_bytes(b"invalid image")
            return True
        return outcome

    configure_render(monkeypatch, target, destination, [processor(first), processor(second)])
    assert core.start() is False
    assert calls == ["first", "second"]
    assert destination.read_bytes() == b"previous export"
    assert list(tmp_path.glob(".output-*")) == []


def test_image_is_published_only_after_all_processors_succeed(monkeypatch, tmp_path):
    target, destination = image_files(tmp_path)

    def process(_source, input_path, output_path):
        assert Path(output_path).parent == destination.parent
        assert Path(output_path) != destination
        assert input_path == output_path
        assert destination.read_bytes() == b"previous export"
        return cv2.imwrite(output_path, np.full((4, 4, 3), 150, dtype=np.uint8))

    configure_render(monkeypatch, target, destination, [processor(process)])
    assert core.start() is True
    assert int(cv2.imread(str(destination))[0, 0, 0]) == 150
    assert int(cv2.imread(str(target))[0, 0, 0]) == 30


def test_read_only_input_does_not_make_image_staging_read_only(monkeypatch, tmp_path):
    target, destination = image_files(tmp_path)
    configure_render(monkeypatch, target, destination, [processor(
        lambda _source, _target, output: cv2.imwrite(
            output, np.full((4, 4, 3), 110, dtype=np.uint8)
        )
    )])
    target.chmod(stat.S_IREAD)
    try:
        assert core.start() is True
        assert int(cv2.imread(str(destination))[0, 0, 0]) == 110
    finally:
        target.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_mapped_image_uses_original_mapping_with_staged_path(monkeypatch, tmp_path):
    target, destination = image_files(tmp_path)
    configure_render(monkeypatch, target, destination, [face_swapper])
    monkeypatch.setattr(face_swapper, "pre_start", lambda: True)
    monkeypatch.setattr(modules.globals, "map_faces", True)
    monkeypatch.setattr(modules.globals, "many_faces", False)
    monkeypatch.setattr(modules.globals, "opacity", 1.0)
    source_face, target_face = {"source": True}, {"target": True}
    monkeypatch.setattr(modules.globals, "source_target_map", [
        {"source": {"face": source_face}, "target": {"face": target_face}},
    ])
    pairs_seen = []

    def swap(frame, pairs):
        pairs_seen.extend(pairs)
        return frame + 10

    monkeypatch.setattr(face_swapper, "_swap_source_target_pairs", swap)
    assert core.start() is True
    assert pairs_seen == [(source_face, target_face)]
    assert int(cv2.imread(str(destination))[0, 0, 0]) == 40


@pytest.mark.parametrize("module", [face_swapper, face_enhancer, face_enhancer_gpen256, face_enhancer_gpen512])
@pytest.mark.parametrize("write_succeeds", [False, True])
def test_image_processors_return_write_result(monkeypatch, module, write_succeeds):
    monkeypatch.setattr(modules.globals, "map_faces", False)
    monkeypatch.setattr(modules.globals, "headless", True)
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    monkeypatch.setattr(module, "read_image", lambda _: frame)
    if module is face_swapper:
        monkeypatch.setattr(module, "get_one_face", lambda _: object())
    monkeypatch.setattr(module, "process_frame", lambda *_: frame)
    monkeypatch.setattr(module, "write_image", lambda *_: write_succeeds)
    assert module.process_image("source.png", "target.png", "output.png") is write_succeeds


@pytest.mark.parametrize("module", [face_swapper, face_enhancer, face_enhancer_gpen256, face_enhancer_gpen512])
def test_image_processors_reject_unreadable_input(monkeypatch, module):
    monkeypatch.setattr(modules.globals, "headless", True)
    monkeypatch.setattr(module, "read_image", lambda _: None)
    assert module.process_image("source.png", "target.png", "output.png") is False


@pytest.mark.parametrize("failure", ["copy", "replace"])
def test_video_publication_failure_preserves_previous_export(monkeypatch, tmp_path, failure):
    target = str(tmp_path / "source.mp4")
    temporary = Path(utilities.get_temp_output_path(target))
    temporary.write_bytes(b"new video")
    destination = tmp_path / "output.mp4"
    destination.write_bytes(b"old video")

    def fail(*_):
        raise OSError("publication denied")

    if failure == "copy":
        monkeypatch.setattr(utilities.shutil, "copyfile", fail)
    else:
        monkeypatch.setattr(utilities.os, "replace", fail)
    assert utilities.move_temp(target, str(destination)) is False
    assert destination.read_bytes() == b"old video"
    assert temporary.read_bytes() == b"new video"
    assert list(tmp_path.glob(".output-*")) == []


def test_video_publication_replaces_from_destination_volume(monkeypatch, tmp_path):
    target = str(tmp_path / "source.mp4")
    temporary = Path(utilities.get_temp_output_path(target))
    temporary.write_bytes(b"new video")
    destination = tmp_path / "output.mp4"
    destination.write_bytes(b"old video")
    replace = utilities.os.replace

    def check_replace(source, output):
        assert Path(source).parent == destination.parent
        assert Path(source) != temporary
        assert destination.read_bytes() == b"old video"
        replace(source, output)

    monkeypatch.setattr(utilities.os, "replace", check_replace)
    assert utilities.move_temp(target, str(destination)) is True
    assert destination.read_bytes() == b"new video"


@pytest.mark.parametrize("remux_succeeds", [False, True])
def test_audio_remux_stages_before_replacement(monkeypatch, tmp_path, remux_succeeds):
    target = str(tmp_path / "source.mp4")
    Path(utilities.get_temp_output_path(target)).write_bytes(b"video")
    destination = tmp_path / "output.mp4"
    destination.write_bytes(b"old video")

    def remux(args):
        assert "1:a:0?" in args
        assert Path(args[-1]).parent == destination.parent
        assert Path(args[-1]) != destination
        assert destination.read_bytes() == b"old video"
        Path(args[-1]).write_bytes(b"video with audio")
        return remux_succeeds

    monkeypatch.setattr(utilities, "run_ffmpeg", remux)
    assert utilities.restore_audio(target, str(destination)) is remux_succeeds
    assert destination.read_bytes() == (b"video with audio" if remux_succeeds else b"old video")
    assert list(tmp_path.glob(".output-*")) == []


def test_finalization_failure_is_not_reported_as_success(monkeypatch, tmp_path, capsys):
    target, destination = tmp_path / "input.mp4", tmp_path / "output.mp4"
    destination.write_bytes(b"old video")
    configure_render(monkeypatch, target, destination, [processor()])
    monkeypatch.setattr(frame_core, "process_video_in_memory", lambda *_: True)
    monkeypatch.setattr(core, "move_temp", lambda *_: False)
    assert core.start() is False
    assert "Video finalization failed" in capsys.readouterr().out
    assert destination.read_bytes() == b"old video"
    assert utilities._TEMP_WORKSPACES == {}


def test_mapping_workspace_is_reused_through_render_and_cleaned(monkeypatch, tmp_path):
    target, destination = tmp_path / "input.mp4", tmp_path / "output.mp4"
    configure_render(monkeypatch, target, destination, [])
    monkeypatch.setattr(modules.globals, "map_faces", True)
    utilities.create_temp(str(target))
    workspace = Path(utilities.get_temp_directory_path(str(target)))
    mapped_frame = workspace / "0001.png"
    mapped_frame.write_bytes(b"frame")
    # These exact file paths are stored by face mapping before render starts.
    observed = []
    modules_to_use = [processor(process_video=lambda _, frames: observed.extend(frames))]
    monkeypatch.setattr(frame_core, "get_frame_processors_modules", lambda _: modules_to_use)
    monkeypatch.setattr(core, "create_video", lambda *_: True)
    monkeypatch.setattr(core, "move_temp", lambda *_: True)
    utilities.create_temp(str(target))
    assert utilities.get_temp_directory_path(str(target)) == str(workspace)
    assert core.start() is True
    assert observed == [str(mapped_frame)]
    assert not workspace.exists()
    assert utilities._TEMP_WORKSPACES == {}


def test_actual_mapping_setup_hands_recorded_frame_paths_to_render(monkeypatch, tmp_path):
    target, destination = tmp_path / "input.mp4", tmp_path / "output.mp4"
    configure_render(monkeypatch, target, destination, [])
    monkeypatch.setattr(modules.globals, "map_faces", True)
    monkeypatch.setattr(modules.globals, "source_target_map", [])

    class MappedFace(dict):
        normed_embedding = np.array([1.0, 0.0], dtype=np.float32)

    def extract(target_path):
        frame_path = Path(utilities.get_temp_directory_path(target_path)) / "0001.png"
        return cv2.imwrite(str(frame_path), np.zeros((4, 4, 3), dtype=np.uint8))

    monkeypatch.setattr(face_analyser, "extract_frames", extract)
    monkeypatch.setattr(face_analyser, "get_many_faces", lambda _: [MappedFace()])
    monkeypatch.setattr(face_analyser, "find_cluster_centroids", lambda _: [[1.0, 0.0]])
    monkeypatch.setattr(face_analyser, "find_closest_centroid", lambda *_: (0, 0.0))
    monkeypatch.setattr(face_analyser, "default_target_face", lambda: None)
    face_analyser.get_unique_faces_from_target_video()
    recorded = modules.globals.source_target_map[0]["target_faces_in_frame"][0]["location"]
    observed = []
    monkeypatch.setattr(frame_core, "get_frame_processors_modules", lambda _: [
        processor(process_video=lambda _, frames: observed.extend(frames)),
    ])
    monkeypatch.setattr(core, "create_video", lambda *_: True)
    monkeypatch.setattr(core, "move_temp", lambda *_: True)
    assert core.start() is True
    assert observed == [recorded]
    assert not Path(recorded).exists()


def test_mapping_setup_stops_on_failed_extraction(monkeypatch, tmp_path):
    monkeypatch.setattr(modules.globals, "target_path", str(tmp_path / "input.mp4"))
    monkeypatch.setattr(modules.globals, "source_target_map", [])
    monkeypatch.setattr(face_analyser, "extract_frames", lambda _: False)
    face_analyser.get_unique_faces_from_target_video()
    assert modules.globals.source_target_map == []
    assert utilities._TEMP_WORKSPACES == {}


def test_same_stem_inputs_have_distinct_owned_workspaces_and_keep_frames(monkeypatch, tmp_path, capsys):
    first, second = str(tmp_path / "clip.mp4"), str(tmp_path / "clip.mkv")
    first_dir = Path(utilities.get_temp_directory_path(first))
    second_dir = Path(utilities.get_temp_directory_path(second))
    assert first_dir != second_dir
    (first_dir / "0001.png").write_bytes(b"retained frame")
    monkeypatch.setattr(modules.globals, "keep_frames", True)
    utilities.clean_temp(first)
    assert first_dir.exists()
    assert str(first_dir) in capsys.readouterr().out
    assert Path(utilities.get_temp_directory_path(first)) != first_dir
    assert utilities.get_temp_frame_paths(first) == []
    assert second_dir.exists()


def test_cleanup_never_deletes_preexisting_input_parent_temp(monkeypatch, tmp_path):
    legacy = tmp_path / "temp" / "clip"
    legacy.mkdir(parents=True)
    (legacy / "precious.png").write_bytes(b"user data")
    target = str(tmp_path / "clip.mp4")
    utilities.clean_temp(target)
    assert utilities._TEMP_WORKSPACES == {}
    owned = Path(utilities.get_temp_directory_path(target))
    utilities.clean_temp(target)
    assert not owned.exists()
    assert (legacy / "precious.png").read_bytes() == b"user data"


def test_destroy_cleans_abandoned_mapping_workspaces(monkeypatch, tmp_path):
    first = Path(utilities.get_temp_directory_path(str(tmp_path / "first.mp4")))
    second = Path(utilities.get_temp_directory_path(str(tmp_path / "second.mp4")))
    monkeypatch.setattr(modules.globals, "target_path", str(tmp_path / "second.mp4"))
    core.destroy(to_quit=False)
    assert not first.exists() and not second.exists()
    assert utilities._TEMP_WORKSPACES == {}


def test_cleanup_failure_preserves_ownership_and_blocks_stale_frame_reuse(monkeypatch, tmp_path):
    target, destination = tmp_path / "input.mp4", tmp_path / "output.mp4"
    configure_render(monkeypatch, target, destination, [processor()])
    workspace = Path(utilities.get_temp_directory_path(str(target)))
    (workspace / "0001.png").write_bytes(b"stale frame")
    remove_tree = utilities.shutil.rmtree

    def locked(_):
        raise PermissionError("frame is in use")

    monkeypatch.setattr(utilities.shutil, "rmtree", locked)
    assert utilities.clean_temp(str(target)) is False
    assert str(workspace) in utilities._TEMP_WORKSPACES.values()
    assert core.start() is False
    assert not destination.exists()
    monkeypatch.setattr(utilities.shutil, "rmtree", remove_tree)
    assert utilities.clean_temp(str(target)) is True
    assert not workspace.exists()
    assert utilities._TEMP_WORKSPACES == {}


def test_cleanup_failure_does_not_override_successful_export(monkeypatch, tmp_path, capsys):
    target, destination = tmp_path / "input.mp4", tmp_path / "output.mp4"
    configure_render(monkeypatch, target, destination, [processor()])

    def render(_source, target_path, _fps):
        Path(utilities.get_temp_output_path(target_path)).write_bytes(b"new video")
        return True

    def locked(_):
        raise PermissionError("frame is in use")

    monkeypatch.setattr(frame_core, "process_video_in_memory", render)
    monkeypatch.setattr(utilities.shutil, "rmtree", locked)
    assert core.start() is True
    assert destination.read_bytes() == b"new video"
    assert "Temporary cleanup failed" in capsys.readouterr().out
    assert len(utilities._TEMP_WORKSPACES) == 1


@pytest.mark.parametrize("probe_output", [b"0/0", b"0/1", b"-1/2", b"N/A", b"garbage"])
def test_invalid_fps_uses_positive_fallback(monkeypatch, probe_output):
    monkeypatch.setattr(utilities.subprocess, "check_output", lambda _: probe_output)
    assert utilities.detect_fps("video.mp4") == 30.0


def test_missing_ffprobe_uses_fps_fallback(monkeypatch):
    def missing(_):
        raise FileNotFoundError("ffprobe unavailable")
    monkeypatch.setattr(utilities.subprocess, "check_output", missing)
    assert utilities.detect_fps("video.mp4") == 30.0


def test_normalize_output_allows_missing_optional_path():
    assert utilities.normalize_output_path("source.png", "target.mp4", None) is None


@pytest.mark.parametrize("completed", [False, True])
def test_headless_render_exits_with_result(monkeypatch, completed):
    monkeypatch.setattr(core, "parse_args", lambda: None)
    monkeypatch.setattr(core, "pre_check", lambda: True)
    monkeypatch.setattr(core, "limit_resources", lambda: None)
    monkeypatch.setattr(core, "start", lambda: completed)
    monkeypatch.setattr(frame_core, "get_frame_processors_modules", lambda _: [])
    monkeypatch.setattr(modules.globals, "headless", True)
    monkeypatch.setattr(modules.globals, "download_models", False)
    monkeypatch.setattr(modules.globals, "check_execution_provider", False)
    with pytest.raises(SystemExit) as caught:
        core.run()
    assert caught.value.code == (0 if completed else 1)


@pytest.mark.parametrize("failing_check", ["application", "processor"])
def test_headless_precheck_failures_exit_nonzero(monkeypatch, failing_check):
    monkeypatch.setattr(core, "parse_args", lambda: None)
    monkeypatch.setattr(core, "pre_check", lambda: failing_check != "application")
    monkeypatch.setattr(frame_core, "get_frame_processors_modules", lambda _: [
        SimpleNamespace(pre_check=lambda: False),
    ])
    monkeypatch.setattr(modules.globals, "headless", True)
    monkeypatch.setattr(modules.globals, "download_models", False)
    monkeypatch.setattr(modules.globals, "check_execution_provider", False)
    with pytest.raises(SystemExit) as caught:
        core.run()
    assert caught.value.code == 1


def test_headless_precheck_requires_ffprobe(monkeypatch, capsys):
    monkeypatch.setattr(modules.globals, "headless", True)
    monkeypatch.setattr(core.shutil, "which", lambda name: "ffmpeg.exe" if name == "ffmpeg" else None)
    assert core.pre_check() is False
    assert "ffprobe" in capsys.readouterr().out
