import copy
from collections.abc import Mapping
from typing import Any, List, Optional
import cv2
import insightface
import logging
import threading
import numpy as np
import platform
import modules.globals
import modules.processors.frame.core
from modules.compositing.color import (
    ColorMatchStatistics,
    LuminanceMatchStatistics,
    blend_color_match_statistics,
    blend_luminance_match_statistics,
    match_color_statistics,
    match_luminance_statistics,
)
from modules.compositing.masks import (
    FeatherSettings,
    create_aligned_face_alpha,
    create_expression_occlusion_mask,
    create_extended_subject_mask,
    create_landmark_face_mask,
    estimate_blur_amount,
    estimate_edge_contrast,
    get_adaptive_feather_settings,
    preserve_target_edges_in_alpha,
    refine_alpha_with_boundary_color_mismatch,
    refine_alpha_with_landmark_mask,
    refine_alpha_with_skin_chroma_mask,
)
from modules.core import update_status
from modules.diagnostics.overlays import draw_diagnostic_overlay
from modules.execution_providers import (
    build_provider_config,
    build_session_options,
    format_provider_config_summary,
    provider_names,
)
from modules.expression_regions import (
    MOUTH_OUTER_INDICES,
    compute_mouth_region_confidence,
)
from modules.expression_temporal import (
    collect_expression_snapshots,
    expression_temporal_weight,
)
from modules.expression_stabilizer import blend_expression_region_landmarks
from modules.face_pose import estimate_profile_score
from modules.face_analyser import get_one_face, get_many_faces, default_source_face
from modules.temporal_smoothing import blend_frame_regions
from modules.typing import Face, Frame
from modules.utilities import (
    is_image,
    is_video,
    read_image,
)
from modules.paths import MODELS_DIR
from modules.cluster_analysis import find_closest_centroid
from modules.gpu_processing import gpu_gaussian_blur, gpu_sharpen, gpu_add_weighted, gpu_resize
import os
from collections import deque
import time

FACE_SWAPPER = None
THREAD_LOCK = threading.Lock()
NAME = "DLC.FACE-SWAPPER"
_TORCH = None
_HAS_TORCH_CUDA: Optional[bool] = None

# --- START: Added for Interpolation ---
PREVIOUS_FRAME_RESULT = None # Stores the final processed frame from the previous step
PREVIOUS_EXPRESSION_SNAPSHOTS = {}
COMPOSITING_COLOR_STATISTICS = {
    "color": {},
    "luminance": {},
    "max_entries": 32,
}
COMPOSITING_ALPHA_MASKS = {
    "alpha": {},
    "max_entries": 32,
}
COMPOSITING_OCCLUSION_PRIORITY_MASKS = {
    "mask": {},
    "max_entries": 32,
}
MOUTH_MASK_GEOMETRY = {
    "landmarks": {},
    "max_entries": 32,
}
EXPRESSION_REGION_GEOMETRY = {
    "landmarks": {},
    "max_entries": 32,
}
# --- END: Added for Interpolation ---

# --- START: Mac M1-M5 Optimizations ---
IS_APPLE_SILICON = platform.system() == 'Darwin' and platform.machine() == 'arm64'
FRAME_CACHE = deque(maxlen=3)  # Cache for frame reuse
FACE_DETECTION_CACHE = {}  # Cache face detections
LAST_DETECTION_TIME = 0
DETECTION_INTERVAL = 0.033  # ~30 FPS detection rate for live mode
FRAME_SKIP_COUNTER = 0
ADAPTIVE_QUALITY = True
# --- END: Mac M1-M5 Optimizations ---

models_dir = MODELS_DIR

def pre_check() -> bool:
    try:
        os.makedirs(models_dir, exist_ok=True)
    except OSError as e:
        logging.error(f"Failed to create directory {models_dir} due to permission error: {e}")
        return False

    fp16_path = os.path.join(models_dir, "inswapper_128_fp16.onnx")
    fp32_path = os.path.join(models_dir, "inswapper_128.onnx")
    if not os.path.exists(fp16_path) and not os.path.exists(fp32_path):
        update_status(
            f"Required model not found in {models_dir}. "
            "Run DeepLiveCamStudioCLI.exe --download-models after reviewing model licenses.",
            NAME,
        )
        return False
    return True


def pre_start() -> bool:
    # Check for either model variant
    fp16_path = os.path.join(models_dir, "inswapper_128_fp16.onnx")
    fp32_path = os.path.join(models_dir, "inswapper_128.onnx")
    if not os.path.exists(fp16_path) and not os.path.exists(fp32_path):
        update_status(f"Model not found in {models_dir}. Please download inswapper_128.onnx.", NAME)
        return False

    # Try to get the face swapper to ensure it loads correctly
    if get_face_swapper() is None:
        # Error message already printed within get_face_swapper
        return False

    return True


def get_face_swapper() -> Any:
    global FACE_SWAPPER

    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            # Prefer FP16 on GPUs with Tensor Cores (Turing+) — half the
            # memory bandwidth, faster inference.  Fall back to FP32 for
            # older GPUs (e.g. GTX 16xx) where FP16 can produce NaN.
            fp32_path = os.path.join(models_dir, "inswapper_128.onnx")
            fp16_path = os.path.join(models_dir, "inswapper_128_fp16.onnx")
            use_fp16 = _has_torch_cuda() and os.path.exists(fp16_path)
            if use_fp16:
                model_path = fp16_path
            elif os.path.exists(fp32_path):
                model_path = fp32_path
            else:
                update_status(f"No inswapper model found in {models_dir}.", NAME)
                return None
            # On Apple Silicon, rewrite Pad(reflect) → Slice+Concat so
            # CoreML can run the entire model in a single partition on
            # the Neural Engine instead of bouncing between CPU and ANE.
            if IS_APPLE_SILICON:
                from modules.onnx_optimize import optimize_for_coreml
                model_path = optimize_for_coreml(model_path)

            update_status(f"Loading face swapper model from: {model_path}", NAME)
            try:
                providers_config = build_provider_config(
                    modules.globals.execution_providers,
                    is_apple_silicon=IS_APPLE_SILICON,
                    directml_device_id=getattr(
                        modules.globals, "directml_device_id", 0
                    ),
                )
                update_status(
                    f"Face swapper requested providers: "
                    f"{provider_names(providers_config)}",
                    NAME,
                )
                update_status(
                    f"Face swapper provider config: "
                    f"{format_provider_config_summary(providers_config)}",
                    NAME,
                )
                FACE_SWAPPER = insightface.model_zoo.get_model(
                    model_path,
                    providers=providers_config,
                    sess_options=build_session_options(providers_config),
                )
                try:
                    active_providers = FACE_SWAPPER.session.get_providers()
                    update_status(
                        f"Face swapper active providers: {active_providers}",
                        NAME,
                    )
                except Exception:
                    pass
                # Set up CUDA graph session for faster inference
                if _has_torch_cuda() and any(
                    p == "CUDAExecutionProvider" or
                    (isinstance(p, tuple) and p[0] == "CUDAExecutionProvider")
                    for p in providers_config
                ):
                    _init_cuda_graph_session(model_path, FACE_SWAPPER)
                update_status("Face swapper model loaded successfully.", NAME)
            except Exception as e:
                update_status(f"Error loading face swapper model: {e}", NAME)
                FACE_SWAPPER = None
                return None
    return FACE_SWAPPER


def _torch_module():
    global _TORCH
    if _TORCH is not None:
        return _TORCH
    try:
        import torch
    except Exception:
        return None
    _TORCH = torch
    return _TORCH


def _has_torch_cuda() -> bool:
    global _HAS_TORCH_CUDA
    if isinstance(_HAS_TORCH_CUDA, bool):
        return _HAS_TORCH_CUDA
    torch = _torch_module()
    if torch is None:
        _HAS_TORCH_CUDA = False
        return False
    try:
        _HAS_TORCH_CUDA = bool(torch.cuda.is_available())
    except Exception:
        _HAS_TORCH_CUDA = False
    return _HAS_TORCH_CUDA

# Cache for paste-back
_paste_cache = {
    'soft_alpha': {},  # keyed by aligned size and adaptive feather settings
    'max_alpha_entries': 16,
}


def _get_soft_alpha(size: int, settings: FeatherSettings) -> np.ndarray:
    """Feathered alpha template in aligned-face space, cached.

    Keeping the mask in aligned space lets us adapt the feather profile while
    preserving an O(crop_area) paste-back path.
    """
    key = settings.cache_key(size)
    cache = _paste_cache['soft_alpha']
    if key not in cache:
        if len(cache) >= _paste_cache['max_alpha_entries']:
            cache.pop(next(iter(cache)))
        cache[key] = create_aligned_face_alpha(size, settings)
    return cache[key]


def reset_compositing_temporal_state() -> None:
    """Clear per-track compositing temporal history."""
    _reset_compositing_color_temporal_state()
    _reset_compositing_alpha_temporal_state()
    _reset_occlusion_priority_temporal_state()
    _reset_mouth_mask_temporal_state()
    _reset_expression_region_temporal_state()


def _reset_compositing_color_temporal_state() -> None:
    COMPOSITING_COLOR_STATISTICS["color"].clear()
    COMPOSITING_COLOR_STATISTICS["luminance"].clear()


def _reset_compositing_alpha_temporal_state() -> None:
    COMPOSITING_ALPHA_MASKS["alpha"].clear()


def _reset_occlusion_priority_temporal_state() -> None:
    COMPOSITING_OCCLUSION_PRIORITY_MASKS["mask"].clear()


def _reset_mouth_mask_temporal_state() -> None:
    MOUTH_MASK_GEOMETRY["landmarks"].clear()


def _reset_expression_region_temporal_state() -> None:
    EXPRESSION_REGION_GEOMETRY["landmarks"].clear()


def _compositing_temporal_key(face: Face | Mapping | None) -> str | None:
    tracking_id = _face_value(face, "tracking_id", None)
    if tracking_id is None:
        return None
    try:
        return f"track:{int(tracking_id)}"
    except (TypeError, ValueError):
        return f"track:{tracking_id}"


def _compositing_temporal_strength() -> float:
    strength = getattr(
        modules.globals,
        "compositing_color_temporal_smoothing",
        0.0,
    )
    try:
        return float(np.clip(strength or 0.0, 0.0, 1.0))
    except (TypeError, ValueError):
        return 0.0


def _compositing_alpha_temporal_strength() -> float:
    strength = getattr(
        modules.globals,
        "compositing_alpha_temporal_smoothing",
        0.0,
    )
    try:
        return float(np.clip(strength or 0.0, 0.0, 1.0))
    except (TypeError, ValueError):
        return 0.0


def _motion_adjusted_compositing_temporal_strength(
    base_weight: float,
    face: Face | Mapping | None,
) -> float:
    weight = float(np.clip(base_weight, 0.0, 1.0))
    if weight <= 0.0:
        return 0.0
    if _tracking_should_reset_temporal_state(face):
        return 0.0

    reduction = float(
        np.clip(
            getattr(
                modules.globals,
                "compositing_color_temporal_motion_reduction",
                0.0,
            )
            or 0.0,
            0.0,
            1.0,
        )
    )
    if reduction <= 0.0:
        return weight

    motion = _tracking_motion_amount(face)
    low_threshold = max(
        0.0,
        float(
            getattr(
                modules.globals,
                "compositing_color_temporal_motion_threshold",
                0.08,
            )
            or 0.0
        ),
    )
    high_threshold = max(
        low_threshold,
        float(
            getattr(
                modules.globals,
                "compositing_color_temporal_high_motion_threshold",
                0.35,
            )
            or low_threshold
        ),
    )
    if motion <= low_threshold:
        return weight
    if motion >= high_threshold:
        amount = 1.0
    else:
        amount = (motion - low_threshold) / max(high_threshold - low_threshold, 1e-6)
    return float(np.clip(weight * (1.0 - reduction * amount), 0.0, 1.0))


