"""Generate the Windows Python dependency license snapshot."""

from __future__ import annotations

import argparse
import sysconfig
from importlib import metadata
from pathlib import Path

BUILD_AND_SUPPORT_PACKAGES = {
    "altgraph": "PyInstaller build dependency; verify final payload inclusion separately.",
    "iniconfig": "Test support package; verify final payload inclusion separately.",
    "pefile": "PyInstaller build dependency; verify final payload inclusion separately.",
    "pip": "Build package manager; Python modules can be frozen incidentally. Preserve package and vendor notices.",
    "pluggy": "Test support package; verify final payload inclusion separately.",
    "pytest": "Test package; excluded by spec policy, subject to final payload verification.",
    "pyinstaller": "Packaging tool; bootstrap and runtime-hook code is included in frozen applications.",
    "pyinstaller-hooks-contrib": "Packaging hooks; selected runtime hooks can be included in the frozen application.",
    "pywin32-ctypes": "PyInstaller build dependency; verify final payload inclusion separately.",
    "setuptools": "Build backend; Python and vendored modules can be frozen incidentally. Preserve package and vendor notices.",
    "torch": "Isolated CUDA DLL source; Torch Python exclusion is spec policy and requires final archive/payload verification.",
    "torchaudio": "Excluded by spec policy; verify final payload separately.",
    "torchvision": "Excluded by spec policy; verify final payload separately.",
    "uv": "Build tool; verify final payload inclusion separately.",
    "wheel": "Build support package; verify final payload inclusion separately.",
}


def normalize_license(dist: metadata.Distribution) -> str:
    license_text = dist.metadata.get("License-Expression") or dist.metadata.get("License") or ""
    classifiers = [
        classifier.removeprefix("License :: ")
        for classifier in dist.metadata.get_all("Classifier") or []
        if classifier.startswith("License ::")
    ]
    if not license_text and classifiers:
        license_text = "; ".join(classifiers)
    license_text = " ".join(license_text.split())
    return license_text[:140] or "UNKNOWN"


def package_name(dist: metadata.Distribution) -> str:
    return dist.metadata.get("Name") or dist._path.name


def row(name: str, version: str, license_text: str, extra: str | None = None) -> str:
    columns = [f"`{name}`", f"`{version}`", license_text]
    if extra is not None:
        columns.append(extra)
    return "| " + " | ".join(columns) + " |"


def generate(output: Path) -> None:
    # PYTHONPATH can expose the isolated Torch helper. Its bootstrap tools must
    # not shadow or duplicate the versions used by the main build interpreter.
    main_packages = {"pip", "setuptools", "pyinstaller", "pyinstaller-hooks-contrib"}
    dists = [dist for dist in metadata.distributions() if package_name(dist).lower() not in main_packages]
    paths = sorted({sysconfig.get_path("purelib"), sysconfig.get_path("platlib")})
    dists.extend(dist for dist in metadata.distributions(path=paths) if package_name(dist).lower() in main_packages)
    dists.sort(key=lambda dist: package_name(dist).lower())
    runtime_rows: list[str] = []
    support_rows: list[str] = []

    for dist in dists:
        name = package_name(dist)
        key = name.lower().replace("_", "-")
        license_text = normalize_license(dist)
        if key in BUILD_AND_SUPPORT_PACKAGES:
            support_rows.append(row(name, dist.version, license_text, BUILD_AND_SUPPORT_PACKAGES[key]))
        else:
            runtime_rows.append(row(name, dist.version, license_text))

    content = [
        "---",
        "author: Neil Mitchell",
        "creator: Neil Mitchell",
        "last_modified_by: Neil Mitchell",
        "---",
        "",
        "# Python Dependency License Snapshot",
        "",
        "Generated from the active Python environment. Package metadata can be incomplete or overly broad; this snapshot is release evidence, not legal advice. Re-generate and review this file for each public release candidate.",
        "",
        "The PyInstaller build may collect native DLLs and data files from dependencies even when their `.dist-info` directories are not copied into `dist`. Treat the licenses below as the dependency set to review for Windows binary redistribution.",
        "",
        "## Runtime Dependency Metadata",
        "",
        "| Package | Version | License metadata observed |",
        "| --- | ---: | --- |",
        *runtime_rows,
        "",
        "## Build and Support Package Metadata",
        "",
        "This table records package roles in the build environment, not proven exclusions. PyInstaller can collect build/support modules incidentally, including pip and setuptools. Inspect the final native payload and both executable archives to establish what is actually bundled; retain notices for collected packages and their vendors.",
        "",
        "| Package | Version | License metadata observed | Role and payload verification |",
        "| --- | ---: | --- | --- |",
        *support_rows,
        "",
        "## High-Attention Items",
        "",
        "- `PySide6`, `PySide6_Addons`, `PySide6_Essentials`, and `shiboken6` carry LGPL/GPL options. Preserve Qt notices and do not prevent users from inspecting or replacing LGPL-covered components where required.",
        "- `pyvirtualcam` metadata currently reports GPLv2. Review compatibility with AGPL-3.0 before public binary distribution.",
        "- `cv2_enumerate_cameras` metadata includes GPL-3.0 text. Keep source availability and notices.",
        "- See `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md` for the bundled native-library and LGPL/GPL-family release checklist.",
        "- `namex` did not expose usable license metadata in this environment; inspect upstream before publishing if it remains `UNKNOWN`.",
        "- Native DLLs from ONNX Runtime GPU, TensorFlow, NumPy/SciPy OpenBLAS, OpenCV, and Qt may have additional notice files that should be preserved in the installer.",
        "",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(content), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="LICENSES/PYTHON_DEPENDENCIES.md",
        type=Path,
        help="Markdown output path.",
    )
    args = parser.parse_args()
    generate(args.output)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
