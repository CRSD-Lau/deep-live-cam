"""Explicit model download and verification helpers."""

from __future__ import annotations

import hashlib
import os
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from tqdm import tqdm

from modules.paths import MODELS_DIR


@dataclass(frozen=True)
class ModelSpec:
    file_name: str
    url: str
    sha256: str
    source: str
    license_note: str
    required: bool = False


MODEL_SPECS: tuple[ModelSpec, ...] = (
    ModelSpec(
        file_name="inswapper_128.onnx",
        url="https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128.onnx",
        sha256="e4a3f08c753cb72d04e10aa0f7dbe3deebbf39567d4ead6dce08e98aa49e16af",
        source="hacksider/deep-live-cam on Hugging Face",
        license_note="GPL-3.0 is declared on the Hugging Face repository; InsightFace model use may carry non-commercial research restrictions.",
        required=True,
    ),
    ModelSpec(
        file_name="inswapper_128_fp16.onnx",
        url="https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx",
        sha256="6d51a9278a1f650cffefc18ba53f38bf2769bf4bbff89267822cf72945f8a38b",
        source="hacksider/deep-live-cam on Hugging Face",
        license_note="GPL-3.0 is declared on the Hugging Face repository; InsightFace model use may carry non-commercial research restrictions.",
    ),
    ModelSpec(
        file_name="GPEN-BFR-256.onnx",
        url="https://huggingface.co/netrunner-exe/Face-Upscalers-onnx/resolve/main/GPEN-BFR-256.onnx",
        sha256="aa5bd3ab238640a378c59e4a560f7a7150627944cf2129e6311ae4720e833271",
        source="netrunner-exe/Face-Upscalers-onnx on Hugging Face",
        license_note="No OSI license is declared; repository card states non-commercial, academic, and educational use only.",
    ),
    ModelSpec(
        file_name="GPEN-BFR-512.onnx",
        url="https://huggingface.co/netrunner-exe/Face-Upscalers-onnx/resolve/main/GPEN-BFR-512.onnx",
        sha256="0960f836488735444d508b588e44fb5dfd19c68fde9163ad7878aa24d1d5115e",
        source="netrunner-exe/Face-Upscalers-onnx on Hugging Face",
        license_note="No OSI license is declared; repository card states non-commercial, academic, and educational use only.",
    ),
    ModelSpec(
        file_name="gfpgan-1024.onnx",
        url="https://huggingface.co/hacksider/deep-live-cam/resolve/main/gfpgan-1024.onnx",
        sha256="ee8dd6415e388b3a410689d5d9395a2bf50b5973b588421ebfa57bc266f19e24",
        source="hacksider/deep-live-cam on Hugging Face; derived from TencentARC/GFPGAN",
        license_note="Hugging Face mirror declares GPL-3.0; upstream GFPGAN is Apache-2.0, but the exact ONNX conversion provenance should be rechecked before redistribution.",
    ),
)


def model_directory() -> Path:
    path = Path(MODELS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def spec_by_name(file_name: str) -> ModelSpec | None:
    return next((spec for spec in MODEL_SPECS if spec.file_name == file_name), None)


def local_model_path(file_name: str) -> Path:
    return model_directory() / file_name


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_model(path: Path, spec: ModelSpec) -> bool:
    return path.exists() and hash_file(path).lower() == spec.sha256.lower()


def missing_models(required_only: bool = False) -> list[ModelSpec]:
    specs = [spec for spec in MODEL_SPECS if spec.required or not required_only]
    return [spec for spec in specs if not verify_model(local_model_path(spec.file_name), spec)]


def print_model_notice(specs: Iterable[ModelSpec]) -> None:
    print("Model download notice")
    print("=====================")
    print(f"Models will be stored in: {model_directory()}")
    print("The Windows installer does not bundle model/checkpoint files.")
    print("Review each model source and license before downloading:")
    for spec in specs:
        print(f"- {spec.file_name}")
        print(f"  Source: {spec.source}")
        print(f"  URL: {spec.url}")
        print(f"  SHA256: {spec.sha256}")
        print(f"  License note: {spec.license_note}")


def confirm_download() -> bool:
    if not sys.stdin.isatty():
        return False
    try:
        answer = input("Download these models now? [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def download_models(assume_yes: bool = False, required_only: bool = False) -> int:
    specs = missing_models(required_only=required_only)
    if not specs:
        print(f"All selected models are present and verified in {model_directory()}.")
        return 0

    print_model_notice(specs)
    if not assume_yes and not confirm_download():
        print("Download cancelled. No model files were installed.")
        return 2

    for spec in specs:
        destination = local_model_path(spec.file_name)
        temporary = destination.with_suffix(destination.suffix + ".download")
        _download_file(spec.url, temporary)
        actual = hash_file(temporary)
        if actual.lower() != spec.sha256.lower():
            temporary.unlink(missing_ok=True)
            print(
                f"Checksum mismatch for {spec.file_name}. "
                f"Expected {spec.sha256}, got {actual}."
            )
            return 1
        os.replace(temporary, destination)
        print(f"Verified {destination}")
    return 0


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "DeepLiveCamStudio/installer"})
    with urllib.request.urlopen(request) as response:
        total = int(response.headers.get("Content-Length", 0))
        with tqdm(total=total, desc=destination.name, unit="B", unit_scale=True, unit_divisor=1024) as progress:
            with destination.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    progress.update(len(chunk))