def _motion_adjusted_compositing_alpha_temporal_strength(
    base_weight: float,
    face: Face | Mapping | None,
) -> float:
    weight = float(np.clip(base_weight, 0.0, 1.0))
    if weight <= 0.0:
        return 0.0
    if _tracking_should_reset_temporal_state(face):
        return 0.0

    reduction = float(
        np.clip(
            getattr(
                modules.globals,
                "compositing_alpha_temporal_motion_reduction",
                0.0,
            )
            or 0.0,
            0.0,
            1.0,
        )
    )
    if reduction <= 0.0:
        return weight

    motion = _tracking_motion_amount(face)
    low_threshold = max(
        0.0,
        float(
            getattr(
                modules.globals,
                "compositing_alpha_temporal_motion_threshold",
                0.08,
            )
            or 0.0
        ),
    )
    high_threshold = max(
        low_threshold,
        float(
            getattr(
                modules.globals,
                "compositing_alpha_temporal_high_motion_threshold",
                0.35,
            )
            or low_threshold
        ),
    )
    if motion <= low_threshold:
        return weight
    if motion >= high_threshold:
        amount = 1.0
    else:
        amount = (motion - low_threshold) / max(high_threshold - low_threshold, 1e-6)
    return float(np.clip(weight * (1.0 - reduction * amount), 0.0, 1.0))


def _remember_compositing_statistics(
    store: dict[str, ColorMatchStatistics | LuminanceMatchStatistics],
    key: str,
    value: ColorMatchStatistics | LuminanceMatchStatistics,
) -> None:
    max_entries = int(COMPOSITING_COLOR_STATISTICS.get("max_entries", 32))
    if key not in store and len(store) >= max_entries:
        store.pop(next(iter(store)))
    store[key] = value


def _remember_compositing_alpha(key: str, alpha: np.ndarray) -> None:
    store = COMPOSITING_ALPHA_MASKS["alpha"]
    max_entries = int(COMPOSITING_ALPHA_MASKS.get("max_entries", 32))
    if key not in store and len(store) >= max_entries:
        store.pop(next(iter(store)))
    store[key] = alpha.copy()


def _remember_occlusion_priority_mask(key: str, mask: np.ndarray) -> None:
    store = COMPOSITING_OCCLUSION_PRIORITY_MASKS["mask"]
    max_entries = int(COMPOSITING_OCCLUSION_PRIORITY_MASKS.get("max_entries", 32))
    if key not in store and len(store) >= max_entries:
        store.pop(next(iter(store)))
    store[key] = mask.copy()


def _occlusion_priority_temporal_strength(face: Face | Mapping | None) -> float:
    strength = float(
        getattr(
            modules.globals,
            "compositing_occlusion_region_temporal_smoothing",
            0.0,
        )
        or 0.0
    )
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0:
        return 0.0

    reduction = float(
        getattr(
            modules.globals,
            "compositing_occlusion_region_temporal_motion_reduction",
            0.0,
        )
        or 0.0
    )
    reduction = float(np.clip(reduction, 0.0, 1.0))
    if reduction <= 0.0:
        return strength

    motion = _tracking_motion_amount(face)
    return float(np.clip(strength * (1.0 - reduction * motion), 0.0, 1.0))


def _smooth_occlusion_priority_mask(
    priority_mask: np.ndarray | None,
    face: Face | Mapping | None,
) -> np.ndarray | None:
    if priority_mask is None:
        return None

    track_key = _compositing_temporal_key(face)
    strength = _occlusion_priority_temporal_strength(face)
    if track_key is None or strength <= 0.0:
        return priority_mask

    store = COMPOSITING_OCCLUSION_PRIORITY_MASKS["mask"]
    if _tracking_should_reset_temporal_state(face):
        store.pop(track_key, None)
        return priority_mask

    previous = store.get(track_key)
    if (
        previous is None
        or previous.shape != priority_mask.shape
        or previous.dtype != priority_mask.dtype
    ):
        _remember_occlusion_priority_mask(track_key, priority_mask)
        return priority_mask

    smoothed = cv2.addWeighted(previous, strength, priority_mask, 1.0 - strength, 0)
    _remember_occlusion_priority_mask(track_key, smoothed)
    return smoothed


def _remember_mouth_mask_landmarks(key: str, landmarks: np.ndarray) -> None:
    store = MOUTH_MASK_GEOMETRY["landmarks"]
    max_entries = int(MOUTH_MASK_GEOMETRY.get("max_entries", 32))
    if key not in store and len(store) >= max_entries:
        store.pop(next(iter(store)))
    store[key] = landmarks.astype(np.float32, copy=True)


def _mouth_mask_temporal_strength(face: Face | Mapping | None) -> float:
    strength = float(
        getattr(modules.globals, "mouth_mask_temporal_smoothing", 0.0) or 0.0
    )
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0:
        return 0.0

    reduction = float(
        getattr(modules.globals, "mouth_mask_temporal_motion_reduction", 0.0)
        or 0.0
    )
    reduction = float(np.clip(reduction, 0.0, 1.0))
    if reduction <= 0.0:
        return strength

    motion = _tracking_motion_amount(face)
    return float(np.clip(strength * (1.0 - reduction * motion), 0.0, 1.0))


def _smooth_mouth_mask_landmarks(
    face: Face | Mapping | None,
    landmarks: np.ndarray,
) -> np.ndarray:
    track_key = _compositing_temporal_key(face)
    strength = _mouth_mask_temporal_strength(face)
    if track_key is None or strength <= 0.0:
        return landmarks

    store = MOUTH_MASK_GEOMETRY["landmarks"]
    if _tracking_should_reset_temporal_state(face):
        store.pop(track_key, None)
        return landmarks

    previous = store.get(track_key)
    if (
        previous is None
        or previous.shape != landmarks.shape
        or not np.all(np.isfinite(previous))
    ):
        _remember_mouth_mask_landmarks(track_key, landmarks)
        return landmarks

    smoothed = previous * strength + landmarks.astype(np.float32) * (1.0 - strength)
    _remember_mouth_mask_landmarks(track_key, smoothed)
    return smoothed.astype(np.float32, copy=False)


def _remember_expression_region_landmarks(key: str, landmarks: np.ndarray) -> None:
    store = EXPRESSION_REGION_GEOMETRY["landmarks"]
    max_entries = int(EXPRESSION_REGION_GEOMETRY.get("max_entries", 32))
    if key not in store and len(store) >= max_entries:
        store.pop(next(iter(store)))
    store[key] = landmarks.astype(np.float32, copy=True)


def _expression_region_temporal_strength(face: Face | Mapping | None) -> float:
    strength = float(
        getattr(modules.globals, "expression_region_temporal_smoothing", 0.0)
        or 0.0
    )
    strength = float(np.clip(strength, 0.0, 1.0))
    if strength <= 0.0:
        return 0.0

    reduction = float(
        getattr(
            modules.globals,
            "expression_region_temporal_motion_reduction",
            0.0,
        )
        or 0.0
    )
    reduction = float(np.clip(reduction, 0.0, 1.0))
    if reduction <= 0.0:
        return strength

    motion = _tracking_motion_amount(face)
    return float(np.clip(strength * (1.0 - reduction * motion), 0.0, 1.0))


def _stabilized_expression_faces(
    faces: Optional[List[Face]] | None,
) -> Optional[List[Face | Mapping]]:
    if not faces:
        return faces
    return [_stabilized_expression_face(face) for face in faces]


def _stabilized_expression_face(face: Face | Mapping | None) -> Face | Mapping | None:
    track_key = _compositing_temporal_key(face)
    landmarks = _face_array(face, "landmark_2d_106")
    strength = _expression_region_temporal_strength(face)
    if track_key is None or landmarks is None or strength <= 0.0:
        return face

    store = EXPRESSION_REGION_GEOMETRY["landmarks"]
    if _tracking_should_reset_temporal_state(face):
        store.pop(track_key, None)
        return face

    previous = store.get(track_key)
    if (
        previous is None
        or previous.shape != landmarks.shape
        or not np.all(np.isfinite(previous))
    ):
        _remember_expression_region_landmarks(track_key, landmarks)
        return face

    smoothed = blend_expression_region_landmarks(
        previous,
        landmarks,
        history_weight=strength,
    )
    _remember_expression_region_landmarks(track_key, smoothed)
    return _copy_face_with_landmarks(face, smoothed)


def _copy_face_with_landmarks(
    face: Face | Mapping | None,
    landmarks: np.ndarray,
) -> Face | Mapping | None:
    if face is None:
        return None
    if isinstance(face, Mapping):
        cloned = dict(face)
        cloned["landmark_2d_106"] = landmarks.astype(np.float32, copy=True)
        return cloned

    try:
        cloned = copy.copy(face)
        setattr(cloned, "landmark_2d_106", landmarks.astype(np.float32, copy=True))
        return cloned
    except Exception:
        return face


def _smooth_compositing_alpha(
    alpha_crop: np.ndarray,
    track_key: str | None,
    history_weight: float,
) -> np.ndarray:
    weight = float(np.clip(history_weight, 0.0, 1.0))
    if track_key is None or weight <= 0.0:
        return alpha_crop

    store = COMPOSITING_ALPHA_MASKS["alpha"]
    previous = store.get(track_key)
    if (
        previous is None
        or previous.shape != alpha_crop.shape
        or previous.dtype != alpha_crop.dtype
    ):
        _remember_compositing_alpha(track_key, alpha_crop)
        return alpha_crop

    smoothed = cv2.addWeighted(previous, weight, alpha_crop, 1.0 - weight, 0)
    _remember_compositing_alpha(track_key, smoothed)
    return smoothed


def _color_statistics_transform(
    track_key: str | None,
    history_weight: float,
):
    if track_key is None or history_weight <= 0.0:
        return None

    def transform(current: ColorMatchStatistics) -> ColorMatchStatistics:
        store = COMPOSITING_COLOR_STATISTICS["color"]
        smoothed = blend_color_match_statistics(
            store.get(track_key),
            current,
            history_weight,
        )
        _remember_compositing_statistics(store, track_key, smoothed)
        return smoothed

    return transform


def _luminance_statistics_transform(
    track_key: str | None,
    history_weight: float,
):
    if track_key is None or history_weight <= 0.0:
        return None

    def transform(current: LuminanceMatchStatistics) -> LuminanceMatchStatistics:
        store = COMPOSITING_COLOR_STATISTICS["luminance"]
        smoothed = blend_luminance_match_statistics(
            store.get(track_key),
            current,
            history_weight,
        )
        _remember_compositing_statistics(store, track_key, smoothed)
        return smoothed

    return transform

# CUDA graph swap session cache
_cuda_graph_session = {
    'session': None,
    'io_binding': None,
    'ort_input': None,
    'ort_latent': None,
    'recorded': False,
}
# Serializes CUDA-graph replay. The io_binding + ort_input/ort_latent are
# shared across threads and run_with_iobinding mutates GPU-side buffers;
# concurrent calls would produce wrong output.
_cuda_graph_lock = threading.Lock()


class _CudaGraphSessionAdapter:
    """Drop-in wrapper around an ONNX Runtime session.

    Routes ``.run()`` through CUDA graph replay when a recorded graph is
    available, and transparently proxies every other attribute to the
    underlying session so insightface's INSwapper sees an unchanged API.
    """

    def __init__(self, underlying):
        # Use object.__setattr__ to bypass our own __setattr__.
        object.__setattr__(self, "_underlying", underlying)

    def run(self, output_names, input_dict, **kwargs):
        if _cuda_graph_session['recorded']:
            try:
                keys = list(input_dict.keys())
                blob = input_dict[keys[0]]
                latent = input_dict[keys[1]]
                return [_cuda_graph_swap_inference(blob, latent)]
            except Exception:
                pass
        return self._underlying.run(output_names, input_dict, **kwargs)

    def __getattr__(self, name):
        return getattr(self._underlying, name)

    def __setattr__(self, name, value):
        setattr(self._underlying, name, value)


