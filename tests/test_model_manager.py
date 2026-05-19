import hashlib
import sys

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
