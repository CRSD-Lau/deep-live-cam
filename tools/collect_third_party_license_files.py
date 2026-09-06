#!/usr/bin/env python3
"""Collect high-attention third-party license files into LICENSES/."""

from __future__ import annotations

import argparse
import shutil
import sys
import sysconfig
from importlib import metadata
from pathlib import Path

BASE_HIGH_ATTENTION_PACKAGES = (
    "tensorflow",
    "opencv-python",
    "onnx",
    "opennsfw2",
    "PySide6",
    "PySide6_Addons",
    "PySide6_Essentials",
    "shiboken6",
    "pyvirtualcam",
    "cv2_enumerate_cameras",
    "easydict",
    "pip",
    "setuptools",
)

# These build packages can be collected incidentally into the frozen runtime.
# Their metadata must come from the main interpreter, not the CUDA helper that
# is exposed through PYTHONPATH only so its torch notices can be collected.
MAIN_ENVIRONMENT_PACKAGES = {"pip", "setuptools"}

PACKAGE_NOTICE_FILES = {
    "tensorflow": ("tensorflow/THIRD_PARTY_NOTICES.txt",),
    "opencv-python": ("cv2/LICENSE.txt", "cv2/LICENSE-3RD-PARTY.txt"),
    "onnxruntime-gpu": ("onnxruntime/LICENSE",),
    "onnxruntime-directml": ("onnxruntime/LICENSE",),
}

LICENSE_NAME_PREFIXES = ("license", "licence", "copying", "notice", "third_party", "authors", "copyright")
ALWAYS_COPY = {"METADATA"}


def safe_name(name: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in name)


def is_notice_file(path: Path) -> bool:
    name = path.name.lower()
    return name in {item.lower() for item in ALWAYS_COPY} or name.startswith(LICENSE_NAME_PREFIXES)


def package_distribution(package: str) -> metadata.Distribution:
    if package not in MAIN_ENVIRONMENT_PACKAGES:
        return metadata.distribution(package)
    paths = sorted({sysconfig.get_path("purelib"), sysconfig.get_path("platlib")})
    for dist in metadata.distributions(path=paths):
        if dist.metadata["Name"].lower().replace("_", "-") == package:
            return dist
    raise metadata.PackageNotFoundError(package)


def supplemental_notice_files(dist: metadata.Distribution) -> list[Path]:
    """Find package-owned notices, including vendored licences, from RECORD."""
    package = dist.metadata["Name"].lower().replace("_", "-")
    if package not in MAIN_ENVIRONMENT_PACKAGES:
        return []
    site_packages = Path(dist._path).parent
    package_root = (site_packages / package).resolve()
    notices = []
    files = dist.files
    if files is None:
        raise RuntimeError(f"Cannot inventory package notices without distribution file records: {package}")
    for entry in files:
        relative = Path(entry)
        if not relative.parts or relative.parts[0] != package or not is_notice_file(relative):
            continue
        source = site_packages / relative
        if not source.resolve().is_relative_to(package_root):
            raise RuntimeError(f"Package notice path escapes {package}: {relative}")
        if not source.is_file():
            raise RuntimeError(f"Expected package notice file not found for {package}: {relative}")
        notices.append(relative)
    return sorted(notices)


def high_attention_packages(onnxruntime_package: str) -> tuple[str, ...]:
    accelerator_packages = (onnxruntime_package,)
    if onnxruntime_package == "onnxruntime-gpu":
        accelerator_packages += ("torch",)
    return (
        BASE_HIGH_ATTENTION_PACKAGES[:2]
        + accelerator_packages
        + BASE_HIGH_ATTENTION_PACKAGES[2:]
    )


def collect(
    output: Path,
    onnxruntime_package: str = "onnxruntime-gpu",
) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    collected_distributions: list[metadata.Distribution] = []
    packages = high_attention_packages(onnxruntime_package)

    for package in packages:
        dist = package_distribution(package)
        name = dist.metadata["Name"]
        version = dist.version
        dist_info = Path(getattr(dist, "_path", ""))
        if not dist_info.exists():
            raise RuntimeError(f"Could not locate installed metadata for {name} {version}.")
        destination = output / f"{safe_name(name)}-{safe_name(version)}"
        if not destination.resolve().is_relative_to(output.resolve()):
            raise RuntimeError(f"License destination escapes the output directory: {destination.name}")
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=True)

        found = False
        for source in sorted(dist_info.rglob("*")):
            # PEP 639 permits arbitrary filenames below dist-info/licenses,
            # including AUTHORS and vendor-specific attribution supplements.
            relative = source.relative_to(dist_info)
            in_license_directory = relative.parts[0].lower() == "licenses"
            if not source.is_file() or not (is_notice_file(source) or in_license_directory):
                continue
            if not source.resolve().is_relative_to(dist_info.resolve()):
                raise RuntimeError(f"Metadata notice path escapes {name}: {relative}")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
            found = found or source.name != "METADATA"

        for relative in supplemental_notice_files(dist):
            source = dist_info.parent / relative
            target = destination / "package" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
            found = found or source.name != "METADATA"

        site_packages = dist_info.parent
        for relative_notice in PACKAGE_NOTICE_FILES.get(package, ()):
            source = site_packages / relative_notice
            if not source.is_file():
                raise RuntimeError(f"Expected package notice file not found for {name} {version}: {source}")
            target = destination / "package" / Path(relative_notice).name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
            found = True

        if not found:
            raise RuntimeError(f"No license/notice metadata files found for {name} {version} in {dist_info}.")
        collected_distributions.append(dist)

    manifest = output / "README.md"
    lines = [
        "---",
        "author: Neil Mitchell",
        "creator: Neil Mitchell",
        "last_modified_by: Neil Mitchell",
        "---",
        "",
        "# Collected Third-Party License Files",
        "",
        "This folder is generated from the active build environment by `tools/collect_third_party_license_files.py`.",
        "It collects high-attention license, notice, and package metadata files that PyInstaller may not copy into the application payload by default.",
        "Build packages such as pip and setuptools can be frozen incidentally; their notices and vendored licences are included without claiming every package file is bundled.",
        "",
        "> [!IMPORTANT]",
        "> Regenerate this folder before each Windows release candidate, then review the diff before publishing.",
        "",
        "## Included Packages",
        "",
    ]
    for dist in collected_distributions:
        lines.append(f"- `{dist.metadata['Name']}` `{dist.version}`")
    lines.extend(
        [
            "",
            "## Review Checklist",
            "",
            "- Confirm package versions match the release build environment.",
            "- Keep original license and notice text intact.",
            "- Re-run the collector whenever dependencies change.",
            "- Update `LICENSES/PYTHON_DEPENDENCIES.md` and `THIRD_PARTY_NOTICES.md` when the license posture changes.",
            "",
        ]
    )
    manifest.write_text("\n".join(lines), encoding="utf-8")
    copied.append(manifest)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect high-attention third-party license files.")
    parser.add_argument("--output", default="LICENSES/THIRD_PARTY_LICENSES", help="Destination folder.")
    parser.add_argument(
        "--onnxruntime-package",
        choices=("onnxruntime-gpu", "onnxruntime-directml"),
        default="onnxruntime-gpu",
        help="Installed ONNX Runtime distribution to collect.",
    )
    args = parser.parse_args()

    try:
        copied = collect(Path(args.output), args.onnxruntime_package)
    except Exception as exc:
        print(f"Failed to collect third-party license files: {exc}", file=sys.stderr)
        return 1

    print(f"Collected {len(copied)} third-party license metadata files into {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