def _init_cuda_graph_session(model_path: str, swapper):
    """Create a CUDA-graph-enabled ONNX session for the swap model.

    CUDA graphs record the GPU kernel launch sequence once, then replay it
    with near-zero CPU overhead on subsequent runs.  Requires static input
    shapes (inswapper is always 1x3x128x128 + 1x512).
    """
    import onnxruntime as ort
    try:
        providers = build_provider_config(
            ["CUDAExecutionProvider"],
            enable_cuda_graph=True,
        )
        sess = ort.InferenceSession(model_path, providers=providers)

        # Pre-allocate GPU buffers with correct shapes
        inp_shape = (1, 3, swapper.input_size[1], swapper.input_size[0])
        latent_shape = (1, 512)
        dummy_inp = np.zeros(inp_shape, dtype=np.float32)
        dummy_lat = np.zeros(latent_shape, dtype=np.float32)

        ort_input = ort.OrtValue.ortvalue_from_numpy(dummy_inp, 'cuda', 0)
        ort_latent = ort.OrtValue.ortvalue_from_numpy(dummy_lat, 'cuda', 0)

        io = sess.io_binding()
        io.bind_ortvalue_input(swapper.input_names[0], ort_input)
        io.bind_ortvalue_input(swapper.input_names[1], ort_latent)
        io.bind_output(swapper.output_names[0], 'cuda', 0)

        # First run records the CUDA graph
        sess.run_with_iobinding(io)

        _cuda_graph_session['session'] = sess
        _cuda_graph_session['io_binding'] = io
        _cuda_graph_session['ort_input'] = ort_input
        _cuda_graph_session['ort_latent'] = ort_latent
        _cuda_graph_session['recorded'] = True

        # Wrap swapper.session in an adapter instead of rebinding
        # session.run. insightface's INSwapper.get() reads .run via the
        # session attribute, so either works; the adapter survives any
        # later attribute reads on the session and keeps the original
        # session object untouched.
        if not isinstance(swapper.session, _CudaGraphSessionAdapter):
            swapper.session = _CudaGraphSessionAdapter(swapper.session)

        import sys
        print(f"[{NAME}] CUDA graph session initialized (swap model)")
        sys.stdout.flush()
    except Exception as e:
        print(f"[{NAME}] CUDA graph init failed, using standard session: {e}")
        _cuda_graph_session['recorded'] = False


def _cuda_graph_swap_inference(blob: np.ndarray, latent: np.ndarray) -> np.ndarray:
    """Run swap model via CUDA graph replay — minimal CPU overhead."""
    cg = _cuda_graph_session
    with _cuda_graph_lock:
        cg['ort_input'].update_inplace(blob)
        cg['ort_latent'].update_inplace(latent)
        cg['session'].run_with_iobinding(cg['io_binding'])
        return cg['io_binding'].get_outputs()[0].numpy()


def _fast_paste_back(
    target_img: Frame,
    bgr_fake: np.ndarray,
    aimg: np.ndarray,
    M: np.ndarray,
    target_face: Face | None = None,
) -> Frame:
    """Paste bgr_fake back onto target_img via the inverse affine of M.

    Restricts work to the face bbox in output coordinates and warps a
    precomputed feathered alpha template per-frame instead of running a
    size-scaled erode+blur on the warped mask. Cost is O(crop_area) regardless
    of how much of the frame the face occupies.
    """
    h, w = target_img.shape[:2]
    face_h, face_w = aimg.shape[:2]
    # inswapper's aligned-face space is square (128x128). _get_soft_alpha
    # caches a single NxN template keyed by N, so fail loudly if that ever
    # stops being true rather than silently mis-warping the alpha mask.
    assert face_h == face_w, f"Expected square aligned face, got {face_h}x{face_w}"
    IM = cv2.invertAffineTransform(M)

    # Bbox in output coords from the affine corners of the aligned-face square.
    corners = np.array(
        [[0, 0], [face_w, 0], [face_w, face_h], [0, face_h]], dtype=np.float32
    )
    transformed = (IM[:, :2] @ corners.T).T + IM[:, 2]
    x1 = int(np.floor(transformed[:, 0].min()))
    x2 = int(np.ceil(transformed[:, 0].max()))
    y1 = int(np.floor(transformed[:, 1].min()))
    y2 = int(np.ceil(transformed[:, 1].max()))
    if x1 >= x2 or y1 >= y2:
        return target_img

    # Small interpolation margin only — the feather is baked into the template.
    pad = 2
    y1p, y2p = max(0, y1 - pad), min(h, y2 + pad + 1)
    x1p, x2p = max(0, x1 - pad), min(w, x2 + pad + 1)

    IM_crop = IM.copy()
    IM_crop[0, 2] -= x1p
    IM_crop[1, 2] -= y1p
    crop_w, crop_h = x2p - x1p, y2p - y1p

    target_crop = target_img[y1p:y2p, x1p:x2p]
    profile_amount = estimate_profile_score(target_face)
    feather_settings = get_adaptive_feather_settings(
        crop_shape=target_crop.shape,
        frame_shape=target_img.shape,
        edge_contrast=estimate_edge_contrast(target_crop),
        blur_amount=estimate_blur_amount(target_crop),
        base_erode_ratio=getattr(
            modules.globals,
            "compositing_mask_erode_ratio",
            0.10,
        ),
        base_blur_ratio=getattr(
            modules.globals,
            "compositing_mask_blur_ratio",
            0.05,
        ),
        scale_strength=getattr(
            modules.globals,
            "compositing_mask_scale_strength",
            0.35,
        ),
        edge_strength=getattr(
            modules.globals,
            "compositing_mask_edge_strength",
            0.35,
        ),
        blur_strength=getattr(
            modules.globals,
            "compositing_mask_motion_blur_strength",
            0.0,
        ),
        motion_amount=_tracking_motion_amount(target_face),
        motion_strength=getattr(
            modules.globals,
            "compositing_mask_motion_strength",
            0.0,
        ),
        profile_amount=profile_amount,
        profile_strength=getattr(
            modules.globals,
            "compositing_mask_profile_strength",
            0.0,
        ),
    )
    soft_alpha = _get_soft_alpha(face_h, feather_settings)
    bgr_fake_crop = cv2.warpAffine(bgr_fake, IM_crop, (crop_w, crop_h), borderMode=cv2.BORDER_REPLICATE)
    alpha_crop = cv2.warpAffine(soft_alpha, IM_crop, (crop_w, crop_h), borderValue=0)
    extended_subject_enabled = getattr(
        modules.globals,
        "compositing_extended_subject_mask",
        False,
    )
    landmark_mask_strength = getattr(
        modules.globals,
        "compositing_landmark_mask_strength",
        0.0,
    )
    if extended_subject_enabled:
        landmark_mask_strength = max(float(landmark_mask_strength or 0.0), 1.0)
    alpha_crop = refine_alpha_with_landmark_mask(
        alpha_crop,
        target_face,
        target_img.shape,
        (x1p, y1p, x2p, y2p),
        strength=landmark_mask_strength,
        dilation_ratio=getattr(
            modules.globals,
            "compositing_landmark_mask_dilation_ratio",
            0.025,
        ),
        feather_ratio=getattr(
            modules.globals,
            "compositing_landmark_mask_feather_ratio",
            0.018,
        ),
        profile_amount=profile_amount,
        profile_taper_ratio=getattr(
            modules.globals,
            "compositing_landmark_mask_profile_taper",
            0.0,
        ),
        extended_subject=extended_subject_enabled,
        hairline_ratio=getattr(
            modules.globals,
            "compositing_extended_subject_hairline_ratio",
            0.32,
        ),
        side_ratio=getattr(
            modules.globals,
            "compositing_extended_subject_side_ratio",
            0.24,
        ),
        shoulder_ratio=getattr(
            modules.globals,
            "compositing_extended_subject_shoulder_ratio",
            0.48,
        ),
        chest_ratio=getattr(
            modules.globals,
            "compositing_extended_subject_chest_ratio",
            0.58,
        ),
    )
    alpha_crop = refine_alpha_with_skin_chroma_mask(
        alpha_crop,
        target_crop,
        strength=getattr(
            modules.globals,
            "compositing_skin_mask_strength",
            0.0,
        ),
        chroma_threshold=getattr(
            modules.globals,
            "compositing_skin_mask_chroma_threshold",
            1.8,
        ),
        max_reduction=getattr(
            modules.globals,
            "compositing_skin_mask_max_reduction",
            0.45,
        ),
        blur_ratio=getattr(
            modules.globals,
            "compositing_skin_mask_blur_ratio",
            0.015,
        ),
        luma_threshold=getattr(
            modules.globals,
            "compositing_skin_mask_luma_threshold",
            0.0,
        ),
        luma_max_reduction=getattr(
            modules.globals,
            "compositing_skin_mask_luma_max_reduction",
            0.0,
        ),
    )
    occlusion_priority_mask = create_expression_occlusion_mask(
        target_face,
        target_img.shape,
        (x1p, y1p, x2p, y2p),
        mouth_strength=getattr(
            modules.globals,
            "compositing_occlusion_mouth_region_strength",
            0.0,
        ),
        eye_strength=getattr(
            modules.globals,
            "compositing_occlusion_eye_region_strength",
            0.0,
        ),
        feather_ratio=getattr(
            modules.globals,
            "compositing_occlusion_region_feather_ratio",
            0.018,
        ),
        mouth_min_confidence=getattr(
            modules.globals,
            "expression_mouth_min_confidence",
            0.0,
        ),
        eye_min_confidence=getattr(
            modules.globals,
            "expression_eye_min_confidence",
            0.0,
        ),
    )
    occlusion_priority_mask = _smooth_occlusion_priority_mask(
        occlusion_priority_mask,
        target_face,
    )
    alpha_crop = preserve_target_edges_in_alpha(
        alpha_crop,
        target_crop,
        strength=getattr(
            modules.globals,
            "compositing_occlusion_edge_strength",
            0.0,
        ),
        edge_threshold=getattr(
            modules.globals,
            "compositing_occlusion_edge_threshold",
            0.35,
        ),
        max_reduction=getattr(
            modules.globals,
            "compositing_occlusion_edge_max_reduction",
            0.55,
        ),
        blur_ratio=getattr(
            modules.globals,
            "compositing_occlusion_edge_blur_ratio",
            0.015,
        ),
        min_contrast=getattr(
            modules.globals,
            "compositing_occlusion_edge_min_contrast",
            24.0,
        ),
        detail_strength=getattr(
            modules.globals,
            "compositing_occlusion_detail_strength",
            0.0,
        ),
        detail_threshold=getattr(
            modules.globals,
            "compositing_occlusion_detail_threshold",
            0.12,
        ),
        priority_mask=occlusion_priority_mask,
        priority_strength=getattr(
            modules.globals,
            "compositing_occlusion_region_boost",
            0.0,
        ),
    )
    temporal_alpha_base_strength = _compositing_alpha_temporal_strength()
    temporal_alpha_strength = _motion_adjusted_compositing_alpha_temporal_strength(
        temporal_alpha_base_strength,
        target_face,
    )
    temporal_alpha_key = _compositing_temporal_key(target_face)
    if temporal_alpha_base_strength <= 0.0 or _tracking_should_reset_temporal_state(
        target_face
    ):
        _reset_compositing_alpha_temporal_state()
    alpha_crop = _smooth_compositing_alpha(
        alpha_crop,
        temporal_alpha_key,
        temporal_alpha_strength,
    )

    temporal_color_base_strength = _compositing_temporal_strength()
    temporal_color_strength = _motion_adjusted_compositing_temporal_strength(
        temporal_color_base_strength,
        target_face,
    )
    temporal_color_key = _compositing_temporal_key(target_face)
    if temporal_color_base_strength <= 0.0 or _tracking_should_reset_temporal_state(
        target_face
    ):
        _reset_compositing_color_temporal_state()

    color_match_strength = getattr(
        modules.globals, "compositing_color_match_strength", 0.0
    )
    if color_match_strength > 0.0:
        bgr_fake_crop = match_color_statistics(
            bgr_fake_crop,
            target_crop,
            alpha_crop,
            strength=color_match_strength,
            trim_percentile=getattr(
                modules.globals,
                "compositing_color_match_trim_percentile",
                0.0,
            ),
            chroma_trim_percentile=getattr(
                modules.globals,
                "compositing_color_chroma_trim_percentile",
                0.0,
            ),
            statistics_transform=_color_statistics_transform(
                temporal_color_key,
                temporal_color_strength,
            ),
        )
    lighting_match_strength = getattr(
        modules.globals, "compositing_lighting_match_strength", 0.0
    )
    if lighting_match_strength > 0.0:
        bgr_fake_crop = match_luminance_statistics(
            bgr_fake_crop,
            target_crop,
            alpha_crop,
            strength=lighting_match_strength,
            contrast_strength=getattr(
                modules.globals,
                "compositing_lighting_contrast_strength",
                0.35,
            ),
            max_mean_shift=getattr(
                modules.globals,
                "compositing_lighting_max_shift",
                12.0,
            ),
            trim_percentile=getattr(
                modules.globals,
                "compositing_color_match_trim_percentile",
                0.0,
            ),
            statistics_transform=_luminance_statistics_transform(
                temporal_color_key,
                temporal_color_strength,
            ),
        )
    alpha_crop = refine_alpha_with_boundary_color_mismatch(
        alpha_crop,
        bgr_fake_crop,
        target_crop,
        strength=getattr(
            modules.globals,
            "compositing_boundary_mismatch_strength",
            0.0,
        ),
        color_threshold=getattr(
            modules.globals,
            "compositing_boundary_mismatch_threshold",
            0.18,
        ),
        max_reduction=getattr(
            modules.globals,
            "compositing_boundary_mismatch_max_reduction",
            0.45,
        ),
        band_ratio=getattr(
            modules.globals,
            "compositing_boundary_mismatch_band_ratio",
            0.035,
        ),
        blur_ratio=getattr(
            modules.globals,
            "compositing_boundary_mismatch_blur_ratio",
            0.012,
        ),
    )

    torch = _torch_module() if _has_torch_cuda() else None
    if torch is not None:
        # Scale alpha to [0, 1] on device — cheaper to upload uint8 than float.
        mask_t = torch.from_numpy(alpha_crop).cuda().float().mul_(1.0 / 255.0).unsqueeze(2)
        fake_t = torch.from_numpy(bgr_fake_crop).float().cuda()
        tgt_t = torch.from_numpy(target_crop).float().cuda()
        blended = (mask_t * fake_t + (1.0 - mask_t) * tgt_t).to(torch.uint8).cpu().numpy()
        target_img[y1p:y2p, x1p:x2p] = blended
    else:
        # Fused uint8 blend via cv2 SIMD — no float32 round-trip.
        # Measured ~7-8× faster than the old numpy float32 path on a 1000×1000 crop.
        alpha_3c = cv2.merge([alpha_crop, alpha_crop, alpha_crop])
        inv_alpha = 255 - alpha_3c
        a_fake = cv2.multiply(bgr_fake_crop, alpha_3c, scale=1.0 / 255.0)
        a_tgt = cv2.multiply(target_crop, inv_alpha, scale=1.0 / 255.0)
        target_img[y1p:y2p, x1p:x2p] = cv2.add(a_fake, a_tgt)

    return target_img


