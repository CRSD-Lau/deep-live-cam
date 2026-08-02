#!/usr/bin/env python3
"""Collect high-attention third-party license files into LICENSES/."""

from __future__ import annotations

import argparse
import shutil
import sys
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
)

PACKAGE_NOTICE_FILES = {
    "tensorflow": ("tensorflow/THIRD_PARTY_NOTICES.txt",),
    "opencv-python": ("cv2/LICENSE.txt", "cv2/LICENSE-3RD-PARTY.txt"),
    "onnxruntime-gpu": ("onnxruntime/LICENSE",),
    "onnxruntime-directml": ("onnxruntime/LICENSE",),
}

LICENSE_NAME_PREFIXES = ("license", "copying", "notice", "third_party")
ALWAYS_COPY = {"METADATA"}


def safe_name(name: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in name)


def is_notice_file(path: Path) -> bool:
    name = path.name.lower()
    return name in {item.lower() for item in ALWAYS_COPY} or name.startswith(LICENSE_NAME_PREFIXES)


def high_attention_packages(onnxruntime_package: str) -> tuple[str, ...]:
    return (
        BASE_HIGH_ATTENTION_PACKAGES[:2]
        + (onnxruntime_package,)
        + BASE_HIGH_ATTENTION_PACKAGES[2:]
    )


def collect(
    output: Path,
    onnxruntime_package: str = "onnxruntime-gpu",
) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    packages = high_attention_packages(onnxruntime_package)

    for package in packages:
        dist = metadata.distribution(package)
        name = dist.metadata["Name"]
        version = dist.version
        dist_info = Path(getattr(dist, "_path", ""))
        if not dist_info.exists():
            raise RuntimeError(f"Could not locate installed metadata for {name} {version}.")
        destination = output / f"{safe_name(name)}-{safe_name(version)}"
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=True)

        found = False
        for source in sorted(dist_info.rglob("*")):
            if not source.is_file() or not is_notice_file(source):
                continue
            relative = source.relative_to(dist_info)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
            found = True

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

    manifest = output / "README.md"
    lines = [
        "# Collected Third-Party License Files",
        "",
        "This folder is generated from the active build environment by `tools/collect_third_party_license_files.py`.",
        "It collects high-attention license, notice, and package metadata files that PyInstaller may not copy into the application payload by default.",
        "",
        "> [!IMPORTANT]",
        "> Regenerate this folder before each Windows release candidate, then review the diff before publishing.",
        "",
        "## Included Packages",
        "",
    ]
    for package in packages:
        dist = metadata.distribution(package)
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
