import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


def load_execution_providers(monkeypatch, available):
    class FakeSessionOptions:
        enable_mem_pattern = True
        execution_mode = None
        graph_optimization_level = None

    fake_ort = SimpleNamespace(
        get_available_providers=lambda: list(available),
        SessionOptions=FakeSessionOptions,
        GraphOptimizationLevel=SimpleNamespace(ORT_ENABLE_ALL="all"),
        ExecutionMode=SimpleNamespace(ORT_SEQUENTIAL="sequential"),
    )
    monkeypatch.setitem(sys.modules, "onnxruntime", fake_ort)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "modules"
        / "execution_providers.py"
    )
    spec = importlib.util.spec_from_file_location(
        "dlc_test_execution_providers", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cuda_request_keeps_cpu_fallback(monkeypatch):
    providers = load_execution_providers(
        monkeypatch,
        ["CUDAExecutionProvider", "CPUExecutionProvider"],
    )

    resolved = providers.resolve_execution_providers(["cuda"], logger=None)

    assert resolved == ["CUDAExecutionProvider", "CPUExecutionProvider"]


def test_unavailable_cuda_falls_back_to_cpu_and_logs(monkeypatch):
    providers = load_execution_providers(monkeypatch, ["CPUExecutionProvider"])
    messages = []

    resolved = providers.resolve_execution_providers(
        ["cuda"],
        logger=messages.append,
    )

    assert resolved == ["CPUExecutionProvider"]
    assert any("CUDAExecutionProvider is not available" in msg for msg in messages)


def test_directml_alias_resolves_dml_provider(monkeypatch):
    providers = load_execution_providers(
        monkeypatch,
        ["DmlExecutionProvider", "CPUExecutionProvider"],
    )

    resolved = providers.resolve_execution_providers(["directml"], logger=None)

    assert resolved == ["DmlExecutionProvider", "CPUExecutionProvider"]


def test_directml_config_selects_windows_adapter(monkeypatch):
    providers = load_execution_providers(
        monkeypatch,
        ["DmlExecutionProvider", "CPUExecutionProvider"],
    )

    config = providers.build_provider_config(
        ["DmlExecutionProvider", "CPUExecutionProvider"],
        directml_device_id=1,
    )

    assert config == [
        ("DmlExecutionProvider", {"device_id": "1"}),
        "CPUExecutionProvider",
    ]


def test_directml_session_options_disable_unsupported_modes(monkeypatch):
    providers = load_execution_providers(
        monkeypatch,
        ["DmlExecutionProvider", "CPUExecutionProvider"],
    )

    options = providers.build_session_options(["DmlExecutionProvider"])

    assert options.enable_mem_pattern is False
    assert options.execution_mode == "sequential"
    assert options.graph_optimization_level == "all"


def test_missing_requested_provider_detects_cpu_fallback(monkeypatch):
    providers = load_execution_providers(monkeypatch, ["CPUExecutionProvider"])

    missing = providers.missing_requested_providers(
        ["directml"],
        ["CPUExecutionProvider"],
    )

    assert missing == ["DmlExecutionProvider"]


def test_missing_requested_provider_rejects_unknown_alias(monkeypatch):
    providers = load_execution_providers(monkeypatch, ["CPUExecutionProvider"])

    missing = providers.missing_requested_providers(
        ["not-a-provider"],
        ["CPUExecutionProvider"],
    )

    assert missing == ["not-a-provider"]


def test_tensorrt_request_adds_cuda_and_cpu_fallbacks(monkeypatch):
    providers = load_execution_providers(
        monkeypatch,
        [
            "TensorrtExecutionProvider",
            "CUDAExecutionProvider",
            "CPUExecutionProvider",
        ],
    )
    messages = []

    resolved = providers.resolve_execution_providers(
        ["tensorrt"],
        logger=messages.append,
    )

    assert resolved == [
        "TensorrtExecutionProvider",
        "CUDAExecutionProvider",
        "CPUExecutionProvider",
    ]
    assert any("TensorRT fallback" in msg for msg in messages)


def test_build_provider_config_adds_tensorrt_cache_and_fp16_options(
    monkeypatch,
    tmp_path,
):
    providers = load_execution_providers(monkeypatch, ["CPUExecutionProvider"])
    cache_dir = tmp_path / "trt-cache"

    config = providers.build_provider_config(
        ["TensorrtExecutionProvider", "CUDAExecutionProvider"],
        tensorrt_cache_path=cache_dir,
    )

    assert config[0][0] == "TensorrtExecutionProvider"
    assert config[0][1]["trt_fp16_enable"] == "1"
    assert config[0][1]["trt_engine_cache_enable"] == "1"
    assert config[0][1]["trt_engine_cache_path"] == str(cache_dir)
    assert config[0][1]["trt_timing_cache_path"] == str(cache_dir)
    assert cache_dir.exists()
    assert config[1] == "CUDAExecutionProvider"


def test_provider_config_summary_is_json_safe_for_configured_options(
    monkeypatch,
    tmp_path,
):
    providers = load_execution_providers(monkeypatch, ["CPUExecutionProvider"])
    cache_dir = tmp_path / "trt-cache"
    config = providers.build_provider_config(
        ["TensorrtExecutionProvider", "CUDAExecutionProvider"],
        tensorrt_cache_path=cache_dir,
    )

    summary = providers.provider_config_summary(config)
    formatted = providers.format_provider_config_summary(config)

    assert summary[0]["name"] == "TensorrtExecutionProvider"
    assert summary[0]["options"]["trt_fp16_enable"] == "1"
    assert summary[0]["options"]["trt_engine_cache_path"] == str(cache_dir)
    assert summary[1] == {"name": "CUDAExecutionProvider", "options": {}}
    assert "TensorrtExecutionProvider(" in formatted
    assert "trt_fp16_enable=1" in formatted
    assert "CUDAExecutionProvider" in formatted


def test_build_provider_config_can_enable_cuda_graph(monkeypatch):
    providers = load_execution_providers(monkeypatch, ["CPUExecutionProvider"])

    config = providers.build_provider_config(
        ["CUDAExecutionProvider"],
        enable_cuda_graph=True,
    )

    assert config == [("CUDAExecutionProvider", {"enable_cuda_graph": "1"})]


def test_build_provider_config_preserves_preconfigured_tuples(monkeypatch):
    providers = load_execution_providers(monkeypatch, ["CPUExecutionProvider"])
    configured = ("CUDAExecutionProvider", {"device_id": "0"})

    config = providers.build_provider_config([configured])

    assert config == [configured]


def test_build_provider_config_adds_coreml_options_on_apple_silicon(monkeypatch):
    providers = load_execution_providers(monkeypatch, ["CPUExecutionProvider"])

    config = providers.build_provider_config(
        ["CoreMLExecutionProvider"],
        is_apple_silicon=True,
    )

    assert config[0][0] == "CoreMLExecutionProvider"
    assert config[0][1]["ModelFormat"] == "MLProgram"
    assert config[0][1]["MLComputeUnits"] == "ALL"
