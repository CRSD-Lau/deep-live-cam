"""Generate the Windows Python dependency license snapshot."""

from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path


EXCLUDED_PACKAGES = {
    "altgraph": "PyInstaller/build tooling dependency; not an app runtime dependency.",
    "iniconfig": "Test tooling dependency; not an app runtime dependency.",
    "pefile": "PyInstaller/build tooling dependency; not an app runtime dependency.",
    "pip": "Build environment package manager; not an app runtime dependency.",
    "pluggy": "Test tooling dependency; not an app runtime dependency.",
    "pytest": "Test-only dependency; spec excludes pytest and tests.",
    "pyinstaller": "Build tooling only; not shipped as an app runtime dependency.",
    "pyinstaller-hooks-contrib": "Build tooling only; not shipped as an app runtime dependency.",
    "pywin32-ctypes": "PyInstaller/build tooling dependency; not an app runtime dependency.",
    "setuptools": "Build environment package; may appear via vendored metadata but is not a declared app runtime dependency.",
    "torch": "Spec excludes torch; bundle scan checks _internal/torch is absent.",
    "torchaudio": "Spec excludes torchaudio.",
    "torchvision": "Spec excludes torchvision.",
    "uv": "Tooling only; not part of app runtime.",
    "wheel": "Build environment package; not an app runtime dependency.",
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
    dists = sorted(metadata.distributions(), key=lambda dist: package_name(dist).lower())
    runtime_rows: list[str] = []
    excluded_rows: list[str] = []

    for dist in dists:
        name = package_name(dist)
        key = name.lower().replace("_", "-")
        license_text = normalize_license(dist)
        if key in EXCLUDED_PACKAGES:
            excluded_rows.append(row(name, dist.version, license_text, EXCLUDED_PACKAGES[key]))
        else:
            runtime_rows.append(row(name, dist.version, license_text))

    content = [
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
        "## Installed But Excluded From The Windows Bundle",
        "",
        "The local development environment may contain these packages, but they are build/test tooling or are excluded by the PyInstaller spec. Re-check the bundle scan before publishing.",
        "",
        "| Package | Version | License metadata observed | Exclusion evidence |",
        "| --- | ---: | --- | --- |",
        *excluded_rows,
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
