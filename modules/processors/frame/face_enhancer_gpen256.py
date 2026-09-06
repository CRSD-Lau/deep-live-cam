"""GPEN-BFR-256 face enhancer — ONNX-based face restoration at 256x256."""

from typing import Any, List
import os
import threading

import modules.globals
import modules.processors.frame.core
from modules.core import update_status
from modules.face_analyser import get_one_face
from modules.typing import Frame, Face
from modules.utilities import (
    is_image,
    is_video,
    read_image,
    write_image,
)
from modules.processors.frame._onnx_enhancer import (
    create_onnx_session,
    warmup_session,
    enhance_face_onnx,
)
from modules.paths import MODELS_DIR

NAME = "DLC.FACE-ENHANCER-GPEN256"
INPUT_SIZE = 256
MODEL_URL = "https://huggingface.co/netrunner-exe/Face-Upscalers-onnx/resolve/main/GPEN-BFR-256.onnx"
MODEL_FILE = "GPEN-BFR-256.onnx"

ENHANCER = None
THREAD_LOCK = threading.Lock()
DOWNLOAD_ATTEMPTED = False
MODEL_UNAVAILABLE_REASON = None

models_dir = MODELS_DIR


def pre_check() -> bool:
    return ensure_model_available()


def ensure_model_available() -> bool:
    global DOWNLOAD_ATTEMPTED, MODEL_UNAVAILABLE_REASON

    model_path = os.path.join(models_dir, MODEL_FILE)
    if os.path.exists(model_path):
        return True

    MODEL_UNAVAILABLE_REASON = MODEL_UNAVAILABLE_REASON or (
        f"{MODEL_FILE} was not found in {models_dir}. "
        "Run DeepLiveCamStudioCLI.exe --download-models after reviewing model licenses, "
        "or select Face Enhancer: None."
    )
    update_status(MODEL_UNAVAILABLE_REASON, NAME)
    modules.globals.fp_ui["face_enhancer_gpen256"] = False
    return False


def pre_start() -> bool:
    if not is_image(modules.globals.target_path) and not is_video(modules.globals.target_path):
        update_status("Select an image or video for target path.", NAME)
        return False
    return True


def get_enhancer() -> Any:
    global ENHANCER
    with THREAD_LOCK:
        if ENHANCER is None:
            model_path = os.path.join(models_dir, MODEL_FILE)
            if not ensure_model_available():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            print(f"{NAME}: Loading ONNX model from {model_path}")
            ENHANCER = create_onnx_session(model_path)
            warmup_session(ENHANCER)
            print(f"{NAME}: Model loaded successfully.")
    return ENHANCER


def enhance_face(temp_frame: Frame, face: Face) -> Frame:
    try:
        session = get_enhancer()
    except Exception as e:
        print(f"{NAME}: {e}")
        return temp_frame
    try:
        return enhance_face_onnx(temp_frame, face, session, INPUT_SIZE)
    except Exception as e:
        print(f"{NAME}: Error during face enhancement: {e}")
        return temp_frame


def process_frame(source_face: Face | None, temp_frame: Frame, detected_faces=None) -> Frame:
    if detected_faces:
        target_face = detected_faces[0]
    else:
        target_face = get_one_face(temp_frame)
    if target_face is None:
        return temp_frame
    return enhance_face(temp_frame, target_face)


def process_frame_v2(temp_frame: Frame) -> Frame:
    target_face = get_one_face(temp_frame)
    if target_face:
        temp_frame = enhance_face(temp_frame, target_face)
    return temp_frame


def process_frames(
    source_path: str | None, temp_frame_paths: List[str], progress: Any = None
) -> None:
    for temp_frame_path in temp_frame_paths:
        temp_frame = read_image(temp_frame_path)
        if temp_frame is None:
            if progress:
                progress.update(1)
            continue
        result = process_frame(None, temp_frame)
        write_image(temp_frame_path, result)
        if progress:
            progress.update(1)


def process_image(source_path: str | None, target_path: str, output_path: str) -> bool:
    target_frame = read_image(target_path)
    if target_frame is None:
        print(f"{NAME}: Error: Failed to read target image {target_path}")
        return False
    result_frame = process_frame(None, target_frame)
    if result_frame is None or not write_image(output_path, result_frame):
        print(f"{NAME}: Error: Failed to write output image {output_path}")
        return False
    print(f"{NAME}: Enhanced image saved to {output_path}")
    return True


def process_video(source_path: str | None, temp_frame_paths: List[str]) -> None:
    modules.processors.frame.core.process_video(source_path, temp_frame_paths, process_frames)