def swap_face(source_face: Face, target_face: Face, temp_frame: Frame) -> Frame:
    """Optimized face swapping with better memory management and performance."""
    face_swapper = get_face_swapper()
    if face_swapper is None:
        update_status("Face swapper model not loaded or failed to load. Skipping swap.", NAME)
        return temp_frame

    # Safety check for faces
    if source_face is None or target_face is None:
        return temp_frame
    if not hasattr(source_face, 'normed_embedding') or source_face.normed_embedding is None:
        return temp_frame

    normalized_frame = _normalize_bgr_frame(temp_frame)
    if normalized_frame is None:
        return temp_frame
    temp_frame = normalized_frame

    # _fast_paste_back writes in-place on the GPU path.  Only copy when
    # mouth_mask or opacity < 1 need an unmodified original.
    opacity = getattr(modules.globals, "opacity", 1.0)
    opacity = max(0.0, min(1.0, opacity))
    mouth_mask_enabled = getattr(modules.globals, "mouth_mask", False)
    needs_original = opacity < 1.0 or mouth_mask_enabled
    if needs_original:
        original_frame = temp_frame.copy()
    else:
        original_frame = temp_frame

    if temp_frame.dtype != np.uint8:
        temp_frame = np.clip(temp_frame, 0, 255).astype(np.uint8)

    try:
        if not temp_frame.flags['C_CONTIGUOUS']:
            temp_frame = np.ascontiguousarray(temp_frame)

        # Use paste_back=False and our optimized paste-back
        if any("DmlExecutionProvider" in p for p in modules.globals.execution_providers):
            with modules.globals.dml_lock:
                bgr_fake, M = face_swapper.get(
                    temp_frame, target_face, source_face, paste_back=False
                )
        else:
            bgr_fake, M = face_swapper.get(
                temp_frame, target_face, source_face, paste_back=False
            )

        if bgr_fake is None:
            return original_frame

        if not isinstance(bgr_fake, np.ndarray):
            return original_frame

        # Pass a dummy aimg with correct shape — _fast_paste_back only uses aimg.shape
        # to create the white mask. Avoids redundant norm_crop2 (~0.6ms).
        _face_size = face_swapper.input_size[0]
        _aimg_dummy = np.empty((_face_size, _face_size, 3), dtype=np.uint8)

        swapped_frame = _fast_paste_back(
            temp_frame,
            bgr_fake,
            _aimg_dummy,
            M,
            target_face,
        )

    except Exception as e:
        print(f"Error during face swap: {e}")
        return original_frame

    # --- Post-swap Processing (Masking, Opacity, etc.) ---
    # Now, work with the guaranteed uint8 'swapped_frame'

    if mouth_mask_enabled: # Check if mouth_mask is enabled
        # Create a mask for the target face
        face_mask = create_face_mask(target_face, original_frame) # Use original_frame for mask creation geometry

        # Create the mouth mask using the ORIGINAL frame (before swap) for cutout
        mouth_mask, mouth_cutout, mouth_box, lower_lip_polygon = (
            create_lower_mouth_mask(target_face, original_frame) # Use original_frame for real mouth cutout
        )

        # Apply the mouth area only if mouth_cutout exists
        if mouth_cutout is not None and mouth_box != (0,0,0,0):
            # Apply mouth area (from original) onto the 'swapped_frame'
            swapped_frame = apply_mouth_area(
                swapped_frame, mouth_cutout, mouth_box, face_mask, lower_lip_polygon
            )

            # Draw bounding box only while slider is being dragged
            if getattr(modules.globals, "show_mouth_mask_box", False):
                mouth_mask_data = (mouth_mask, mouth_cutout, mouth_box, lower_lip_polygon)
                swapped_frame = draw_mouth_mask_visualization(
                    swapped_frame, target_face, mouth_mask_data
                )
        
    # --- Poisson Blending ---
    if getattr(modules.globals, "poisson_blend", False):
        face_mask = create_face_mask(target_face, temp_frame)
        if face_mask is not None:
            # Find bounding box of the mask
            y_indices, x_indices = np.where(face_mask > 0)
            if len(x_indices) > 0 and len(y_indices) > 0:
                x_min, x_max = np.min(x_indices), np.max(x_indices)
                y_min, y_max = np.min(y_indices), np.max(y_indices)

                # Calculate center
                center = (int((x_min + x_max) / 2), int((y_min + y_max) / 2))

                # Crop src and mask
                src_crop = swapped_frame[y_min : y_max + 1, x_min : x_max + 1]
                mask_crop = face_mask[y_min : y_max + 1, x_min : x_max + 1]

                try:
                    # Use original_frame as destination to blend the swapped face onto it
                    swapped_frame = cv2.seamlessClone(
                        src_crop,
                        original_frame,
                        mask_crop,
                        center,
                        cv2.NORMAL_CLONE,
                    )
                except Exception as e:
                    print(f"Poisson blending failed: {e}")
        
    # Apply opacity blend between the original frame and the swapped frame
    if opacity >= 1.0:
        return swapped_frame.astype(np.uint8)

    # Blend the original_frame with the (potentially mouth-masked) swapped_frame
    final_swapped_frame = gpu_add_weighted(original_frame.astype(np.uint8), 1 - opacity, swapped_frame.astype(np.uint8), opacity, 0)
    return final_swapped_frame.astype(np.uint8)


def _normalize_bgr_frame(frame: Frame) -> np.ndarray | None:
    if frame is None or not hasattr(frame, "shape"):
        return None
    try:
        array = np.asarray(frame)
    except (TypeError, ValueError):
        return None
    if array.size == 0:
        return None
    if array.ndim == 2:
        return cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)
    if array.ndim != 3:
        return None
    if array.shape[2] == 3:
        return array
    if array.shape[2] == 4:
        return cv2.cvtColor(array, cv2.COLOR_BGRA2BGR)
    if array.shape[2] == 1:
        return cv2.cvtColor(array[:, :, 0], cv2.COLOR_GRAY2BGR)
    return None


# --- START: Mac M1-M5 Optimized Face Detection ---
def get_faces_optimized(frame: Frame, use_cache: bool = True) -> Optional[List[Face]]:
    """Optimized face detection for live mode on Apple Silicon"""
    global LAST_DETECTION_TIME, FACE_DETECTION_CACHE
    
    if not use_cache or not IS_APPLE_SILICON:
        # Standard detection
        if modules.globals.many_faces:
            return get_many_faces(frame)
        else:
            face = get_one_face(frame)
            return [face] if face else None
    
    # Adaptive detection rate for live mode
    current_time = time.time()
    time_since_last = current_time - LAST_DETECTION_TIME
    
    # Skip detection if too soon (adaptive frame skipping)
    if time_since_last < DETECTION_INTERVAL and FACE_DETECTION_CACHE:
        return FACE_DETECTION_CACHE.get('faces')
    
    # Perform detection
    LAST_DETECTION_TIME = current_time
    if modules.globals.many_faces:
        faces = get_many_faces(frame)
    else:
        face = get_one_face(frame)
        faces = [face] if face else None
    
    # Cache results
    FACE_DETECTION_CACHE['faces'] = faces
    FACE_DETECTION_CACHE['timestamp'] = current_time
    
    return faces
# --- END: Mac M1-M5 Optimized Face Detection ---

