import hashlib
from http.client import IncompleteRead
import sys
from types import SimpleNamespace
import urllib.request

import pytest

from modules import model_manager


def make_spec(file_name: str, content: bytes) -> model_manager.ModelSpec:
    return model_manager.ModelSpec(
        file_name=file_name,
        url=f"https://example.test/{file_name}",
        sha256=hashlib.sha256(content).hexdigest(),
        source="example model source",
        license_note="example license note",
        required=True,
    )


def test_download_models_cancels_without_interactive_consent(monkeypatch, tmp_path, capsys):
    content = b"model bytes"
    spec = make_spec("required.onnx", content)
    monkeypatch.setattr(model_manager, "MODEL_SPECS", (spec,))
    monkeypatch.setattr(model_manager, "MODELS_DIR", str(tmp_path))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    exit_code = model_manager.download_models()

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Model download notice" in captured.out
    assert "example license note" in captured.out
    assert "Download cancelled" in captured.out
    assert not (tmp_path / "required.onnx").exists()


def test_download_models_writes_verified_file_after_consent(monkeypatch, tmp_path):
    content = b"verified model bytes"
    spec = make_spec("verified.onnx", content)
    monkeypatch.setattr(model_manager, "MODEL_SPECS", (spec,))
    monkeypatch.setattr(model_manager, "MODELS_DIR", str(tmp_path))

    def fake_download(url, destination):
        assert url == spec.url
        destination.write_bytes(content)

    monkeypatch.setattr(model_manager, "_download_file", fake_download)

    exit_code = model_manager.download_models(assume_yes=True)

    assert exit_code == 0
    assert (tmp_path / "verified.onnx").read_bytes() == content
    assert not (tmp_path / "verified.onnx.download").exists()


def test_download_models_removes_temporary_file_on_checksum_mismatch(
    monkeypatch,
    tmp_path,
    capsys,
):
    spec = make_spec("mismatch.onnx", b"expected bytes")
    monkeypatch.setattr(model_manager, "MODEL_SPECS", (spec,))
    monkeypatch.setattr(model_manager, "MODELS_DIR", str(tmp_path))

    def fake_download(url, destination):
        destination.write_bytes(b"unexpected bytes")

    monkeypatch.setattr(model_manager, "_download_file", fake_download)

    exit_code = model_manager.download_models(assume_yes=True)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Checksum mismatch for mismatch.onnx" in captured.out
    assert not (tmp_path / "mismatch.onnx").exists()
    assert not (tmp_path / "mismatch.onnx.download").exists()


def test_missing_models_accepts_existing_file_only_when_checksum_matches(
    monkeypatch,
    tmp_path,
):
    content = b"known model bytes"
    spec = make_spec("known.onnx", content)
    monkeypatch.setattr(model_manager, "MODEL_SPECS", (spec,))
    monkeypatch.setattr(model_manager, "MODELS_DIR", str(tmp_path))

    (tmp_path / "known.onnx").write_bytes(b"wrong bytes")
    assert model_manager.missing_models(required_only=True) == [spec]

    (tmp_path / "known.onnx").write_bytes(content)
    assert model_manager.missing_models(required_only=True) == []


def test_download_file_rejects_non_https_url_before_network_access(monkeypatch, tmp_path):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("No opener should be built for an insecure URL")

    monkeypatch.setattr(model_manager.urllib.request, "build_opener", fail_if_called)

    with pytest.raises(ValueError, match="non-HTTPS model download URL"):
        model_manager._download_file("http://example.test/model.onnx", tmp_path / "model.onnx")


def test_download_file_rejects_redirect_to_non_https_url(monkeypatch, tmp_path):
    class FakeResponse:
        headers = {"Content-Length": "0"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def geturl(self):
            return "http://example.test/model.onnx"

    monkeypatch.setattr(
        model_manager.urllib.request, "build_opener",
        lambda *_args: SimpleNamespace(open=lambda *_a, **_kw: FakeResponse()),
    )

    with pytest.raises(ValueError, match="non-HTTPS model download URL"):
        model_manager._download_file("https://example.test/model.onnx", tmp_path / "model.onnx")


@pytest.mark.parametrize("failure", [
    OSError("connection lost"), ValueError("insecure redirect"), IncompleteRead(b"partial"),
])
def test_interrupted_download_cleans_only_owned_file(monkeypatch, tmp_path, failure):
    spec = make_spec("required.onnx", b"expected")
    monkeypatch.setattr(model_manager, "MODEL_SPECS", (spec,))
    monkeypatch.setattr(model_manager, "MODELS_DIR", str(tmp_path))
    destination = tmp_path / spec.file_name
    destination.write_bytes(b"previous model")
    unrelated = tmp_path / "required.onnx.download"
    unrelated.write_bytes(b"another download")
    owned = []

    def fail_download(_url, temporary):
        owned.append(temporary)
        temporary.write_bytes(b"partial")
        raise failure

    monkeypatch.setattr(model_manager, "_download_file", fail_download)
    assert model_manager.download_models(assume_yes=True) == 1
    assert destination.read_bytes() == b"previous model"
    assert unrelated.read_bytes() == b"another download"
    assert all(not path.exists() for path in owned)


def test_download_publish_failure_preserves_destination(monkeypatch, tmp_path):
    spec = make_spec("required.onnx", b"expected")
    monkeypatch.setattr(model_manager, "MODEL_SPECS", (spec,))
    monkeypatch.setattr(model_manager, "MODELS_DIR", str(tmp_path))
    destination = tmp_path / spec.file_name
    destination.write_bytes(b"previous model")
    monkeypatch.setattr(model_manager, "_download_file", lambda _u, p: p.write_bytes(b"expected"))

    def fail_replace(*_args):
        raise PermissionError("destination busy")

    monkeypatch.setattr(model_manager.os, "replace", fail_replace)
    assert model_manager.download_models(assume_yes=True) == 1
    assert destination.read_bytes() == b"previous model"
    assert list(tmp_path.iterdir()) == [destination]


def test_https_redirect_handler_rejects_insecure_intermediate_hop():
    handler = model_manager._HTTPSRedirectHandler()
    request = urllib.request.Request("https://example.test/model.onnx")
    with pytest.raises(ValueError, match="non-HTTPS"):
        handler.redirect_request(request, None, 302, "Found", {}, "http://cdn.test/model.onnx")
    redirected = handler.redirect_request(
        request, None, 302, "Found", {}, "https://cdn.test/model.onnx"
    )
    assert redirected.full_url == "https://cdn.test/model.onnx"


def test_directory_is_not_a_verified_model(tmp_path):
    assert not model_manager.verify_model(tmp_path, make_spec("model.onnx", b""))


def test_locked_temporary_file_does_not_mask_download_failure(monkeypatch, tmp_path, capsys):
    spec = make_spec("required.onnx", b"expected")
    monkeypatch.setattr(model_manager, "MODEL_SPECS", (spec,))
    monkeypatch.setattr(model_manager, "MODELS_DIR", str(tmp_path))

    def failed_download(_url, _temporary):
        raise OSError("connection lost")

    def failed_unlink(*_args, **_kwargs):
        raise PermissionError("temporary file locked")

    monkeypatch.setattr(model_manager, "_download_file", failed_download)
    monkeypatch.setattr(model_manager.Path, "unlink", failed_unlink)
    assert model_manager.download_models(assume_yes=True) == 1
    output = capsys.readouterr().out
    assert "connection lost" in output
    assert "Could not remove temporary download" in output
    assert not (tmp_path / spec.file_name).exists()
