#!/usr/bin/env python3
"""Diagnose ONNX Runtime CUDA provider availability."""

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
        "--strict",
        action="store_true",
        help="exit non-zero when a requested provider is unavailable",
    )
    return parser.parse_args()


def load_provider_helpers():
    module_path = os.path.join(PROJECT_ROOT, "modules", "execution_providers.py")
    spec = importlib.util.spec_from_file_location("dlc_execution_providers", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load provider resolver from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.resolve_execution_providers, module.build_provider_config


def main() -> int:
    args = parse_args()

    dll_dirs = register_windows_cuda_dll_dirs()
    for directory in dll_dirs:
        print(f"[check-cuda] Registered CUDA DLL directory: {directory}")

    try:
        import onnxruntime
    except ImportError:
        print("onnxruntime is not installed. Run: pip install -r requirements.txt")
        return 1

    resolve_execution_providers, build_provider_config = load_provider_helpers()

    available = list(onnxruntime.get_available_providers())
    resolved = resolve_execution_providers(
        args.execution_provider,
        available=available,
        logger=lambda message: print(f"[check-cuda] {message}"),
    )

    print(f"[check-cuda] onnxruntime version: {onnxruntime.__version__}")
    print(f"[check-cuda] active resolution: {resolved}")

    try:
        import torch

        print(f"[check-cuda] torch version: {torch.__version__}")
        print(f"[check-cuda] torch.cuda.is_available(): {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"[check-cuda] CUDA device: {torch.cuda.get_device_name(0)}")
    except Exception as exc:
        print(f"[check-cuda] torch CUDA check skipped: {exc}")

    requested_cuda = any(
        provider.lower().replace("executionprovider", "") == "cuda"
        for provider in args.execution_provider
    )
    cuda_active = "CUDAExecutionProvider" in resolved
    if requested_cuda and not cuda_active:
        print(
            "[check-cuda] CUDAExecutionProvider is not active. Install a CUDA-capable "
            "onnxruntime-gpu build and confirm NVIDIA CUDA/cuDNN DLLs are on PATH. "
            "Deep-Live-Cam will use CPUExecutionProvider fallback until CUDA loads."
        )
        return 2 if args.strict else 0

    probe_providers = []
    if resolved:
        try:
            probe_providers = create_probe_session(
                onnxruntime,
                build_provider_config(resolved),
            )
            print(f"[check-cuda] ONNX probe session providers: {probe_providers}")
        except Exception as exc:
            print(f"[check-cuda] ONNX probe session failed: {exc}")
            if args.strict:
                return 3

    if requested_cuda and "CUDAExecutionProvider" in resolved and "CUDAExecutionProvider" not in probe_providers:
        print(
            "[check-cuda] CUDAExecutionProvider is advertised by ONNX Runtime but "
            "did not load for an actual session. On Windows this usually means "
            "CUDA/cuDNN DLLs are missing from PATH. Install CUDA-enabled PyTorch "
            "with: pip install -U torch torchvision torchaudio --index-url "
            "https://download.pytorch.org/whl/cu128"
        )
        return 4 if args.strict else 0

    print("[check-cuda] Provider check complete.")
    return 0


def create_probe_session(onnxruntime, providers: list[str]) -> list[str]:
    import numpy as np
    import onnx
    from onnx import TensorProto, helper

    input_tensor = helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 1])
    output_tensor = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 1])
    node = helper.make_node("Identity", ["input"], ["output"])
    graph = helper.make_graph([node], "cuda_provider_probe", [input_tensor], [output_tensor])
    model = helper.make_model(
        graph,
        producer_name="deep-live-cam-check-cuda",
        opset_imports=[helper.make_operatorsetid("", 13)],
    )
    model.ir_version = min(model.ir_version, 10)

    session = onnxruntime.InferenceSession(
        model.SerializeToString(),
        providers=providers,
    )
    session.run(["output"], {"input": np.array([[1.0]], dtype=np.float32)})
    return list(session.get_providers())


if __name__ == "__main__":
    raise SystemExit(main())
