from types import SimpleNamespace

from tools import check_frozen_runtime_imports as frozen


def reader_with(modules):
    class Reader:
        def __init__(self, path):
            self.path = path

        def open_embedded_archive(self, name):
            assert name == "PYZ.pyz"
            filename = self.path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
            return SimpleNamespace(toc=modules[filename])
    return Reader


def test_embedded_vendor_rejected_even_without_external_pip_directory(tmp_path):
    reader = reader_with({
        "DeepLiveCamStudio.exe": ["modules.core", "pip._vendor.certifi"],
        "DeepLiveCamStudioCLI.exe": ["modules.core", "torch.jit"],
    })
    failures = frozen.check(tmp_path, reader)
    assert any("DeepLiveCamStudio.exe embeds forbidden module: pip._vendor.certifi" in item for item in failures)
    assert any("DeepLiveCamStudioCLI.exe embeds forbidden module: torch.jit" in item for item in failures)


def test_patched_main_certifi_is_allowed_but_external_pip_is_rejected(tmp_path):
    reader = reader_with({name: ["PIL", "certifi", "filelock", "setuptools"] for name in
                          ("DeepLiveCamStudio.exe", "DeepLiveCamStudioCLI.exe")})
    assert frozen.check(tmp_path, reader) == []
    (tmp_path / "_internal/pip").mkdir(parents=True)
    assert frozen.check(tmp_path, reader) == ["External runtime contains forbidden package: pip"]
