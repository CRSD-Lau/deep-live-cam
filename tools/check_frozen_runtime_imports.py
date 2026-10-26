"""Reject build-only package managers and Torch code in both frozen executables."""

from __future__ import annotations

import argparse
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader


FORBIDDEN_PACKAGES = ("pip", "torch", "torchvision", "torchaudio")


def check(dist: Path, reader_type=CArchiveReader) -> list[str]:
    failures = []
    for package in FORBIDDEN_PACKAGES:
        if (dist / "_internal" / package).exists():
            failures.append(f"External runtime contains forbidden package: {package}")
    for filename in ("DeepLiveCamStudio.exe", "DeepLiveCamStudioCLI.exe"):
        archive = reader_type(str(dist / filename))
        pyz = archive.open_embedded_archive("PYZ.pyz")
        for module in pyz.toc:
            if any(module == package or module.startswith(package + ".") for package in FORBIDDEN_PACKAGES):
                failures.append(f"{filename} embeds forbidden module: {module}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", required=True, type=Path)
    args = parser.parse_args()
    failures = check(args.dist)
    for failure in failures:
        print(failure)
    if failures:
        return 1
    print("Both executable archives exclude pip and Torch Python packages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
