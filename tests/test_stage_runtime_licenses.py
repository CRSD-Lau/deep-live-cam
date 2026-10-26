from pathlib import Path

import pytest

from tools import stage_runtime_licenses as staging


def license_source(tmp_path: Path, profile: str) -> Path:
    source = tmp_path / "source"
    notices = source / "THIRD_PARTY_LICENSES"
    notices.mkdir(parents=True)
    runtime = "onnxruntime-directml" if profile == "DirectML" else "onnxruntime-gpu"
    packages = [(runtime, "1.0"), ("pillow", "13.0.0"), ("certifi", "2026.10.23"),
                ("filelock", "4.2.4"), ("setuptools", "84.1.0")]
    if profile == "Cuda":
        packages.append(("torch", "2.11.0+cu128"))
    (notices / "README.md").write_text("\n".join(f"- `{name}` `{version}`" for name, version in packages), encoding="utf-8")
    for name, version in packages:
        path = notices / f"{name}-{version.replace('+', '_')}" / "licenses" / "LICENSE"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"Upstream licence\r\n")
    (notices / "old-package-1.0").mkdir()
    (source / "PYTHON_DEPENDENCIES.md").write_text("CUDA current inventory", encoding="utf-8")
    (source / "PYTHON_DEPENDENCIES_DIRECTML.md").write_text("DirectML current inventory", encoding="utf-8")
    return source


@pytest.mark.parametrize("profile", ["Cuda", "DirectML"])
def test_staging_retains_only_current_manifest_notices_and_marks_other_inventory(tmp_path, profile):
    source = license_source(tmp_path, profile)
    dist = tmp_path / "dist"
    old = dist / "LICENSES" / "THIRD_PARTY_LICENSES" / "stale-cuda-package"
    old.mkdir(parents=True)
    staging.stage(source, dist, profile)
    output = dist / "LICENSES"
    active = "PYTHON_DEPENDENCIES_DIRECTML.md" if profile == "DirectML" else "PYTHON_DEPENDENCIES.md"
    inactive = "PYTHON_DEPENDENCIES.md" if profile == "DirectML" else "PYTHON_DEPENDENCIES_DIRECTML.md"
    assert (output / active).read_bytes() == (source / active).read_bytes()
    marker = (output / inactive).read_text(encoding="utf-8")
    assert f"Not applicable to this {profile} runtime" in marker
    assert "author: Neil Mitchell" in marker
    assert not old.exists()
    assert not (output / "THIRD_PARTY_LICENSES/old-package-1.0").exists()
    assert (source / "THIRD_PARTY_LICENSES/old-package-1.0").exists()
    assert (output / "THIRD_PARTY_LICENSES/pillow-13.0.0/licenses/LICENSE").read_bytes() == b"Upstream licence\r\n"
    assert not list(dist.glob(".licenses-*"))


def test_wrong_profile_or_missing_notices_preserves_existing_destination(tmp_path):
    source = license_source(tmp_path, "DirectML")
    dist = tmp_path / "dist"
    sentinel = dist / "LICENSES/keep.txt"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="profile"):
        staging.stage(source, dist, "Cuda")
    (source / "THIRD_PARTY_LICENSES/pillow-13.0.0/licenses/LICENSE").unlink()
    (source / "THIRD_PARTY_LICENSES/pillow-13.0.0/licenses").rmdir()
    (source / "THIRD_PARTY_LICENSES/pillow-13.0.0").rmdir()
    with pytest.raises(ValueError, match="missing or unsafe"):
        staging.stage(source, dist, "DirectML")
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert not list(dist.glob(".licenses-*"))


def test_staging_refuses_source_as_runtime_destination(tmp_path):
    source = tmp_path / "LICENSES"
    source.mkdir()
    with pytest.raises(ValueError, match="generated runtime"):
        staging.stage(source, tmp_path, "Cuda")
