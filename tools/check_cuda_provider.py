#!/usr/bin/env python3
"""Diagnose ONNX Runtime execution-provider availability with real inference."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def register_windows_cuda_dll_dirs() -> list[str]:
    """Expose CUDA DLLs shipped by PyTorch/NVIDIA wheels to ONNX Runtime."""
    if sys.platform != "win32":
        return []

    registered: list[str] = []
    site_packages_candidates = [
        os.path.join(sys.prefix, "Lib", "site-packages"),
        os.path.join(PROJECT_ROOT, "venv", "Lib", "site-packages"),
    ]

    for site_packages in site_packages_candidates:
        candidate_dirs: list[str] = []
        torch_lib = os.path.join(site_packages, "torch", "lib")
        if os.path.isdir(torch_lib):
            candidate_dirs.append(torch_lib)

        nvidia_dir = os.path.join(site_packages, "nvidia")
        if os.path.isdir(nvidia_dir):
            for package_name in os.listdir(nvidia_dir):
                bin_dir = os.path.join(nvidia_dir, package_name, "bin")
                if os.path.isdir(bin_dir):
                    candidate_dirs.append(bin_dir)

        for directory in candidate_dirs:
            if directory in registered:
                continue
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(directory)
            except (AttributeError, OSError):
                pass
            registered.append(directory)

    return registered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execution-provider",
        nargs="+",
        default=["cuda"],
        metavar="PROVIDER",
        help="provider alias to check, for example cuda, directml, openvino, cpu",
    )
    parser.add_argument(
        "--directml-device-id",
        type=non_negative_int,
        default=0,
        help="DirectML adapter index (0 is the Windows default GPU)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when a requested provider is unavailable or falls back",
    )
    return parser.parse_args()


def non_negative_int(value: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value} is not an integer") from exc
    if result < 0:
        raise argparse.ArgumentTypeError("value must be 0 or greater")
    return result


def load_provider_helpers():
    module_path = os.path.join(PROJECT_ROOT, "modules", "execution_providers.py")
    spec = importlib.util.spec_from_file_location("dlc_execution_providers", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load provider resolver from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _requests_cuda(requested: list[str]) -> bool:
    return any(
        provider.lower().replace("_", "").replace("-", "").replace(
            "executionprovider", ""
        )
        == "cuda"
        for provider in requested
    )


def _install_hint(missing: list[str]) -> str:
    if "DmlExecutionProvider" in missing:
        return (
            "Install the DirectML runtime profile with tools\\setup_directml.ps1 "
            "or pip install -r requirements-directml.txt."
        )
    if "CUDAExecutionProvider" in missing:
        return (
            "Install a CUDA-capable onnxruntime-gpu build and confirm NVIDIA "
            "CUDA/cuDNN DLLs are available."
        )
    return "Install an ONNX Runtime build that contains the requested provider."


def main() -> int:
    args = parse_args()
    prefix = "[check-provider]"

    if _requests_cuda(args.execution_provider):
        for directory in register_windows_cuda_dll_dirs():
            print(f"{prefix} Registered CUDA DLL directory: {directory}")

    try:
        import onnxruntime
    except ImportError:
        print("onnxruntime is not installed. Run: pip install -r requirements.txt")
        return 1

    helpers = load_provider_helpers()
    available = list(onnxruntime.get_available_providers())
    resolved = helpers.resolve_execution_providers(
        args.execution_provider,
        available=available,
        logger=lambda message: print(f"{prefix} {message}"),
    )
    configured = helpers.build_provider_config(
        resolved,
        directml_device_id=args.directml_device_id,
    )

    print(f"{prefix} onnxruntime version: {onnxruntime.__version__}")
    print(f"{prefix} configured providers: {helpers.format_provider_config_summary(configured)}")

    missing_from_resolution = helpers.missing_requested_providers(
        args.execution_provider,
        resolved,
    )
    if missing_from_resolution:
        print(
            f"{prefix} Requested provider(s) unavailable: "
            f"{', '.join(missing_from_resolution)}. {_install_hint(missing_from_resolution)}"
        )
        if args.strict:
            return 2

    if _requests_cuda(args.execution_provider):
        try:
            import torch

            print(f"{prefix} torch version: {torch.__version__}")
            print(f"{prefix} torch.cuda.is_available(): {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                print(f"{prefix} CUDA device: {torch.cuda.get_device_name(0)}")
        except Exception as exc:
            print(f"{prefix} torch CUDA check skipped: {exc}")

    try:
        active = helpers.probe_execution_providers(configured)
        print(f"{prefix} ONNX probe session providers: {active}")
    except Exception as exc:
        print(f"{prefix} ONNX probe session failed: {exc}")
        return 3 if args.strict else 0

    missing_from_session = helpers.missing_requested_providers(
        args.execution_provider,
        active,
    )
    if missing_from_session:
        print(
            f"{prefix} Requested provider(s) fell back during real inference: "
            f"{', '.join(missing_from_session)}. {_install_hint(missing_from_session)}"
        )
        return 4 if args.strict else 0

    print(f"{prefix} Provider check complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
