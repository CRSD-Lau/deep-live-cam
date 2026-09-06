from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import pytest

import modules.globals
from modules import core, utilities
from modules.processors.frame import core as frame_core
from modules.processors.frame import (
    face_enhancer, face_enhancer_gpen256, face_enhancer_gpen512, face_swapper,
)


PROCESSORS = (face_swapper, face_enhancer, face_enhancer_gpen256, face_enhancer_gpen512)


def save_fixture(path, value=30):
    Image.new("RGB", (5, 4), (value, value, value)).save(path, "PNG")


def test_write_image_round_trips_unicode_directory_and_filename(tmp_path):
    directory = tmp_path / "Café_汉字_🙂"
    directory.mkdir()
    destination = directory / "成果_é.png"
    frame = np.arange(60, dtype=np.uint8).reshape((4, 5, 3))

    assert utilities.write_image(str(destination), frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])

    np.testing.assert_array_equal(utilities.read_image(str(destination)), frame)
    assert [path.name for path in directory.iterdir()] == [destination.name]


def test_write_image_preserves_alpha_and_forwards_encoding_options(monkeypatch, tmp_path):
    destination = tmp_path / "透明.PNG"
    frame = np.arange(80, dtype=np.uint8).reshape((4, 5, 4))
    params = [cv2.IMWRITE_PNG_COMPRESSION, 1]
    imencode = cv2.imencode
    calls = []

    def record_encode(extension, value, options):
        calls.append((extension, options))
        return imencode(extension, value, options)

    def forbidden_imwrite(*_):
        raise AssertionError("OpenCV path-based writes cannot safely handle Unicode")

    monkeypatch.setattr(utilities.cv2, "imencode", record_encode)
    monkeypatch.setattr(utilities.cv2, "imwrite", forbidden_imwrite)

    assert utilities.write_image(str(destination), frame, params)

    assert calls == [(".PNG", params)]
    np.testing.assert_array_equal(
        utilities.read_image(str(destination), cv2.IMREAD_UNCHANGED), frame,
    )


@pytest.mark.parametrize("frame", [None, np.zeros((0, 5, 3), dtype=np.uint8)])
def test_invalid_image_does_not_replace_existing_file(tmp_path, frame):
    destination = tmp_path / "成果.png"
    destination.write_bytes(b"existing image")

    assert utilities.write_image(str(destination), frame) is False
    assert destination.read_bytes() == b"existing image"
    assert [path.name for path in tmp_path.iterdir()] == [destination.name]


def test_unsupported_codec_preserves_existing_destination(tmp_path):
    destination = tmp_path / "成果.unsupported"
    destination.write_bytes(b"existing image")

    assert utilities.write_image(str(destination), np.zeros((4, 5, 3), dtype=np.uint8)) is False
    assert destination.read_bytes() == b"existing image"
    assert [path.name for path in tmp_path.iterdir()] == [destination.name]


@pytest.mark.parametrize("failure", ["encode-false", "encode-error", "write", "short-write", "replace"])
def test_write_image_failure_preserves_existing_unicode_file(monkeypatch, tmp_path, failure):
    destination = tmp_path / "成果_é.png"
    save_fixture(destination)
    original = destination.read_bytes()
    frame = np.full((4, 5, 3), 150, dtype=np.uint8)

    if failure == "encode-false":
        monkeypatch.setattr(utilities.cv2, "imencode", lambda *_: (False, None))
    elif failure == "encode-error":
        def failed_encode(*_):
            raise cv2.error("encoding failed")
        monkeypatch.setattr(utilities.cv2, "imencode", failed_encode)
    elif failure in {"write", "short-write"}:
        original_write = Path.write_bytes

        def partial_write(path, payload):
            written = original_write(path, payload[:3])
            if failure == "write":
                raise OSError("disk full")
            return written

        monkeypatch.setattr(Path, "write_bytes", partial_write)
    else:
        def denied_replace(*_):
            raise PermissionError("destination is in use")
        monkeypatch.setattr(utilities.os, "replace", denied_replace)

    assert utilities.write_image(str(destination), frame) is False
    assert destination.read_bytes() == original
    assert [path.name for path in tmp_path.iterdir()] == [destination.name]


@pytest.mark.parametrize("module", PROCESSORS)
@pytest.mark.parametrize("unicode_directory", [False, True])
def test_each_image_processor_replaces_actual_unicode_staging_file(
    monkeypatch, tmp_path, module, unicode_directory,
):
    directory = tmp_path / ("人物_é" if unicode_directory else "images")
    directory.mkdir()
    source = directory / "源.png"
    staging = directory / ".成果-暂存.png"
    save_fixture(source, 10)
    save_fixture(staging, 30)
    monkeypatch.setattr(modules.globals, "headless", True)
    monkeypatch.setattr(modules.globals, "map_faces", False)
    monkeypatch.setattr(module, "process_frame", lambda _source, frame: frame + 40)
    if module is face_swapper:
        monkeypatch.setattr(module, "get_one_face", lambda _: object())

    assert module.process_image(str(source), str(staging), str(staging)) is True
    np.testing.assert_array_equal(
        utilities.read_image(str(staging)), np.full((4, 5, 3), 70, dtype=np.uint8),
    )
    assert {path.name for path in directory.iterdir()} == {source.name, staging.name}


@pytest.mark.parametrize("module", PROCESSORS)
def test_disk_processors_read_and_write_frames_under_unicode_temp_directory(
    monkeypatch, tmp_path, module,
):
    directory = tmp_path / "临时帧_é"
    directory.mkdir()
    source = directory / "源.png"
    frame_path = directory / "0001.png"
    save_fixture(source, 10)
    save_fixture(frame_path, 30)
    monkeypatch.setattr(modules.globals, "headless", True)
    monkeypatch.setattr(modules.globals, "map_faces", False)
    monkeypatch.setattr(module, "process_frame", lambda _source, frame: frame + 40)
    if module is face_swapper:
        monkeypatch.setattr(module, "get_one_face", lambda _: object())

    module.process_frames(str(source), [str(frame_path)])

    np.testing.assert_array_equal(
        utilities.read_image(str(frame_path)), np.full((4, 5, 3), 70, dtype=np.uint8),
    )
    assert {path.name for path in directory.iterdir()} == {source.name, frame_path.name}


def test_render_publishes_all_processor_changes_to_unicode_destination(monkeypatch, tmp_path):
    source = tmp_path / "源.png"
    target = tmp_path / "対象.png"
    destination = tmp_path / "成果.png"
    save_fixture(source, 10)
    save_fixture(target, 30)
    destination.write_bytes(b"previous export")
    for name, value in {
        "source_path": str(source), "target_path": str(target),
        "output_path": str(destination), "headless": True,
        "map_faces": False, "nsfw_filter": False,
    }.items():
        monkeypatch.setattr(modules.globals, name, value)
    monkeypatch.setattr(frame_core, "get_frame_processors_modules", lambda _: list(PROCESSORS))
    monkeypatch.setattr(core, "release_resources", lambda: None)
    monkeypatch.setattr(face_swapper, "get_one_face", lambda _: object())
    for module in PROCESSORS:
        monkeypatch.setattr(module, "pre_start", lambda: True)
        monkeypatch.setattr(module, "process_frame", lambda _source, frame: frame + 10)

    assert core.start() is True

    np.testing.assert_array_equal(
        utilities.read_image(str(destination)), np.full((4, 5, 3), 70, dtype=np.uint8),
    )
    assert int(utilities.read_image(str(target))[0, 0, 0]) == 30
    assert {path.name for path in tmp_path.iterdir()} == {source.name, target.name, destination.name}
