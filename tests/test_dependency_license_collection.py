import csv
from importlib import metadata

import pytest

from tools import collect_third_party_license_files as collector
from tools import generate_python_dependency_licenses as snapshot


def installed_distribution(tmp_path, name, version, package_files=None, metadata_files=None):
    site = tmp_path / "site-packages"
    info = site / f"{name}-{version}.dist-info"
    info.mkdir(parents=True, exist_ok=True)
    files = {
        f"{info.name}/METADATA": f"Name: {name}\nVersion: {version}\nLicense: MIT\n".encode(),
        **{f"{info.name}/{path}": value for path, value in (metadata_files or {}).items()},
        **(package_files or {}),
    }
    for relative, data in files.items():
        target = site / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    with (info / "RECORD").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows((relative, "", len(data)) for relative, data in files.items())
    return metadata.PathDistribution(info)


@pytest.mark.parametrize("profile", ["onnxruntime-gpu", "onnxruntime-directml"])
def test_both_profiles_collect_incidentally_frozen_build_tools(profile):
    assert {"pip", "setuptools"} <= set(collector.high_attention_packages(profile))


def test_collector_preserves_metadata_authors_and_arbitrary_license_supplements(tmp_path, monkeypatch):
    upstream = {
        "licenses/LICENSE.txt": b"Upstream licence\r\nDo not rewrite this.\r\n",
        "licenses/AUTHORS.txt": b"Upstream authors\r\n",
        "licenses/src/pip/_vendor/packaging/LICENSE.APACHE": b"Apache supplement\n",
        "licenses/custom/attribution.rst": b"Custom attribution\r\n",
    }
    dist = installed_distribution(tmp_path, "pip", "26.2.1", metadata_files=upstream)
    monkeypatch.setattr(collector, "high_attention_packages", lambda _: ("pip",))
    monkeypatch.setattr(collector, "package_distribution", lambda _: dist)

    output = tmp_path / "collected"
    collector.collect(output)

    for relative, original in upstream.items():
        assert (output / "pip-26.2.1" / relative).read_bytes() == original
    assert (output / "pip-26.2.1/METADATA").read_bytes() == (dist._path / "METADATA").read_bytes()
    manifest = (output / "README.md").read_text(encoding="utf-8")
    assert "`pip` `26.2.1`" in manifest
    assert "author: Neil Mitchell" in manifest


def test_collector_preserves_vendor_layout_and_config_notices_without_copying_code(tmp_path, monkeypatch):
    notices = {
        "setuptools/_vendor/first-1.0.dist-info/licenses/LICENSE": b"First vendor\r\n",
        "setuptools/_vendor/second-2.0.dist-info/LICENSE": b"Second vendor\n",
        "setuptools/_vendor/second-2.0.dist-info/METADATA": b"Name: second\nVersion: 2.0\n",
        "setuptools/config/NOTICE": b"Configuration attribution\n",
        "setuptools/config/_validate_pyproject/NOTICE": b"Validation attribution\n",
    }
    dist = installed_distribution(
        tmp_path,
        "setuptools",
        "83.0.0",
        package_files={
            **notices,
            "setuptools/_vendor/packaging/licenses/_spdx.py": b"must not copy code",
            "unrelated/LICENSE": b"must not copy another package",
        },
        metadata_files={"licenses/LICENSE": b"Setuptools licence"},
    )
    monkeypatch.setattr(collector, "high_attention_packages", lambda _: ("setuptools",))
    monkeypatch.setattr(collector, "package_distribution", lambda _: dist)

    output = tmp_path / "collected"
    collector.collect(output)

    for relative, original in notices.items():
        assert (output / "setuptools-83.0.0/package" / relative).read_bytes() == original
    assert not list(output.rglob("*.py"))
    assert not (output / "setuptools-83.0.0/package/unrelated").exists()


def test_metadata_alone_does_not_count_as_a_license(tmp_path, monkeypatch):
    dist = installed_distribution(tmp_path, "pip", "26.2.1")
    monkeypatch.setattr(collector, "high_attention_packages", lambda _: ("pip",))
    monkeypatch.setattr(collector, "package_distribution", lambda _: dist)

    with pytest.raises(RuntimeError, match="No license/notice"):
        collector.collect(tmp_path / "collected")


