#!/usr/bin/env python3
"""Generate a Windows bundle manifest from a PyInstaller dist folder."""

from __future__ import annotations

import argparse
import datetime as _datetime
import email.parser
from pathlib import Path

FORBIDDEN_MODEL_SUFFIXES = {".onnx", ".pth", ".safetensors"}
NATIVE_SUFFIXES = {".dll", ".pyd", ".exe", ".lib", ".so"}
DEV_ONLY_PATHS = (
    "_internal/matplotlib/mpl-data/sample_data",
    "_internal/sklearn/datasets/data",
    "_internal/sklearn/datasets/images",
    "_internal/sklearn/datasets/tests",
)
REQUIRED_RELEASE_FILES = (
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "COMPLIANCE.md",
    "RELEASE_CHECKLIST.md",
    "RELEASE_REPORT.md",
    "RELEASE_SOURCE_PREP.md",
    "MODEL_DOWNLOAD_VERIFICATION.md",
    "PROCESSING_VERIFICATION.md",
    "docs/OBS_VIRTUAL_CAMERA.md",
    "LICENSES/BUNDLED_BINARY_OBLIGATIONS.md",
    "LICENSES/MODEL_LICENSE_AUDIT.md",
    "LICENSES/PYTHON_DEPENDENCIES.md",
    "LICENSES/THIRD_PARTY_LICENSES/README.md",
    "LICENSES/THIRD_PARTY_LICENSES/tensorflow-2.19.1/package/THIRD_PARTY_NOTICES.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-gpu-1.23.2/package/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opencv-python-4.10.0.84/package/LICENSE-3RD-PARTY.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnx-1.18.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opennsfw2-0.10.2/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/licenses/LicenseRef-Qt-Commercial.txt",
    "LICENSES/THIRD_PARTY_LICENSES/shiboken6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE",
)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_metadata(dist_info: Path) -> dict[str, str]:
    metadata_file = dist_info / "METADATA"
    name = dist_info.name.removesuffix(".dist-info")
    version = ""
    license_text = ""

    if metadata_file.exists():
        message = email.parser.Parser().parsestr(metadata_file.read_text(encoding="utf-8", errors="replace"))
        name = message.get("Name", name)
        version = message.get("Version", "")
        license_text = message.get("License", "")
        if not license_text:
            classifiers = message.get_all("Classifier", [])
            license_classifiers = [item for item in classifiers if item.startswith("License ::")]
            license_text = "; ".join(license_classifiers)

    return {
        "name": name.strip(),
        "version": version.strip(),
        "license": " ".join(license_text.split()) if license_text else "UNKNOWN",
        "path": dist_info,
    }


def native_summary(files: list[Path], root: Path) -> list[tuple[str, int, int]]:
    summary: dict[str, tuple[int, int]] = {}
    for path in files:
        relative_parts = path.relative_to(root).parts
        bucket = relative_parts[0] if len(relative_parts) == 1 else "/".join(relative_parts[:2])
        count, size = summary.get(bucket, (0, 0))
        summary[bucket] = (count + 1, size + path.stat().st_size)
    return sorted((bucket, count, size) for bucket, (count, size) in summary.items())


def generate(dist_dir: Path) -> str:
    dist_dir = dist_dir.resolve()
    now = _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0).isoformat()
    dist_infos = sorted(dist_dir.rglob("*.dist-info"))
    packages = [read_metadata(path) for path in dist_infos]
    packages.sort(key=lambda item: (item["name"].lower(), item["version"].lower(), rel(item["path"], dist_dir)))

    files = [path for path in dist_dir.rglob("*") if path.is_file()]
    native_files = [path for path in files if path.suffix.lower() in NATIVE_SUFFIXES]
    forbidden_models = [path for path in files if path.suffix.lower() in FORBIDDEN_MODEL_SUFFIXES]
    dev_only_status = [(name, (dist_dir / name).exists()) for name in DEV_ONLY_PATHS]
    required_status = [(name, (dist_dir / name).exists()) for name in REQUIRED_RELEASE_FILES]
    total_bytes = sum(path.stat().st_size for path in files)

    lines: list[str] = [
        "# Windows Bundle Manifest",
        "",
        f"Generated: {now}",
        f"Dist directory: `{dist_dir}`",
        "",
        "This manifest is generated from the PyInstaller `dist/DeepLiveCamStudio` payload. It is audit evidence, not a legal opinion.",
        "",
        "## Summary",
        "",
        f"- Files scanned: {len(files)}",
        f"- Total payload bytes: {total_bytes}",
        f"- Python package metadata directories: {len(packages)}",
        f"- Native/binary files: {len(native_files)}",
        f"- Forbidden model/checkpoint files found: {len(forbidden_models)}",
        f"- Dev-only sample/test payload paths found: {sum(1 for _, present in dev_only_status if present)}",
        "",
        "## Required Release Files",
        "",
    ]

    for name, present in required_status:
        lines.append(f"- [{'x' if present else ' '}] `{name}`")

    lines.extend(["", "## Python Package Metadata", ""])
    lines.append("| Package | Version | License Metadata | Metadata Path |")
    lines.append("| --- | --- | --- | --- |")
    for package in packages:
        lines.append(
            "| {name} | {version} | {license} | `{path}` |".format(
                name=package["name"].replace("|", "\\|"),
                version=package["version"].replace("|", "\\|"),
                license=package["license"].replace("|", "\\|"),
                path=rel(package["path"], dist_dir),
            )
        )

    lines.extend(["", "## Native/Binary File Summary", ""])
    lines.append("| Payload Area | File Count | Bytes |")
    lines.append("| --- | ---: | ---: |")
    for bucket, count, size in native_summary(native_files, dist_dir):
        lines.append(f"| `{bucket}` | {count} | {size} |")

    lines.extend(["", "## Forbidden Model/Checkpoint Scan", ""])
    if forbidden_models:
        for path in sorted(forbidden_models):
            lines.append(f"- `{rel(path, dist_dir)}`")
    else:
        lines.append("No `.onnx`, `.pth`, or `.safetensors` files were found in the payload.")

    lines.extend(["", "## Dev-Only Sample/Test Payload Scan", ""])
    for name, present in dev_only_status:
        lines.append(f"- [{' ' if present else 'x'}] `{name}`")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This manifest only reflects files present in the generated Windows payload.",
            "- Review `THIRD_PARTY_NOTICES.md`, `COMPLIANCE.md`, and dependency metadata before publishing.",
            "- Model files are intentionally excluded from the installer and downloaded only after user consent.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Windows PyInstaller payload manifest.")
    parser.add_argument("--dist", default="dist/DeepLiveCamStudio", help="PyInstaller dist directory to scan.")
    parser.add_argument("--output", default="LICENSES/WINDOWS_BUNDLE_MANIFEST.md", help="Manifest output path.")
    args = parser.parse_args()

    dist_dir = Path(args.dist)
    if not dist_dir.exists():
        raise SystemExit(f"Dist directory not found: {dist_dir}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate(dist_dir), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
