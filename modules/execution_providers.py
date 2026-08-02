"""ONNX Runtime execution provider selection and diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, List, Sequence

import onnxruntime
from modules.paths import RUNTIME_DIR

PROVIDER_ALIASES = {
    "cpu": "CPUExecutionProvider",
    "cuda": "CUDAExecutionProvider",
    "tensorrt": "TensorrtExecutionProvider",
    "rocm": "ROCMExecutionProvider",
    "coreml": "CoreMLExecutionProvider",
    "dml": "DmlExecutionProvider",
    "directml": "DmlExecutionProvider",
    "openvino": "OpenVINOExecutionProvider",
}

PREFERRED_PROVIDER_ALIASES = (
    "cuda",
    "rocm",
    "coreml",
    "dml",
    "openvino",
    "cpu",
)


def available_providers() -> List[str]:
    return list(onnxruntime.get_available_providers())


def provider_name(provider) -> str:
    return provider[0] if isinstance(provider, tuple) else str(provider)


def provider_names(providers: Iterable) -> List[str]:
    return [provider_name(provider) for provider in providers]


def provider_config_summary(providers: Iterable) -> List[dict[str, Any]]:
    """Return JSON-safe provider names and options for diagnostics."""
    summary: List[dict[str, Any]] = []
    for provider in providers:
        if isinstance(provider, tuple):
            name = str(provider[0])
            raw_options = provider[1] if len(provider) > 1 else {}
            options = _json_safe_options(raw_options)
        else:
            name = str(provider)
            options = {}
        summary.append({"name": name, "options": options})
    return summary


def format_provider_config_summary(providers: Iterable) -> str:
    """Format provider config options for readable logs."""
    parts: list[str] = []
    for item in provider_config_summary(providers):
        options = item["options"]
        if options:
            option_text = ", ".join(
                f"{key}={value}" for key, value in sorted(options.items())
            )
            parts.append(f"{item['name']}({option_text})")
        else:
            parts.append(str(item["name"]))
    return ", ".join(parts)


def build_provider_config(
    providers: Iterable,
    *,
    is_apple_silicon: bool = False,
    directml_device_id: int | None = None,
    tensorrt_cache_path: str | Path | None = None,
    enable_tensorrt_cache: bool = True,
    enable_tensorrt_fp16: bool = True,
    enable_cuda_graph: bool = False,
) -> List:
    """Build ONNX Runtime provider configs with reusable accelerator options."""
    config: List = []
    for provider in providers:
        if isinstance(provider, tuple):
            config.append(provider)
            continue

        if provider == "CoreMLExecutionProvider" and is_apple_silicon:
            config.append(
                (
                    "CoreMLExecutionProvider",
                    {
                        "ModelFormat": "MLProgram",
                        "MLComputeUnits": "ALL",
                        "SpecializationStrategy": "FastPrediction",
                        "AllowLowPrecisionAccumulationOnGPU": 1,
                        "EnableOnSubgraphs": 1,
                    },
                )
            )
        elif provider == "TensorrtExecutionProvider":
            config.append(
                (
                    "TensorrtExecutionProvider",
                    _tensorrt_provider_options(
                        cache_path=tensorrt_cache_path,
                        enable_cache=enable_tensorrt_cache,
                        enable_fp16=enable_tensorrt_fp16,
                    ),
                )
            )
        elif provider == "DmlExecutionProvider" and directml_device_id is not None:
            config.append(
                (
                    "DmlExecutionProvider",
                    {"device_id": str(directml_device_id)},
                )
            )
        elif provider == "CUDAExecutionProvider" and enable_cuda_graph:
            config.append(("CUDAExecutionProvider", {"enable_cuda_graph": "1"}))
        else:
            config.append(provider)
    return config


def encode_provider(provider: str) -> str:
    return provider.replace("ExecutionProvider", "").lower()


def encode_providers(providers: Iterable[str]) -> List[str]:
    return [encode_provider(provider) for provider in providers]


def normalize_provider_alias(value: str) -> str:
    normalized = value.strip().lower().replace("_", "").replace("-", "")
    if normalized.endswith("executionprovider"):
        normalized = normalized[: -len("executionprovider")]
    if normalized == "directml":
        return "directml"
    return normalized


def suggest_default_execution_provider() -> str:
    encoded_available = set(encode_providers(available_providers()))
    for alias in PREFERRED_PROVIDER_ALIASES:
        provider = PROVIDER_ALIASES[alias]
        if encode_provider(provider) in encoded_available:
            return alias
    return "cpu"


def supported_provider_aliases() -> List[str]:
    return sorted(PROVIDER_ALIASES)


def requested_provider_names(requested: Sequence[str] | None) -> List[str]:
    """Translate requested aliases into canonical ONNX Runtime provider names."""
    names: List[str] = []
    for raw in requested or []:
        alias = normalize_provider_alias(raw)
        provider = PROVIDER_ALIASES.get(alias, str(raw))
        if provider not in names:
            names.append(provider)
    return names


def missing_requested_providers(
    requested: Sequence[str] | None,
    active: Iterable,
) -> List[str]:
    """Return requested providers that did not remain active for a real session."""
    active_names = set(provider_names(active))
    return [
        provider
        for provider in requested_provider_names(requested)
        if provider not in active_names
    ]


def resolve_execution_providers(
    requested: Sequence[str] | None,
    *,
    available: Sequence[str] | None = None,
    include_cpu_fallback: bool = True,
    logger: Callable[[str], None] | None = None,
) -> List[str]:
    """Resolve user provider aliases to available ONNX Runtime providers.

    GPU provider requests stay valid even if the installed ONNX Runtime package
    cannot load that provider. In that case the resolver prints a readable
    message and falls back to CPU when CPUExecutionProvider is available.
    """
    available_list = list(available) if available is not None else available_providers()
    requested_list = list(requested or [suggest_default_execution_provider()])
    resolved: List[str] = []
    unavailable: List[str] = []
    unknown: List[str] = []

    available_by_encoded = {
        encode_provider(provider): provider for provider in available_list
    }

    for raw in requested_list:
        alias = normalize_provider_alias(raw)
        provider = PROVIDER_ALIASES.get(alias)
        if provider is None:
            # Accept exact provider names from advanced users if ORT reports them.
            provider = available_by_encoded.get(alias)
        if provider is None:
            unknown.append(raw)
            continue

        encoded = encode_provider(provider)
        if encoded in available_by_encoded:
            provider = available_by_encoded[encoded]
            if provider not in resolved:
                resolved.append(provider)
        else:
            unavailable.append(provider)

    cpu_provider = available_by_encoded.get("cpu")
    requested_non_cpu = any(
        normalize_provider_alias(value) != "cpu" for value in requested_list
    )
    should_add_cpu = (
        cpu_provider
        and cpu_provider not in resolved
        and (not resolved or (include_cpu_fallback and requested_non_cpu))
    )
    if should_add_cpu:
        resolved.append(cpu_provider)

    tensorrt_provider = available_by_encoded.get("tensorrt")
    cuda_provider = available_by_encoded.get("cuda")
    if (
        tensorrt_provider in resolved
        and cuda_provider
        and cuda_provider not in resolved
    ):
        insert_at = resolved.index(tensorrt_provider) + 1
        resolved.insert(insert_at, cuda_provider)

    if not resolved and available_list:
        resolved.append(available_list[0])

    if logger:
        logger(f"ONNX Runtime available providers: {available_list}")
        logger(f"Requested execution provider(s): {requested_list}")
        for provider in unavailable:
            logger(
                f"Requested provider {provider} is not available; "
                "falling back to the next available provider."
            )
        for provider in unknown:
            logger(
                f"Unknown execution provider '{provider}'. Supported aliases: "
                f"{', '.join(supported_provider_aliases())}."
            )
        if tensorrt_provider in resolved and cuda_provider in resolved:
            logger("CUDAExecutionProvider enabled as TensorRT fallback provider.")
        logger(f"Resolved execution provider(s): {resolved}")

    return resolved


def build_session_options(
    providers: Iterable,
    *,
    disable_cpu_fallback: bool = False,
):
    """Create session options that satisfy accelerator-specific requirements."""
    options = onnxruntime.SessionOptions()
    if hasattr(onnxruntime, "GraphOptimizationLevel"):
        options.graph_optimization_level = (
            onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
        )

    if "DmlExecutionProvider" in provider_names(providers):
        # DirectML does not support memory patterns or parallel session
        # execution. Make both constraints explicit instead of relying on
        # package defaults that may change between ONNX Runtime releases.
        options.enable_mem_pattern = False
        if hasattr(onnxruntime, "ExecutionMode"):
            options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
    if disable_cpu_fallback and hasattr(options, "add_session_config_entry"):
        options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    return options


def probe_execution_providers(providers: Iterable) -> List[str]:
    """Run a tiny real inference and return the providers that stayed active."""
    import numpy as np
    from onnx import TensorProto, helper

    provider_config = build_provider_config(providers)
    left_tensor = helper.make_tensor_value_info(
        "left", TensorProto.FLOAT, [64, 64]
    )
    right_tensor = helper.make_tensor_value_info(
        "right", TensorProto.FLOAT, [64, 64]
    )
    output_tensor = helper.make_tensor_value_info(
        "output", TensorProto.FLOAT, [64, 64]
    )
    node = helper.make_node("MatMul", ["left", "right"], ["output"])
    graph = helper.make_graph(
        [node],
        "execution_provider_probe",
        [left_tensor, right_tensor],
        [output_tensor],
    )
    model = helper.make_model(
        graph,
        producer_name="deep-live-cam-provider-check",
        opset_imports=[helper.make_operatorsetid("", 13)],
    )
    model.ir_version = min(model.ir_version, 10)

    accelerator_config = [
        provider
        for provider in provider_config
        if provider_name(provider) != "CPUExecutionProvider"
    ]
    require_accelerator = bool(accelerator_config)
    session = onnxruntime.InferenceSession(
        model.SerializeToString(),
        sess_options=build_session_options(
            provider_config,
            disable_cpu_fallback=require_accelerator,
        ),
        providers=accelerator_config or provider_config,
    )
    values = np.ones((64, 64), dtype=np.float32)
    result = session.run(
        ["output"],
        {"left": values, "right": values},
    )
    if not np.allclose(result[0], 64.0):
        raise RuntimeError("Execution provider probe returned an incorrect result.")
    return list(session.get_providers())


def _tensorrt_provider_options(
    *,
    cache_path: str | Path | None,
    enable_cache: bool,
    enable_fp16: bool,
) -> dict[str, str]:
    options: dict[str, str] = {}
    if enable_fp16:
        options["trt_fp16_enable"] = "1"
    if enable_cache:
        cache_dir = Path(cache_path or Path(RUNTIME_DIR) / "onnx_tensorrt_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_dir_str = str(cache_dir)
        options["trt_engine_cache_enable"] = "1"
        options["trt_engine_cache_path"] = cache_dir_str
        options["trt_timing_cache_enable"] = "1"
        options["trt_timing_cache_path"] = cache_dir_str
    return options


def _json_safe_options(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {"value": str(value)}
    return {str(key): str(item) for key, item in value.items()}