# --- START: Helper function for interpolation and sharpening ---
def apply_post_processing(
    current_frame: Frame,
    swapped_face_bboxes: List[np.ndarray],
    swapped_faces: Optional[List[Face]] = None,
) -> Frame:
    """Apply face-region sharpening and temporal smoothing."""
    global PREVIOUS_FRAME_RESULT, PREVIOUS_EXPRESSION_SNAPSHOTS

    sharpness_value = getattr(modules.globals, "sharpness", 0.0)
    enable_interpolation = getattr(modules.globals, "enable_interpolation", False)
    interpolation_weight = getattr(modules.globals, "interpolation_weight", 0.2)
    interpolation_active = (
        enable_interpolation
        and 0.0 < interpolation_weight < 1.0
        and bool(swapped_face_bboxes)
    )

    # Skip copy when no post-processing is active
    if sharpness_value <= 0.0 and not interpolation_active:
        PREVIOUS_FRAME_RESULT = None
        PREVIOUS_EXPRESSION_SNAPSHOTS = {}
        return _apply_diagnostic_overlay(
            current_frame,
            swapped_face_bboxes,
            swapped_faces,
        )

    processed_frame = current_frame.copy()

    # 1. Apply Sharpening (if enabled) with optimized kernel for Apple Silicon
    sharpness_value = getattr(modules.globals, "sharpness", 0.0)
    if sharpness_value > 0.0 and swapped_face_bboxes:
        height, width = processed_frame.shape[:2]
        for face_index, bbox in enumerate(swapped_face_bboxes):
            # Ensure bbox is iterable and has 4 elements
            if not hasattr(bbox, '__iter__') or len(bbox) != 4:
                # print(f"Warning: Invalid bbox format for sharpening: {bbox}") # Debug
                continue
            x1, y1, x2, y2 = bbox
            # Ensure coordinates are integers and within bounds
            try:
                 x1, y1 = max(0, int(x1)), max(0, int(y1))
                 x2, y2 = min(width, int(x2)), min(height, int(y2))
            except ValueError:
                # print(f"Warning: Could not convert bbox coordinates to int: {bbox}") # Debug
                continue


            if x2 <= x1 or y2 <= y1:
                continue

            face_region = processed_frame[y1:y2, x1:x2]
            if face_region.size == 0: continue

            # Apply sharpening (GPU-accelerated when CUDA OpenCV is available)
            try:
                face = _face_at_index(swapped_faces, face_index)
                effective_sharpness = _adjusted_sharpness_strength(
                    sharpness_value,
                    face_region,
                    face,
                )
                if effective_sharpness <= 0.0:
                    continue
                sigma = 2 if IS_APPLE_SILICON else 3
                sharpened_region = gpu_sharpen(
                    face_region,
                    strength=effective_sharpness,
                    sigma=sigma,
                )
                processed_frame[y1:y2, x1:x2] = sharpened_region
            except cv2.error:
                pass


    final_frame = processed_frame # Start with the current (potentially sharpened) frame

    if interpolation_active:
        stabilized_faces = _stabilized_expression_faces(swapped_faces)
        effective_interpolation_weight = _expression_adjusted_interpolation_weight(
            interpolation_weight,
            stabilized_faces,
        )
        effective_interpolation_weight = _motion_adjusted_interpolation_weight(
            effective_interpolation_weight,
            swapped_faces,
        )
        if PREVIOUS_FRAME_RESULT is not None and PREVIOUS_FRAME_RESULT.shape == processed_frame.shape and PREVIOUS_FRAME_RESULT.dtype == processed_frame.dtype:
            try:
                final_frame = blend_frame_regions(
                    PREVIOUS_FRAME_RESULT,
                    processed_frame,
                    swapped_face_bboxes,
                    current_weight=effective_interpolation_weight,
                    expansion_ratio=getattr(
                        modules.globals,
                        "temporal_smoothing_region_expansion",
                        0.18,
                    ),
                    feather_ratio=getattr(
                        modules.globals,
                        "temporal_smoothing_feather_ratio",
                        0.18,
                    ),
                    masks=_temporal_smoothing_masks(swapped_faces, processed_frame),
                    mask_strength=getattr(
                        modules.globals,
                        "temporal_smoothing_mask_strength",
                        0.0,
                    ),
                    local_current_weight_masks=_temporal_expression_response_masks(
                        stabilized_faces,
                        processed_frame,
                    ),
                    local_current_weight_boost=getattr(
                        modules.globals,
                        "temporal_smoothing_expression_region_boost",
                        0.0,
                    ),
                )
            except Exception:
                # Keep live/video processing moving if temporal smoothing fails.
                final_frame = processed_frame

            # Update the state for the next frame *with the interpolated result*
            PREVIOUS_FRAME_RESULT = final_frame.copy()
        else:
            # If previous frame invalid or doesn't match, use current frame and update state
            if PREVIOUS_FRAME_RESULT is not None and PREVIOUS_FRAME_RESULT.shape != processed_frame.shape:
                # print("Info: Frame shape changed, resetting interpolation state.") # Debug
                pass
            PREVIOUS_FRAME_RESULT = processed_frame.copy()
    else:
        # Interpolation is off or weight is invalid — no need to cache
        PREVIOUS_FRAME_RESULT = None
        PREVIOUS_EXPRESSION_SNAPSHOTS = {}


    return _apply_diagnostic_overlay(final_frame, swapped_face_bboxes, swapped_faces)
# --- END: Helper function for interpolation and sharpening ---


def _face_at_index(
    faces: Optional[List[Face]] | None,
    index: int,
) -> Face | Mapping | None:
    if not faces or index < 0 or index >= len(faces):
        return None
    return faces[index]


def _adjusted_sharpness_strength(
    base_strength: float,
    face_region: np.ndarray,
    face: Face | Mapping | None = None,
) -> float:
    strength = max(0.0, float(base_strength or 0.0))
    if strength <= 0.0:
        return 0.0

    motion_reduction = float(
        np.clip(
            getattr(
                modules.globals,
                "postprocess_sharpness_motion_reduction",
                0.0,
            )
            or 0.0,
            0.0,
            1.0,
        )
    )
    blur_reduction = float(
        np.clip(
            getattr(
                modules.globals,
                "postprocess_sharpness_blur_reduction",
                0.0,
            )
            or 0.0,
            0.0,
            1.0,
        )
    )
    if motion_reduction <= 0.0 and blur_reduction <= 0.0:
        return strength

    motion_amount = _tracking_motion_amount(face)
    blur_amount = estimate_blur_amount(face_region) if blur_reduction > 0.0 else 0.0
    motion_factor = 1.0 - motion_reduction * motion_amount
    blur_factor = 1.0 - blur_reduction * blur_amount
    return float(np.clip(strength * motion_factor * blur_factor, 0.0, strength))


def _expression_adjusted_interpolation_weight(
    base_weight: float,
    swapped_faces: Optional[List[Face]] = None,
) -> float:
    global PREVIOUS_EXPRESSION_SNAPSHOTS

    if not getattr(modules.globals, "expression_temporal_smoothing", False):
        PREVIOUS_EXPRESSION_SNAPSHOTS = {}
        return base_weight

    current_snapshots = collect_expression_snapshots(swapped_faces or [])
    adjusted_weight = expression_temporal_weight(
        base_weight,
        PREVIOUS_EXPRESSION_SNAPSHOTS,
        current_snapshots,
        stable_threshold=getattr(
            modules.globals,
            "expression_temporal_motion_threshold",
            0.035,
        ),
        high_motion_threshold=getattr(
            modules.globals,
            "expression_temporal_high_motion_threshold",
            0.09,
        ),
        stable_weight_multiplier=getattr(
            modules.globals,
            "expression_temporal_stable_weight_multiplier",
            0.86,
        ),
        motion_weight_boost=getattr(
            modules.globals,
            "expression_temporal_motion_weight_boost",
            0.22,
        ),
        unilateral_eye_motion_scale=getattr(
            modules.globals,
            "expression_temporal_unilateral_eye_motion_scale",
            1.0,
        ),
        mouth_min_confidence=getattr(
            modules.globals,
            "expression_mouth_min_confidence",
            0.25,
        ),
        eye_min_confidence=getattr(
            modules.globals,
            "expression_eye_min_confidence",
            0.25,
        ),
    )
    PREVIOUS_EXPRESSION_SNAPSHOTS = current_snapshots
    return adjusted_weight


def _temporal_smoothing_masks(
    swapped_faces: Optional[List[Face]] = None,
    frame: Frame | None = None,
) -> List[np.ndarray | None] | None:
    strength = getattr(modules.globals, "temporal_smoothing_mask_strength", 0.0)
    if strength <= 0.0 or frame is None or not swapped_faces:
        return None

    masks: List[np.ndarray | None] = []
    for face in swapped_faces:
        masks.append(
            create_landmark_face_mask(
                face,
                frame.shape,
                dilation_ratio=getattr(
                    modules.globals,
                    "compositing_landmark_mask_dilation_ratio",
                    0.025,
                ),
                feather_ratio=getattr(
                    modules.globals,
                    "compositing_landmark_mask_feather_ratio",
                    0.018,
                ),
                profile_amount=estimate_profile_score(face),
                profile_taper_ratio=getattr(
                    modules.globals,
                    "compositing_landmark_mask_profile_taper",
                    0.0,
                ),
                extended_subject=getattr(
                    modules.globals,
                    "compositing_extended_subject_mask",
                    False,
                ),
                hairline_ratio=getattr(
                    modules.globals,
                    "compositing_extended_subject_hairline_ratio",
                    0.32,
                ),
                side_ratio=getattr(
                    modules.globals,
                    "compositing_extended_subject_side_ratio",
                    0.24,
                ),
                shoulder_ratio=getattr(
                    modules.globals,
                    "compositing_extended_subject_shoulder_ratio",
                    0.48,
                ),
                chest_ratio=getattr(
                    modules.globals,
                    "compositing_extended_subject_chest_ratio",
                    0.58,
                ),
            )
        )
    return masks


def _temporal_expression_response_masks(
    swapped_faces: Optional[List[Face]] | None,
    frame: Frame,
) -> list[np.ndarray | None] | None:
    boost = float(
        getattr(modules.globals, "temporal_smoothing_expression_region_boost", 0.0)
        or 0.0
    )
    if boost <= 0.0:
        return None

    frame_h, frame_w = frame.shape[:2]
    masks: list[np.ndarray | None] = []
    for face in swapped_faces or []:
        masks.append(
            create_expression_occlusion_mask(
                face,
                frame.shape,
                (0, 0, frame_w, frame_h),
                mouth_strength=getattr(
                    modules.globals,
                    "temporal_smoothing_expression_mouth_strength",
                    0.0,
                ),
                eye_strength=getattr(
                    modules.globals,
                    "temporal_smoothing_expression_eye_strength",
                    0.0,
                ),
                feather_ratio=getattr(
                    modules.globals,
                    "temporal_smoothing_expression_feather_ratio",
                    0.018,
                ),
                mouth_min_confidence=getattr(
                    modules.globals,
                    "expression_mouth_min_confidence",
                    0.0,
                ),
                eye_min_confidence=getattr(
                    modules.globals,
                    "expression_eye_min_confidence",
                    0.0,
                ),
            )
        )
    return masks


def _motion_adjusted_interpolation_weight(
    base_weight: float,
    swapped_faces: Optional[List[Face]] = None,
) -> float:
    boost = float(
        getattr(modules.globals, "temporal_smoothing_motion_weight_boost", 0.0)
        or 0.0
    )
    if boost <= 0.0:
        return base_weight

    motion_amounts = [
        _tracking_motion_amount(face)
        for face in (swapped_faces or [])
        if face is not None
    ]
    if not motion_amounts:
        return base_weight

    motion = max(motion_amounts)
    low_threshold = max(
        0.0,
        float(
            getattr(modules.globals, "temporal_smoothing_motion_threshold", 0.08)
            or 0.0
        ),
    )
    high_threshold = max(
        low_threshold,
        float(
            getattr(
                modules.globals,
                "temporal_smoothing_high_motion_threshold",
                0.35,
            )
            or low_threshold
        ),
    )
    if motion <= low_threshold:
        return base_weight

    if motion >= high_threshold:
        amount = 1.0
    else:
        amount = (motion - low_threshold) / max(high_threshold - low_threshold, 1e-6)
    return float(np.clip(float(base_weight) + boost * amount, 0.08, 0.90))


def _tracking_motion_amount(face: Face | None) -> float:
    if face is None:
        return 0.0
    raw_motion_amount = _face_value(face, "tracking_motion_amount", 0.0)
    try:
        return float(np.clip(raw_motion_amount, 0.0, 1.0))
    except (TypeError, ValueError):
        return 0.0


def _tracking_missed_frames(face: Face | Mapping | None) -> int:
    raw_missed = _face_value(face, "tracking_missed_frames", 0)
    try:
        return max(0, int(raw_missed))
    except (TypeError, ValueError):
        return 0


def _tracking_prediction_active(face: Face | Mapping | None) -> bool:
    return bool(_face_value(face, "tracking_prediction_active", False))


def _tracking_should_reset_temporal_state(face: Face | Mapping | None) -> bool:
    return _tracking_missed_frames(face) > 0 and not _tracking_prediction_active(face)


def _face_value(face: Face | Mapping | None, attr: str, default: Any = None) -> Any:
    if isinstance(face, Mapping) and attr in face:
        return face[attr]
    return getattr(face, attr, default)