def test_missing_recorded_vendor_notice_fails_collection(tmp_path, monkeypatch):
    relative = "setuptools/_vendor/example/LICENSE"
    dist = installed_distribution(
        tmp_path,
        "setuptools",
        "83.0.0",
        package_files={relative: b"vendor terms"},
        metadata_files={"licenses/LICENSE": b"main terms"},
    )
    (dist._path.parent / relative).unlink()
    monkeypatch.setattr(collector, "high_attention_packages", lambda _: ("setuptools",))
    monkeypatch.setattr(collector, "package_distribution", lambda _: dist)

    with pytest.raises(RuntimeError, match="Expected package notice file not found"):
        collector.collect(tmp_path / "collected")


def test_vendor_notice_record_cannot_escape_package_root(tmp_path):
    dist = installed_distribution(tmp_path, "setuptools", "83.0.0")
    with (dist._path / "RECORD").open("a", encoding="utf-8") as handle:
        handle.write("setuptools/../../outside/LICENSE,,1\n")

    with pytest.raises(RuntimeError, match="escapes setuptools"):
        collector.supplemental_notice_files(dist)


def test_missing_distribution_record_cannot_hide_vendor_notices(tmp_path):
    dist = installed_distribution(tmp_path, "setuptools", "83.0.0")
    (dist._path / "RECORD").unlink()

    with pytest.raises(RuntimeError, match="without distribution file records"):
        collector.supplemental_notice_files(dist)


def test_build_tool_collection_uses_main_interpreter_metadata(tmp_path, monkeypatch):
    main = installed_distribution(tmp_path / "main", "pip", "26.2.1")
    helper = installed_distribution(tmp_path / "helper", "pip", "24.0")
    monkeypatch.setattr(collector.sysconfig, "get_path", lambda _: str(main._path.parent))
    monkeypatch.setattr(collector.metadata, "distribution", lambda _: helper)

    assert collector.package_distribution("pip").version == "26.2.1"
    assert collector.package_distribution("torch") is helper


def test_missing_main_build_tool_does_not_fall_back_to_helper(tmp_path, monkeypatch):
    helper = installed_distribution(tmp_path / "helper", "pip", "24.0")
    monkeypatch.setattr(collector.sysconfig, "get_path", lambda _: str(tmp_path / "empty"))
    monkeypatch.setattr(collector.metadata, "distribution", lambda _: helper)

    with pytest.raises(metadata.PackageNotFoundError):
        collector.package_distribution("pip")


def test_snapshot_reports_main_tool_versions_and_roles_without_claiming_exclusion(tmp_path, monkeypatch):
    pip = installed_distribution(tmp_path / "main", "pip", "26.2.1")
    setuptools = installed_distribution(tmp_path / "main", "setuptools", "83.0.0")
    old_pip = installed_distribution(tmp_path / "helper", "pip", "24.0")
    old_setuptools = installed_distribution(tmp_path / "helper", "setuptools", "65.5.0")
    torch = installed_distribution(tmp_path / "helper", "torch", "2.11.0+cu128")
    runtime = installed_distribution(tmp_path / "main", "onnxruntime-gpu", "1.24.4")
    monkeypatch.setattr(
        snapshot.metadata,
        "distributions",
        lambda path=None: [pip, setuptools, runtime] if path else [old_pip, old_setuptools, torch, pip, setuptools, runtime],
    )
    monkeypatch.setattr(snapshot.sysconfig, "get_path", lambda _: str(pip._path.parent))

    output = tmp_path / "snapshot.md"
    snapshot.generate(output)
    text = output.read_text(encoding="utf-8")

    assert text.count("| `pip` | `26.2.1` |") == 1
    assert text.count("| `setuptools` | `83.0.0` |") == 1
    assert "`24.0`" not in text and "`65.5.0`" not in text
    assert "| `torch` | `2.11.0+cu128` |" in text
    assert "| `onnxruntime-gpu` | `1.24.4` |" in text
    assert "Build and Support Package Metadata" in text
    assert "not proven exclusions" in text
    assert "both executable archives" in text
    assert "Installed But Excluded" not in text
    assert "not shipped as an app runtime" not in text
    assert "author: Neil Mitchell" in text
