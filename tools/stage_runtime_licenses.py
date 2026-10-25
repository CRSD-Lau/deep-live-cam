"""Stage current-profile notices without inheriting historical build inventories."""

from __future__ import annotations

import argparse
import re
import shutil
import tempfile
from pathlib import Path


def stage(source: Path, dist: Path, profile: str) -> None:
    source = source.resolve()
    dist = dist.resolve()
    destination = dist / "LICENSES"
    if (not dist.is_dir() or destination == source
            or destination.resolve() != destination or destination.is_symlink()):
        raise ValueError("Licence destination must be a generated runtime directory")
    manifest = source / "THIRD_PARTY_LICENSES" / "README.md"
    text = manifest.read_text(encoding="utf-8")
    packages = re.findall(r"(?m)^- `([A-Za-z0-9_.-]+)` `([A-Za-z0-9_.+-]+)`$", text)
    names = {name.lower().replace("_", "-") for name, _ in packages}
    runtime = "onnxruntime-directml" if profile == "DirectML" else "onnxruntime-gpu"
    other_runtime = "onnxruntime-gpu" if profile == "DirectML" else "onnxruntime-directml"
    if runtime not in names or other_runtime in names or (profile == "DirectML" and "torch" in names):
        raise ValueError("Collected notices do not match the requested runtime profile")
    if not {"pillow", "certifi", "filelock", "setuptools"} <= names:
        raise ValueError("Collected notices omit security-updated dependencies")
    active = "PYTHON_DEPENDENCIES_DIRECTML.md" if profile == "DirectML" else "PYTHON_DEPENDENCIES.md"
    inactive = "PYTHON_DEPENDENCIES.md" if profile == "DirectML" else "PYTHON_DEPENDENCIES_DIRECTML.md"
    other_profile = "CUDA" if profile == "DirectML" else "DirectML"
    staging = Path(tempfile.mkdtemp(prefix=".licenses-", dir=dist))
    try:
        for path in source.glob("*.md"):
            if path.name not in {inactive, "WINDOWS_BUNDLE_MANIFEST.md"}:
                shutil.copy2(path, staging / path.name)
        if not (staging / active).is_file():
            raise ValueError("Active runtime inventory is missing")
        (staging / inactive).write_text(
            "---\nauthor: Neil Mitchell\ncreator: Neil Mitchell\nlast_modified_by: Neil Mitchell\n---\n\n"
            f"# {other_profile} Dependency Inventory\n\n"
            f"Not applicable to this {profile} runtime.\n\n"
            f"The current inventory for this runtime is [{active}]({active}). "
            f"The {other_profile} inventory is supplied with the separate {other_profile} package.\n",
            encoding="utf-8",
        )
        notices = staging / "THIRD_PARTY_LICENSES"
        notices.mkdir()
        shutil.copy2(manifest, notices / "README.md")
        for name, version in packages:
            directory = f"{name}-{version}".replace("+", "_")
            package_source = source / "THIRD_PARTY_LICENSES" / directory
            if not package_source.resolve().is_relative_to(source) or not package_source.is_dir():
                raise ValueError(f"Collected notice directory missing or unsafe: {directory}")
            shutil.copytree(package_source, notices / directory)
        # LICENSES is generated inside the named runtime only. Replace rather
        # than overlay so an earlier PyInstaller data copy cannot retain notices.
        if destination.exists():
            shutil.rmtree(destination)
        staging.replace(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("LICENSES"))
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("Cuda", "DirectML"), required=True)
    args = parser.parse_args()
    stage(args.source, args.dist, args.profile)


if __name__ == "__main__":
    main()
