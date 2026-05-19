#!/usr/bin/env python3
"""Remove known dev-only payload folders from the Windows PyInstaller dist."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PRUNE_PATHS = (
    "_internal/matplotlib/mpl-data/sample_data",
    "_internal/sklearn/datasets/data",
    "_internal/sklearn/datasets/images",
    "_internal/sklearn/datasets/tests",
)


def contained(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def prune(dist: Path) -> list[Path]:
    dist = dist.resolve()
    removed: list[Path] = []
    for relative in PRUNE_PATHS:
        target = dist / relative
        if not target.exists():
            continue
        if not contained(target, dist):
            raise RuntimeError(f"Refusing to remove path outside dist: {target}")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed.append(target)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune known dev-only files from a Windows PyInstaller dist.")
    parser.add_argument("--dist", default="dist/DeepLiveCamStudio", help="PyInstaller dist directory.")
    args = parser.parse_args()

    dist = Path(args.dist)
    if not dist.exists():
        raise SystemExit(f"Dist directory not found: {dist}")

    removed = prune(dist)
    if removed:
        print("Pruned dev-only payload paths:")
        for path in removed:
            print(f"- {path}")
    else:
        print("No dev-only payload paths needed pruning.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