def _face_array(face: Face | Mapping | None, attr: str) -> np.ndarray | None:
    value = _face_value(face, attr, None)
    if value is None:
        return None
    try:
        array = np.asarray(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if array.size == 0 or not np.all(np.isfinite(array)):
        return None
    return array


def _face_bbox(face: Face | Mapping | None) -> np.ndarray | None:
    bbox = _face_array(face, "bbox")
    if bbox is None:
        return None
    bbox = bbox.reshape(-1)
    if bbox.size < 4:
        return None
    x1, y1, x2, y2 = bbox[:4]
    left, right = sorted((float(x1), float(x2)))
    top, bottom = sorted((float(y1), float(y2)))
    if right <= left or bottom <= top:
        return None
    return np.array([left, top, right, bottom], dtype=np.float32)


def _record_swapped_face(
    face: Face | Mapping | None,
    swapped_face_bboxes: List[np.ndarray],
    swapped_faces: List[Face | Mapping],
) -> None:
    bbox = _face_bbox(face)
    if bbox is None:
        return
    swapped_face_bboxes.append(bbox.astype(int))
    swapped_faces.append(face)


def _apply_diagnostic_overlay(
    frame: Frame,
    swapped_face_bboxes: List[np.ndarray],
    swapped_faces: Optional[List[Face]] = None,
) -> Frame:
    diagnostic_enabled = getattr(modules.globals, "diagnostic_overlay", False)
    subject_mask_enabled = getattr(
        modules.globals,
        "compositing_show_subject_mask",
        False,
    )
    if not diagnostic_enabled and not subject_mask_enabled:
        return frame

    layers = (
        list(getattr(
            modules.globals,
            "diagnostic_overlay_layers",
            ["bbox", "kps", "profile"],
        ))
        if diagnostic_enabled
        else []
    )
    if subject_mask_enabled and "mask" not in layers:
        layers.append("mask")
    faces = [face for face in (swapped_faces or []) if face is not None]
    if not faces and swapped_face_bboxes:
        faces = [{"bbox": bbox} for bbox in swapped_face_bboxes]

    masks = None
    if "mask" in layers and faces:
        masks = [create_face_mask(face, frame) for face in faces]

    return draw_diagnostic_overlay(
        frame,
        faces,
        layers=layers,
        profile_name=getattr(modules.globals, "quality_mode", None),
        masks=masks,
    )


def process_frame(source_face: Face, temp_frame: Frame, target_face: Face = None) -> Frame:
    """Process a single frame, swapping source_face onto detected target(s).

    Args:
        target_face: Pre-detected target face. When provided, skips the
            internal face detection call (saves ~30-40ms per frame).
            Ignored when many_faces mode is active.
    """
    if getattr(modules.globals, "opacity", 1.0) == 0:
        global PREVIOUS_FRAME_RESULT
        PREVIOUS_FRAME_RESULT = None
        return temp_frame

    processed_frame = temp_frame
    swapped_face_bboxes = []
    swapped_faces = []

    if modules.globals.many_faces:
        many_faces = get_many_faces(processed_frame)
        if many_faces:
            current_swap_target = processed_frame.copy()
            for face in many_faces:
                current_swap_target = swap_face(source_face, face, current_swap_target)
                _record_swapped_face(face, swapped_face_bboxes, swapped_faces)
            processed_frame = current_swap_target
    else:
        if target_face is None:
            target_face = get_one_face(processed_frame)
        if target_face:
            processed_frame = swap_face(source_face, target_face, processed_frame)
            _record_swapped_face(target_face, swapped_face_bboxes, swapped_faces)

    final_frame = apply_post_processing(processed_frame, swapped_face_bboxes, swapped_faces)
    return final_frame


def _mapped_targets_for_file(
    map_data: Mapping[str, Any], temp_frame_path: str, target_is_image: bool
) -> list[Any]:
    if target_is_image:
        target_info = map_data.get("target", {})
        target_face = target_info.get("face") if target_info else None
        return [target_face] if target_face else []

    targets: list[Any] = []
    for frame_data in map_data.get("target_faces_in_frame", []):
        if frame_data and frame_data.get("location") == temp_frame_path:
            targets.extend(frame_data.get("faces", []) or [])
    return targets


def _file_source_target_pairs(temp_frame_path: str) -> list[tuple[Any, Any]]:
    source_target_map = getattr(modules.globals, "source_target_map", None)
    if not source_target_map:
        return []

    target_is_image = is_image(modules.globals.target_path)
    if modules.globals.many_faces:
        source_face = default_source_face()
        if not source_face:
            return []
        return [
            (source_face, target_face)
            for map_data in source_target_map
            for target_face in _mapped_targets_for_file(
                map_data, temp_frame_path, target_is_image
            )
        ]

    pairs: list[tuple[Any, Any]] = []
    for map_data in source_target_map:
        source_info = map_data.get("source", {})
        source_face = source_info.get("face") if source_info else None
        if not source_face:
            continue
        pairs.extend(
            (source_face, target_face)
            for target_face in _mapped_targets_for_file(
                map_data, temp_frame_path, target_is_image
            )
        )
    return pairs


def _simple_map_pairs(
    detected_faces: list[Any], simple_map: Mapping[str, Any]
) -> tuple[list[tuple[Any, Any]], bool]:
    source_faces = simple_map.get("source_faces", [])
    target_embeddings = simple_map.get("target_embeddings", [])
    if not source_faces or not target_embeddings:
        return [], False
    if len(source_faces) != len(target_embeddings):
        return [], False

    if len(detected_faces) <= len(target_embeddings):
        pairs = []
        for detected_face in detected_faces:
            if detected_face.normed_embedding is None:
                continue
            closest_idx, _ = find_closest_centroid(
                target_embeddings, detected_face.normed_embedding
            )
            if 0 <= closest_idx < len(source_faces):
                pairs.append((source_faces[closest_idx], detected_face))
        return pairs, False

    detected_with_embedding = [
        face for face in detected_faces if face.normed_embedding is not None
    ]
    if not detected_with_embedding:
        return [], True
    detected_embeddings = [face.normed_embedding for face in detected_with_embedding]
    pairs = []
    for index, target_embedding in enumerate(target_embeddings):
        if index >= len(source_faces):
            continue
        closest_idx, _ = find_closest_centroid(
            detected_embeddings, target_embedding
        )
        if 0 <= closest_idx < len(detected_with_embedding):
            pairs.append((source_faces[index], detected_with_embedding[closest_idx]))
    return pairs, False


def _live_source_target_pairs(
    processed_frame: Frame,
) -> tuple[list[tuple[Any, Any]], bool]:
    detected_faces = get_many_faces(processed_frame)
    if not detected_faces:
        return [], False
    if modules.globals.many_faces:
        source_face = default_source_face()
        pairs = (
            [(source_face, target_face) for target_face in detected_faces]
            if source_face
            else []
        )
        return pairs, False

    simple_map = getattr(modules.globals, "simple_map", None)
    if simple_map:
        return _simple_map_pairs(detected_faces, simple_map)

    source_face = default_source_face()
    target_face = get_one_face(processed_frame, detected_faces)
    pairs = [(source_face, target_face)] if source_face and target_face else []
    return pairs, False


def _swap_source_target_pairs(
    processed_frame: Frame, source_target_pairs: list[tuple[Any, Any]]
) -> Frame:
    swapped_face_bboxes: list[Any] = []
    swapped_faces: list[Any] = []
    current_swap_target = processed_frame.copy()
    for source_face, target_face in source_target_pairs:
        if source_face and target_face:
            current_swap_target = swap_face(
                source_face, target_face, current_swap_target
            )
            _record_swapped_face(
                target_face, swapped_face_bboxes, swapped_faces
            )
    return apply_post_processing(
        current_swap_target, swapped_face_bboxes, swapped_faces
    )


def process_frame_v2(temp_frame: Frame, temp_frame_path: str = "") -> Frame:
    """Handle mapped file targets and live streams without changing swap order."""
    if getattr(modules.globals, "opacity", 1.0) == 0:
        global PREVIOUS_FRAME_RESULT
        PREVIOUS_FRAME_RESULT = None
        return temp_frame

    target_path = modules.globals.target_path
    is_file_target = target_path and (is_image(target_path) or is_video(target_path))
    if is_file_target:
        source_target_pairs = _file_source_target_pairs(temp_frame_path)
        skip_post_processing = False
    else:
        source_target_pairs, skip_post_processing = _live_source_target_pairs(
            temp_frame
        )
    if skip_post_processing:
        return temp_frame
    return _swap_source_target_pairs(temp_frame, source_target_pairs)


def process_frames(
    source_path: str, temp_frame_paths: List[str], progress: Any = None
) -> None:
    """
    Processes a list of frame paths (typically for video).
    Optimized with better memory management and caching.
    Iterates through frames, applies the appropriate swapping logic based on globals,
    and saves the result back to the frame path. Handles multi-threading via caller.
    """
    # Determine which processing function to use based on map_faces global setting
    use_v2 = getattr(modules.globals, "map_faces", False)
    source_face = None # Initialize source_face

    # --- Pre-load source face only if needed (Simple Mode: map_faces=False) ---
    if not use_v2:
        if not source_path or not os.path.exists(source_path):
            update_status(f"Error: Source path invalid or not provided for simple mode: {source_path}", NAME)
            # Log the error but allow proceeding; subsequent check will stop processing.
        else:
            try:
                source_img = read_image(source_path)
                if source_img is None:
                    # Specific error for file reading failure
                    update_status(f"Error reading source image file {source_path}. Please check the path and file integrity.", NAME)
                else:
                    source_face = get_one_face(source_img)
                    if source_face is None:
                        # Specific message for no face detected after successful read
                        update_status(f"Warning: Successfully read source image {source_path}, but no face was detected. Swaps will be skipped.", NAME)
                    # Free memory immediately after extracting face
                    del source_img
            except Exception as e:
                # Print the specific exception caught
                import traceback
                print(f"{NAME}: Caught exception during source image processing for {source_path}:")
                traceback.print_exc() # Print the full traceback
                update_status(f"Error during source image reading or analysis {source_path}: {e}", NAME)
                # Log general exception during the process

    total_frames = len(temp_frame_paths)
    # update_status(f"Processing {total_frames} frames. Use V2 (map_faces): {use_v2}", NAME) # Optional Debug

    # --- Stop processing entirely if in Simple Mode and source face is invalid ---
    if not use_v2 and source_face is None:
        update_status(f"Halting video processing: Invalid or no face detected in source image for simple mode.", NAME)
        if progress:
            # Ensure the progress bar completes if it was started
            remaining_updates = total_frames - progress.n if hasattr(progress, 'n') else total_frames
            if remaining_updates > 0:
                progress.update(remaining_updates)
        return # Exit the function entirely

    # --- Process each frame path provided in the list ---
    # Note: In the current core.py multi_process_frame, temp_frame_paths will usually contain only ONE path per call.
    for i, temp_frame_path in enumerate(temp_frame_paths):
        # update_status(f"Processing frame {i+1}/{total_frames}: {os.path.basename(temp_frame_path)}", NAME) # Optional Debug

        # Read the target frame
        temp_frame = None
        try:
            temp_frame = cv2.imread(temp_frame_path)
            if temp_frame is None:
                print(f"{NAME}: Error: Could not read frame: {temp_frame_path}, skipping.")
                if progress: progress.update(1)
                continue # Skip this frame if read fails
        except Exception as read_e:
            print(f"{NAME}: Error reading frame {temp_frame_path}: {read_e}, skipping.")
            if progress: progress.update(1)
            continue

        # Select processing function and execute
        result_frame = None
        try:
            if use_v2:
                # V2 uses global maps and needs the frame path for lookup in video mode
                # update_status(f"Using process_frame_v2 for: {os.path.basename(temp_frame_path)}", NAME) # Optional Debug
                result_frame = process_frame_v2(temp_frame, temp_frame_path)
            else:
                # Simple mode uses the pre-loaded source_face (already checked for validity above)
                # update_status(f"Using process_frame (simple) for: {os.path.basename(temp_frame_path)}", NAME) # Optional Debug
                result_frame = process_frame(source_face, temp_frame) # source_face is guaranteed to be valid here

            # Check if processing actually returned a frame
            if result_frame is None:
                 print(f"{NAME}: Warning: Processing returned None for frame {temp_frame_path}. Using original.")
                 result_frame = temp_frame

        except Exception as proc_e:
            print(f"{NAME}: Error processing frame {temp_frame_path}: {proc_e}")
            # import traceback # Optional for detailed debugging
            # traceback.print_exc()
            result_frame = temp_frame # Use original frame on processing error

        # Write the result back to the same frame path with optimized compression
        try:
            # Use PNG compression level 3 (faster) instead of default 9
            write_success = cv2.imwrite(temp_frame_path, result_frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            if not write_success:
                print(f"{NAME}: Error: Failed to write processed frame to {temp_frame_path}")
        except Exception as write_e:
            print(f"{NAME}: Error writing frame {temp_frame_path}: {write_e}")
        
        # Free memory immediately after processing
        del temp_frame
        if result_frame is not None:
            del result_frame

        # Update progress bar
        if progress:
            progress.update(1)
        # else: # Basic console progress (optional)
        #     if (i + 1) % 10 == 0 or (i + 1) == total_frames: # Update every 10 frames or on last frame
        #        update_status(f"Processed frame {i+1}/{total_frames}", NAME)


def process_image(source_path: str, target_path: str, output_path: str) -> bool:
    """Processes a single target image."""
    # --- Reset interpolation state for single image processing ---
    global PREVIOUS_FRAME_RESULT
    PREVIOUS_FRAME_RESULT = None
    # ---

    use_v2 = getattr(modules.globals, "map_faces", False)

    # Read target first
    try:
        target_frame = read_image(target_path)
        if target_frame is None:
            update_status(f"Error: Could not read target image: {target_path}", NAME)
            return False
    except Exception as read_e:
        update_status(f"Error reading target image {target_path}: {read_e}", NAME)
        return False

    result = None
    try:
        if use_v2:
            if getattr(modules.globals, "many_faces", False):
                 update_status("Processing image with 'map_faces' and 'many_faces'. Using pre-analysis map.", NAME)
            # V2 processes based on global maps, doesn't need source_path here directly
            # Assumes maps are pre-populated. Pass target_path for map lookup.
            result = process_frame_v2(target_frame, target_path)

        else: # Simple mode
            try:
                source_img = read_image(source_path)
                if source_img is None:
                    update_status(f"Error: Could not read source image: {source_path}", NAME)
                    return False
                source_face = get_one_face(source_img)
                if not source_face:
                    update_status(f"Error: No face found in source image: {source_path}", NAME)
                    return False
            except Exception as src_e:
                 update_status(f"Error reading or analyzing source image {source_path}: {src_e}", NAME)
                 return False

            result = process_frame(source_face, target_frame)

        # Write the result if processing was successful
        if result is not None:
            write_success = cv2.imwrite(output_path, result)
            if write_success:
                update_status(f"Output image saved to: {output_path}", NAME)
                return True
            else:
                update_status(f"Error: Failed to write output image to {output_path}", NAME)
        else:
            # This case might occur if process_frame/v2 returns None unexpectedly
            update_status("Image processing failed (result was None).", NAME)

    except Exception as proc_e:
         update_status(f"Error during image processing: {proc_e}", NAME)
         # import traceback
         # traceback.print_exc()
    return False


def process_video(source_path: str, temp_frame_paths: List[str]) -> None:
    """Sets up and calls the frame processing for video."""
    # --- Reset interpolation state before starting video processing ---
    global PREVIOUS_FRAME_RESULT
    PREVIOUS_FRAME_RESULT = None
    # ---

    mode_desc = "'map_faces'" if getattr(modules.globals, "map_faces", False) else "'simple'"
    if getattr(modules.globals, "map_faces", False) and getattr(modules.globals, "many_faces", False):
        mode_desc += " and 'many_faces'. Using pre-analysis map."
    update_status(f"Processing video with {mode_desc} mode.", NAME)

    # Pass the correct source_path (needed for simple mode in process_frames)
    # The core processing logic handles calling the right frame function (process_frames)
    modules.processors.frame.core.process_video(
        source_path, temp_frame_paths, process_frames # Pass the newly modified process_frames
    )

# ==========================
# MASKING FUNCTIONS (Mostly unchanged, added safety checks and minor improvements)
# ==========================

def create_lower_mouth_mask(
    face: Face, frame: Frame
) -> (np.ndarray, np.ndarray, tuple, np.ndarray):
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    mouth_cutout = None
    lower_lip_polygon = None # Initialize
    mouth_box = (0,0,0,0) # Initialize

    # Validate face and landmarks
    if face is None or not hasattr(face, 'landmark_2d_106'):
        # print("Warning: Invalid face object passed to create_lower_mouth_mask.")
        return mask, mouth_cutout, mouth_box, lower_lip_polygon

    landmarks = face.landmark_2d_106

    # Check landmark validity
    if landmarks is None or not isinstance(landmarks, np.ndarray) or landmarks.shape[0] < 106:
        # print("Warning: Invalid or insufficient landmarks for mouth mask.")
        return mask, mouth_cutout, mouth_box, lower_lip_polygon

    mouth_min_confidence = float(
        getattr(modules.globals, "expression_mouth_min_confidence", 0.0) or 0.0
    )
    if mouth_min_confidence > 0.0:
        mouth_confidence = compute_mouth_region_confidence(face)
        if mouth_confidence < mouth_min_confidence:
            return mask, mouth_cutout, mouth_box, lower_lip_polygon

    try: # Wrap main logic in try-except
        # Use outer mouth landmarks (52-71) to capture the full mouth area
        # This covers both upper and lower lips for proper mouth preservation
        lower_lip_order = list(MOUTH_OUTER_INDICES)

        # Check if all indices are valid for the loaded landmarks (already partially done by < 106 check)
        if max(lower_lip_order) >= landmarks.shape[0]:
            # print(f"Warning: Landmark index {max(lower_lip_order)} out of bounds for shape {landmarks.shape[0]}.")
            return mask, mouth_cutout, mouth_box, lower_lip_polygon

        lower_lip_landmarks = landmarks[lower_lip_order].astype(np.float32)

        # Filter out potential NaN or Inf values in landmarks
        if not np.all(np.isfinite(lower_lip_landmarks)):
            # print("Warning: Non-finite values detected in lower lip landmarks.")
            return mask, mouth_cutout, mouth_box, lower_lip_polygon

        center = np.mean(lower_lip_landmarks, axis=0)
        if not np.all(np.isfinite(center)): # Check center calculation
            # print("Warning: Could not calculate valid center for mouth mask.")
            return mask, mouth_cutout, mouth_box, lower_lip_polygon


        mouth_mask_size = getattr(modules.globals, "mouth_mask_size", 0.0) # 0-100 slider
        # 0=tight lip outline, 50=covers mouth area, 100=mouth to chin
        expansion_factor = 1 + (mouth_mask_size / 100.0) * 2.5

        # Expand landmarks from center, with extra downward bias toward chin
        offsets = lower_lip_landmarks - center
        # Add extra downward expansion for points below center (toward chin)
        chin_bias = 1 + (mouth_mask_size / 100.0) * 1.5  # extra vertical stretch downward
        scale_y = np.where(offsets[:, 1] > 0, expansion_factor * chin_bias, expansion_factor)
        expanded_landmarks = lower_lip_landmarks.copy()
        expanded_landmarks[:, 0] = center[0] + offsets[:, 0] * expansion_factor
        expanded_landmarks[:, 1] = center[1] + offsets[:, 1] * scale_y

        # Ensure landmarks are finite after adjustments
        if not np.all(np.isfinite(expanded_landmarks)):
            # print("Warning: Non-finite values detected after expanding landmarks.")
            return mask, mouth_cutout, mouth_box, lower_lip_polygon

        expanded_landmarks = _smooth_mouth_mask_landmarks(
            face,
            expanded_landmarks,
        ).astype(np.int32)

        min_x, min_y = np.min(expanded_landmarks, axis=0)
        max_x, max_y = np.max(expanded_landmarks, axis=0)

        # Add padding *after* initial min/max calculation
        padding_ratio = 0.1 # Percentage padding
        padding_x = int((max_x - min_x) * padding_ratio)
        padding_y = int((max_y - min_y) * padding_ratio) # Use y-range for y-padding

        # Apply padding and clamp to frame boundaries
        frame_h, frame_w = frame.shape[:2]
        min_x = max(0, min_x - padding_x)
        min_y = max(0, min_y - padding_y)
        max_x = min(frame_w, max_x + padding_x)
        max_y = min(frame_h, max_y + padding_y)


        if max_x > min_x and max_y > min_y:
            # Create the mask ROI
            mask_roi_h = max_y - min_y
            mask_roi_w = max_x - min_x
            mask_roi = np.zeros((mask_roi_h, mask_roi_w), dtype=np.uint8)

            # Shift polygon coordinates relative to the ROI's top-left corner
            polygon_relative_to_roi = expanded_landmarks - [min_x, min_y]

            # Draw polygon on the ROI mask
            cv2.fillPoly(mask_roi, [polygon_relative_to_roi], 255)

            # Apply Gaussian blur (GPU-accelerated when available)
            blur_k_size = getattr(modules.globals, "mask_blur_kernel", 15) # Default 15
            blur_k_size = max(1, blur_k_size // 2 * 2 + 1) # Ensure odd
            mask_roi = gpu_gaussian_blur(mask_roi, (blur_k_size, blur_k_size), 0)

            # Place the mask ROI in the full-sized mask
            mask[min_y:max_y, min_x:max_x] = mask_roi

            # Extract the masked area from the *original* frame
            mouth_cutout = frame[min_y:max_y, min_x:max_x].copy()

            lower_lip_polygon = expanded_landmarks # Return polygon in original frame coords
            mouth_box = (min_x, min_y, max_x, max_y) # Return the calculated box
        else:
            # print("Warning: Invalid mouth mask bounding box after padding/clamping.") # Optional debug
            pass

    except IndexError:
        pass
    except Exception as exc:
        print(f"Error in create_lower_mouth_mask: {exc}")

    # Return values, ensuring defaults if errors occurred
    return mask, mouth_cutout, mouth_box, lower_lip_polygon


def draw_mouth_mask_visualization(
    frame: Frame, face: Face, mouth_mask_data: tuple
) -> Frame:

    # Validate inputs
    if frame is None or face is None or mouth_mask_data is None or len(mouth_mask_data) != 4:
        return frame # Return original frame if inputs are invalid

    mask, mouth_cutout, box, lower_lip_polygon = mouth_mask_data
    (min_x, min_y, max_x, max_y) = box

    # Check if polygon is valid for drawing
    if lower_lip_polygon is None or not isinstance(lower_lip_polygon, np.ndarray) or len(lower_lip_polygon) < 3:
        return frame # Cannot draw without a valid polygon

    vis_frame = frame.copy()
    height, width = vis_frame.shape[:2]

    # Ensure box coordinates are valid integers within frame bounds
    try:
        min_x, min_y = max(0, int(min_x)), max(0, int(min_y))
        max_x, max_y = min(width, int(max_x)), min(height, int(max_y))
    except ValueError:
        # print("Warning: Invalid coordinates for mask visualization box.")
        return frame

    if max_x <= min_x or max_y <= min_y:
        return frame # Invalid box

    # Draw the lower lip polygon (green outline)
    try:
         # Ensure polygon points are within frame boundaries before drawing
         safe_polygon = lower_lip_polygon.copy()
         safe_polygon[:, 0] = np.clip(safe_polygon[:, 0], 0, width - 1)
         safe_polygon[:, 1] = np.clip(safe_polygon[:, 1], 0, height - 1)
         cv2.polylines(vis_frame, [safe_polygon.astype(np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)
    except Exception as e:
        print(f"Error drawing polygon for visualization: {e}") # Optional debug
        pass

    # Draw bounding box (red rectangle)
    cv2.rectangle(vis_frame, (min_x, min_y), (max_x, max_y), (0, 0, 255), 2)

    # Optional: Add labels
    label_pos_y = min_y - 10 if min_y > 20 else max_y + 15 # Adjust position based on box location
    label_pos_x = min_x
    try:
        cv2.putText(vis_frame, "Mouth Mask", (label_pos_x, label_pos_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
    except Exception:
        pass


    return vis_frame


def apply_mouth_area(
    frame: np.ndarray,
    mouth_cutout: np.ndarray,
    mouth_box: tuple,
    face_mask: np.ndarray, # Full face mask (for blending edges)
    mouth_polygon: np.ndarray, # Specific polygon for the mouth area itself
) -> np.ndarray:

    # Basic validation
    if (frame is None or mouth_cutout is None or mouth_box is None or
        face_mask is None or mouth_polygon is None):
        # print("Warning: Invalid input (None value) to apply_mouth_area") # Optional debug
        return frame
    if (mouth_cutout.size == 0 or face_mask.size == 0 or len(mouth_polygon) < 3):
        # print("Warning: Invalid input (empty array/polygon) to apply_mouth_area") # Optional debug
        return frame

    try: # Wrap main logic in try-except
        min_x, min_y, max_x, max_y = map(int, mouth_box) # Ensure integer coords
        box_width = max_x - min_x
        box_height = max_y - min_y

        # Check box validity
        if box_width <= 0 or box_height <= 0:
            # print("Warning: Invalid mouth box dimensions in apply_mouth_area.")
            return frame

        # Define the Region of Interest (ROI) on the target frame (swapped frame)
        frame_h, frame_w = frame.shape[:2]
        # Clamp coordinates strictly within frame boundaries
        min_y, max_y = max(0, min_y), min(frame_h, max_y)
        min_x, max_x = max(0, min_x), min(frame_w, max_x)

        # Recalculate box dimensions based on clamped coords
        box_width = max_x - min_x
        box_height = max_y - min_y
        if box_width <= 0 or box_height <= 0:
            # print("Warning: ROI became invalid after clamping in apply_mouth_area.")
            return frame # ROI is invalid

        roi = frame[min_y:max_y, min_x:max_x]

        # Ensure ROI extraction was successful
        if roi.size == 0:
            # print("Warning: Extracted ROI is empty in apply_mouth_area.")
            return frame

        # Resize mouth cutout from original frame to fit the ROI size
        resized_mouth_cutout = None
        if roi.shape[:2] != mouth_cutout.shape[:2]:
             # Check if mouth_cutout has valid dimensions before resizing
             if mouth_cutout.shape[0] > 0 and mouth_cutout.shape[1] > 0:
                  resized_mouth_cutout = gpu_resize(mouth_cutout, (box_width, box_height), interpolation=cv2.INTER_LINEAR)
             else:
                 # print("Warning: mouth_cutout has invalid dimensions, cannot resize.")
                 return frame # Cannot proceed without valid cutout
        else:
             resized_mouth_cutout = mouth_cutout

        # If resize failed or original was invalid
        if resized_mouth_cutout is None or resized_mouth_cutout.size == 0:
            # print("Warning: Mouth cutout is invalid after resize attempt.")
            return frame

        # --- Mask Creation ---
        # Create a mask based on the mouth_polygon, relative to the ROI
        polygon_mask_roi = np.zeros(roi.shape[:2], dtype=np.uint8)
        adjusted_polygon = mouth_polygon - [min_x, min_y]
        cv2.fillPoly(polygon_mask_roi, [adjusted_polygon.astype(np.int32)], 255)

        # Feather the edges with Gaussian blur for smooth blending
        feather_amount = max(1, min(30, min(box_width, box_height) // 8))
        kernel_size = 2 * feather_amount + 1
        feathered_mask = cv2.GaussianBlur(polygon_mask_roi.astype(np.float32), (kernel_size, kernel_size), 0)

        # Normalize to [0.0, 1.0]
        max_val = feathered_mask.max()
        if max_val > 1e-6:
            feathered_mask = feathered_mask / max_val
        else:
            feathered_mask.fill(0.0)

        # --- Blending: paste original mouth onto swapped face ---
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            mask_3ch = feathered_mask[:, :, np.newaxis].astype(np.float32)
            inv_mask = 1.0 - mask_3ch

            # Blend: (original_mouth * mask) + (swapped_face * (1 - mask))
            blended_roi = (resized_mouth_cutout.astype(np.float32) * mask_3ch +
                           roi.astype(np.float32) * inv_mask)

            frame[min_y:max_y, min_x:max_x] = np.clip(blended_roi, 0, 255).astype(np.uint8)

    except Exception as e:
        print(f"Error applying mouth area: {e}") # Optional debug
        # import traceback
        # traceback.print_exc()
        pass # Don't crash, just return the frame as is

    return frame


def create_face_mask(
    face: Face,
    frame: Frame,
    *,
    extended_subject: bool | None = None,
    hairline_ratio: float | None = None,
    side_ratio: float | None = None,
    shoulder_ratio: float | None = None,
    chest_ratio: float | None = None,
) -> np.ndarray:
    """Creates a feathered mask covering the whole face area based on landmarks."""
    if frame is None or not hasattr(frame, "shape") or len(frame.shape) < 2:
        return np.zeros((0, 0), dtype=np.uint8)

    mask = np.zeros(frame.shape[:2], dtype=np.uint8) # Start with uint8

    landmarks = _face_array(face, "landmark_2d_106")
    if landmarks is None or landmarks.shape[0] < 106:
        # print("Warning: Invalid or insufficient landmarks for face mask.")
        return mask # Return empty mask

    try: # Wrap main logic in try-except
        # Filter out non-finite landmark values
        if not np.all(np.isfinite(landmarks)):
            # print("Warning: Non-finite values detected in landmarks for face mask.")
            return mask

        landmarks_int = landmarks.astype(np.int32)

        # Use standard face outline landmarks (0-32)
        # Use standard face outline (0-32)
        face_outline = landmarks_int[0:33]
        if extended_subject is None:
            extended_subject = getattr(
                modules.globals,
                "compositing_extended_subject_mask",
                False,
            )

        # Estimate forehead points to ensure mask covers the whole face (including forehead)
        # This is critical for Poisson blending to work correctly on the forehead
        eyebrows = landmarks_int[33:43]
        if eyebrows.shape[0] > 0:
            chin = landmarks_int[16]
            eyebrow_center = np.mean(eyebrows, axis=0)
            
            # Vector from chin to eyebrows (upwards)
            up_vector = eyebrow_center - chin
            norm = np.linalg.norm(up_vector)
            if norm > 0:
                up_vector /= norm
                
                # Extend upwards by 1.0 of the chin-to-eyebrow distance (aggressive coverage)
                # This ensures the mask covers the entire forehead for proper blending
                forehead_offset = up_vector * (norm * 1.0)
                
                # Shift eyebrows up to create forehead points
                forehead_points = eyebrows + forehead_offset
                
                # Expand the top points slightly outwards to cover forehead corners
                # Calculate the center of the new top points
                top_center = np.mean(forehead_points, axis=0)
                
                # Expand outwards by 20%
                forehead_points = (forehead_points - top_center) * 1.2 + top_center
                
                # Combine outline and forehead points
                face_outline = np.concatenate((face_outline, forehead_points.astype(np.int32)), axis=0)

        # Calculate convex hull of these points
        # Use try-except as convexHull can fail on degenerate input
        try:
             hull = cv2.convexHull(face_outline.astype(np.float32)) # Use float for accuracy
             if hull is None or len(hull) < 3:
                 # print("Warning: Convex hull calculation failed or returned too few points.")
                 # Fallback: use bounding box of landmarks? Or just return empty mask?
                 return mask

             # Draw the filled convex hull on the mask
             cv2.fillConvexPoly(mask, hull.astype(np.int32), 255)
        except Exception as hull_e:
             print(f"Error creating convex hull for face mask: {hull_e}")
             return mask # Return empty mask on error

        if extended_subject:
            face_bbox = _face_bbox(face)
            mask, _points = create_extended_subject_mask(
                face_outline.astype(np.float32),
                bbox=(
                    tuple(float(value) for value in face_bbox.tolist())
                    if face_bbox is not None
                    else None
                ),
                frame_shape=frame.shape,
                base_mask=mask,
                hairline_ratio=(
                    getattr(
                        modules.globals,
                        "compositing_extended_subject_hairline_ratio",
                        0.32,
                    )
                    if hairline_ratio is None
                    else hairline_ratio
                ),
                side_ratio=(
                    getattr(
                        modules.globals,
                        "compositing_extended_subject_side_ratio",
                        0.24,
                    )
                    if side_ratio is None
                    else side_ratio
                ),
                shoulder_ratio=(
                    getattr(
                        modules.globals,
                        "compositing_extended_subject_shoulder_ratio",
                        0.48,
                    )
                    if shoulder_ratio is None
                    else shoulder_ratio
                ),
                chest_ratio=(
                    getattr(
                        modules.globals,
                        "compositing_extended_subject_chest_ratio",
                        0.58,
                    )
                    if chest_ratio is None
                    else chest_ratio
                ),
            )


        # Apply Gaussian blur to feather the mask edges (GPU-accelerated when available)
        blur_k_size = getattr(modules.globals, "face_mask_blur", 31) # Default 31
        blur_k_size = max(1, blur_k_size // 2 * 2 + 1) # Ensure odd and positive
        mask = gpu_gaussian_blur(mask, (blur_k_size, blur_k_size), 0)

        # --- Optional: Return float mask for apply_mouth_area ---
        # mask = mask.astype(float) / 255.0
        # ---

    except IndexError:
        # print("Warning: Landmark index out of bounds for face mask.") # Optional debug
        pass
    except Exception as e:
        print(f"Error creating face mask: {e}") # Print unexpected errors
        # import traceback
        # traceback.print_exc()
        pass

    return mask # Return uint8 mask


def apply_color_transfer(source, target):
    """
    Apply color transfer using LAB color space. Handles potential division by zero and ensures output is uint8.
    """
    # Input validation
    if source is None or target is None or source.size == 0 or target.size == 0:
        # print("Warning: Invalid input to apply_color_transfer.")
        return source # Return original source if invalid input

    # Ensure images are 3-channel BGR uint8
    if len(source.shape) != 3 or source.shape[2] != 3 or source.dtype != np.uint8:
        # print("Warning: Source image for color transfer is not uint8 BGR.")
        # Attempt conversion if possible, otherwise return original
        try:
            if len(source.shape) == 2: # Grayscale
                source = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
            source = np.clip(source, 0, 255).astype(np.uint8)
            if len(source.shape)!= 3 or source.shape[2]!= 3: raise ValueError("Conversion failed")
        except Exception:
            return source
    if len(target.shape) != 3 or target.shape[2] != 3 or target.dtype != np.uint8:
        # print("Warning: Target image for color transfer is not uint8 BGR.")
        try:
            if len(target.shape) == 2: # Grayscale
                target = cv2.cvtColor(target, cv2.COLOR_GRAY2BGR)
            target = np.clip(target, 0, 255).astype(np.uint8)
            if len(target.shape)!= 3 or target.shape[2]!= 3: raise ValueError("Conversion failed")
        except Exception:
             return source # Return original source if target invalid

    result_bgr = source # Default to original source in case of errors

    try:
        # Convert to float32 [0, 1] range for LAB conversion
        source_float = source.astype(np.float32) / 255.0
        target_float = target.astype(np.float32) / 255.0

        source_lab = cv2.cvtColor(source_float, cv2.COLOR_BGR2LAB)
        target_lab = cv2.cvtColor(target_float, cv2.COLOR_BGR2LAB)

        # Compute statistics
        source_mean, source_std = cv2.meanStdDev(source_lab)
        target_mean, target_std = cv2.meanStdDev(target_lab)

        # Reshape for broadcasting
        source_mean = source_mean.reshape((1, 1, 3))
        source_std = source_std.reshape((1, 1, 3))
        target_mean = target_mean.reshape((1, 1, 3))
        target_std = target_std.reshape((1, 1, 3))

        # Avoid division by zero or very small std deviations (add epsilon)
        epsilon = 1e-6
        source_std = np.maximum(source_std, epsilon)
        # target_std = np.maximum(target_std, epsilon) # Target std can be small

        # Perform color transfer in LAB space
        result_lab = (source_lab - source_mean) * (target_std / source_std) + target_mean

        # --- No explicit clipping needed in LAB space typically ---
        # Clipping is handled implicitly by the conversion back to BGR and then to uint8

        # Convert back to BGR float [0, 1]
        result_bgr_float = cv2.cvtColor(result_lab, cv2.COLOR_LAB2BGR)

        # Clip final BGR values to [0, 1] range before scaling to [0, 255]
        result_bgr_float = np.clip(result_bgr_float, 0.0, 1.0)

        # Convert back to uint8 [0, 255]
        result_bgr = (result_bgr_float * 255.0).astype("uint8")

    except cv2.error:
        return source # Return original source if conversion fails
    except Exception:
        return source

    return result_bgr
