import pytest

from modules import utilities


def test_conditional_download_rejects_non_https_url_before_network_access(monkeypatch, tmp_path):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen should not be called for an insecure URL")

    monkeypatch.setattr(utilities.urllib.request, "urlopen", fail_if_called)

    with pytest.raises(ValueError, match="non-HTTPS download URL"):
        utilities.conditional_download(str(tmp_path), ["http://example.test/file.bin"])


def test_conditional_download_rejects_redirect_to_non_https_url(monkeypatch, tmp_path):
    class FakeResponse:
        headers = {"Content-Length": "0"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def geturl(self):
            return "http://example.test/file.bin"

    monkeypatch.setattr(utilities.urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse())

    with pytest.raises(ValueError, match="non-HTTPS download URL"):
        utilities.conditional_download(str(tmp_path), ["https://example.test/file.bin"])

    assert not (tmp_path / "file.bin").exists()
