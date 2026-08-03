"""PySide6 UI for Deep-Live-Cam.

Public API kept stable for the rest of the codebase:
    init(start, destroy) -> _Window
        Returned object has .mainloop() that core.py calls.
    update_status(text)
        Thread-safe; routed through Qt signal when called off-UI.
    check_and_ignore_nsfw(target, destroy=None) -> bool
"""

from __future__ import annotations

import inspect
import os
import platform
import queue
import sys
import threading
import time
import traceback
import webbrowser
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps
from PySide6.QtCore import (
    QEventLoop,
    QObject,
    QThread,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import modules.globals
import modules.metadata
from modules.capturer import get_video_frame, get_video_frame_total
from modules.enhancement_registry import (
    ENHANCER_KEYS,
    active_enhancer_key,
    default_enhancer_state,
    enhancer_key_for_processor_name,
    get_enhancer_choices,
)
from modules.execution_providers import provider_config_summary
from modules.gpu_processing import gpu_cvt_color, gpu_flip, gpu_resize
from modules.live_queue import get_latest, put_latest
from modules.pipeline_metrics import (
    MetricsJsonlWriter,
    PipelineMetrics,
    format_metrics,
    safe_write_metrics_snapshot,
)
from modules.quality_profiles import (
    QUALITY_MODE_NAMES,
    apply_quality_profile,
    get_quality_profile,
    quality_profile_runtime_state,
    restore_quality_profile_runtime_state,
)
from modules.tracking.face_track import FaceTracker
from modules.utilities import (
    IMAGE_FILE_FILTER,
    MEDIA_FILE_FILTER,
    has_image_extension,
    is_image,
    is_video,
    read_image,
)
from modules.video_capture import VideoCapturer
from modules.paths import install_root, resource_root, user_data_dir
from runtime.virtual_cam import VirtualCameraSink

if platform.system() == "Windows":
    from pygrabber.dshow_graph import FilterGraph

import json


# ─── constants ────────────────────────────────────────────────────────────

ROOT_HEIGHT = 900
ROOT_WIDTH = 1500

PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH = 1200
PREVIEW_DEFAULT_WIDTH = 640
PREVIEW_DEFAULT_HEIGHT = 360

POPUP_WIDTH = 750
POPUP_HEIGHT = 810
POPUP_SCROLL_WIDTH = 720
POPUP_SCROLL_HEIGHT = 700

POPUP_LIVE_WIDTH = 900
POPUP_LIVE_HEIGHT = 820
POPUP_LIVE_SCROLL_WIDTH = 870
POPUP_LIVE_SCROLL_HEIGHT = 700

MAPPER_PREVIEW_SIZE = 100
SOURCE_TARGET_PREVIEW_SIZE = 240
MEDIA_SLOT_HEIGHT = 390
MEDIA_ACTION_WIDTH = SOURCE_TARGET_PREVIEW_SIZE
APP_LOGO_NAME = "Logo.png"


def app_logo_path() -> str:
    for base in (resource_root(), install_root()):
        candidate = base / APP_LOGO_NAME
        if candidate.exists():
            return str(candidate)
    return ""


def app_icon() -> QIcon:
    logo = app_logo_path()
    if logo:
        return QIcon(logo)
    return QIcon()


# ─── modern dark stylesheet ───────────────────────────────────────────────

QSS = """
QMainWindow, QDialog {
    background-color: #171715;
    color: #ece8df;
}
QWidget {
    color: #ece8df;
    font-family: "Segoe UI";
    font-size: 10.5pt;
}

QFrame#studioHeader {
    background-color: #22211e;
    border: 1px solid #39352f;
    border-radius: 8px;
}
QLabel#titleLabel {
    color: #f4efe5;
    font-size: 19pt;
    font-weight: 700;
}
QLabel#subtitleLabel {
    color: #b9b0a3;
    font-size: 9.5pt;
}
QLabel#pillLabel {
    background-color: #2d2b27;
    border: 1px solid #4a443a;
    border-radius: 8px;
    color: #d8c9b3;
    padding: 5px 10px;
    font-size: 9pt;
    font-weight: 600;
}

QGroupBox {
    background-color: #22211e;
    border: 1px solid #39352f;
    border-radius: 8px;
    margin-top: 20px;
    padding: 20px 16px 16px 16px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 2px 10px;
    background-color: #171715;
    border-radius: 5px;
    color: #d9b06d;
}

QPushButton {
    background-color: #c58a3a;
    color: #181510;
    border: 1px solid #d6a45a;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 700;
}
QPushButton:hover  { background-color: #d49a4c; }
QPushButton:pressed{ background-color: #aa752f; }
QPushButton:disabled {
    background-color: #393631;
    border-color: #393631;
    color: #7f786d;
}
QPushButton#secondary {
    background-color: #2d3332;
    border-color: #43504d;
    color: #d7e6e2;
}
QPushButton#secondary:hover { background-color: #37403e; }
QPushButton#danger {
    background-color: #5c2722;
    border-color: #8e4037;
    color: #f3ddd8;
}
QPushButton#danger:hover  { background-color: #723129; }

QComboBox {
    background-color: #1b1b19;
    border: 1px solid #454138;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 24px;
}
QComboBox:hover { border-color: #c58a3a; }
QComboBox QAbstractItemView {
    background-color: #22211e;
    selection-background-color: #725126;
    border: 1px solid #454138;
}

QCheckBox {
    spacing: 8px;
    padding: 3px 0;
}
QCheckBox::indicator {
    width: 34px; height: 18px;
    border-radius: 8px;
    background-color: #3b3833;
    border: 1px solid #4e493f;
}
QCheckBox::indicator:checked {
    background-color: #c58a3a;
    border-color: #d6a45a;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #383530;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #efe5d4;
    width: 16px; height: 16px;
    margin: -5px 0;
    border-radius: 8px;
    border: 1px solid #c58a3a;
}
QSlider::sub-page:horizontal {
    background: #c58a3a;
    border-radius: 3px;
}

QLabel#mediaTitle {
    color: #efe1c3;
    font-size: 9.5pt;
    font-weight: 700;
}
QLabel#mediaHint {
    color: #8f8577;
    font-size: 8.5pt;
}
QFrame#mediaSlot {
    background-color: #1c1b18;
    border: 1px solid #38342e;
    border-radius: 8px;
}
QLabel#imageDrop {
    background-color: #151512;
    border: 1px dashed #5b5347;
    border-radius: 6px;
    color: #8f8577;
    font-weight: 600;
}
QLabel#statusLabel {
    color: #c8c0b4;
    font-size: 10pt;
}
QLabel#linkLabel {
    color: #d9b06d;
}

QStatusBar {
    background-color: #171715;
    color: #9f9689;
}
QScrollArea { border: none; background: transparent; }
"""


# ─── module-level state ───────────────────────────────────────────────────

_APP: Optional[QApplication] = None
_MAIN: Optional["MainWindow"] = None
_PREVIEW: Optional["PreviewWindow"] = None
_WEBCAM_PREVIEW: Optional["WebcamPreviewWindow"] = None
_MAPPER: Optional["MapperDialog"] = None
_LIVE_MAPPER: Optional["LiveMapperDialog"] = None
_BRIDGE: Optional["_UIBridge"] = None


def _(text: str) -> str:
    """Return UI text."""
    return text


def _destroy_without_quit(destroy_cb: Callable) -> None:
    accepts_to_quit = False
    try:
        signature = inspect.signature(destroy_cb)
        accepts_to_quit = (
            "to_quit" in signature.parameters
            or any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values())
        )
    except (TypeError, ValueError):
        accepts_to_quit = False

    try:
        if accepts_to_quit:
            destroy_cb(to_quit=False)
        else:
            destroy_cb()
    except SystemExit:
        pass


# Preserve original cwd state for file dialogs.
_RECENT_SOURCE_DIR: Optional[str] = None
_RECENT_TARGET_DIR: Optional[str] = None
_RECENT_OUTPUT_DIR: Optional[str] = None


# ─── image utilities ─────────────────────────────────────────────────────


def fit_image_to_size(image, width: int, height: int):
    """BGR ndarray → BGR ndarray scaled to fit within (width, height)."""
    if width is None and height is None or width <= 0 or height <= 0:
        return image
    h, w = image.shape[:2]
    ratio_w = width / w
    ratio_h = height / h
    ratio = min(ratio_w, ratio_h)
    new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
    return gpu_resize(image, dsize=new_size)


def _bgr_to_qpixmap(bgr: np.ndarray) -> QPixmap:
    """Zero-copy BGR ndarray → QPixmap."""
    h, w = bgr.shape[:2]
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    qimg = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


def _pil_to_qpixmap(image: Image.Image) -> QPixmap:
    """PIL.Image → QPixmap."""
    image = image.convert("RGBA")
    data = image.tobytes("raw", "RGBA")
    qimg = QImage(data, image.width, image.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg.copy())


def render_image_preview(image_path: str, size: Tuple[int, int]) -> QPixmap:
    image = Image.open(image_path)
    if size:
        image = ImageOps.fit(image, size, Image.LANCZOS)
    return _pil_to_qpixmap(image)


def render_video_preview(
    video_path: str, size: Tuple[int, int], frame_number: int = 0
) -> Optional[QPixmap]:
    capture = cv2.VideoCapture(video_path)
    try:
        if frame_number:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        has_frame, frame = capture.read()
        if not has_frame:
            return None
        image = Image.fromarray(gpu_cvt_color(frame, cv2.COLOR_BGR2RGB))
        if size:
            image = ImageOps.fit(image, size, Image.LANCZOS)
        return _pil_to_qpixmap(image)
    finally:
        capture.release()


# ─── persistence ─────────────────────────────────────────────────────────


def _switch_state_path():
    path = user_data_dir() / "switch_states.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_switch_states():
    state = {
        "keep_fps": modules.globals.keep_fps,
        "keep_audio": modules.globals.keep_audio,
        "keep_frames": modules.globals.keep_frames,
        "many_faces": modules.globals.many_faces,
        "map_faces": modules.globals.map_faces,
        "quality_mode": modules.globals.quality_mode,
        "poisson_blend": modules.globals.poisson_blend,
        "color_correction": modules.globals.color_correction,
        "nsfw_filter": modules.globals.nsfw_filter,
        "live_mirror": modules.globals.live_mirror,
        "live_resizable": modules.globals.live_resizable,
        "fp_ui": modules.globals.fp_ui,
        "show_fps": modules.globals.show_fps,
        "mouth_mask": modules.globals.mouth_mask,
        "show_mouth_mask_box": modules.globals.show_mouth_mask_box,
        "mouth_mask_size": modules.globals.mouth_mask_size,
        "mouth_mask_temporal_smoothing": modules.globals.mouth_mask_temporal_smoothing,
        "mouth_mask_temporal_motion_reduction": modules.globals.mouth_mask_temporal_motion_reduction,
        "compositing_extended_subject_mask": modules.globals.compositing_extended_subject_mask,
        "compositing_show_subject_mask": modules.globals.compositing_show_subject_mask,
        "opacity": modules.globals.opacity,
        "sharpness": modules.globals.sharpness,
        "enable_interpolation": modules.globals.enable_interpolation,
        "interpolation_weight": modules.globals.interpolation_weight,
        "live_process_latest_frame": modules.globals.live_process_latest_frame,
        "live_detection_interval_ratio": modules.globals.live_detection_interval_ratio,
        "face_tracking_enabled": modules.globals.face_tracking_enabled,
        "face_tracking_current_weight": modules.globals.face_tracking_current_weight,
        "face_tracking_reset_ratio": modules.globals.face_tracking_reset_ratio,
        "face_tracking_max_missed": modules.globals.face_tracking_max_missed,
        "face_tracking_confidence_weight": modules.globals.face_tracking_confidence_weight,
        "face_tracking_confidence_reference": modules.globals.face_tracking_confidence_reference,
        "face_tracking_confidence_min_weight": modules.globals.face_tracking_confidence_min_weight,
        "face_tracking_min_detection_confidence": modules.globals.face_tracking_min_detection_confidence,
        "expression_temporal_unilateral_eye_motion_scale": modules.globals.expression_temporal_unilateral_eye_motion_scale,
        "compositing_color_match_strength": modules.globals.compositing_color_match_strength,
    }
    state.update(quality_profile_runtime_state(modules.globals))
    try:
        with _switch_state_path().open("w", encoding="utf-8") as f:
            json.dump(state, f)
    except OSError:
        pass


def load_switch_states():
    try:
        with _switch_state_path().open("r", encoding="utf-8") as f:
            state = json.load(f)
        modules.globals.keep_fps = state.get("keep_fps", True)
        modules.globals.keep_audio = state.get("keep_audio", True)
        modules.globals.keep_frames = state.get("keep_frames", False)
        modules.globals.many_faces = state.get("many_faces", False)
        modules.globals.map_faces = state.get("map_faces", False)
        quality_mode = state.get("quality_mode", "balanced")
        if quality_mode not in QUALITY_MODE_NAMES:
            quality_mode = "balanced"
        apply_quality_profile(quality_mode, modules.globals)
        modules.globals.color_correction = state.get("color_correction", False)
        modules.globals.nsfw_filter = state.get("nsfw_filter", False)
        modules.globals.live_mirror = state.get("live_mirror", False)
        modules.globals.live_resizable = state.get("live_resizable", False)
        if "fp_ui" in state:
            saved_fp_ui = default_enhancer_state()
            saved_fp_ui.update(state.get("fp_ui", {}))
            modules.globals.fp_ui = saved_fp_ui
        modules.globals.show_fps = state.get("show_fps", False)
        modules.globals.show_mouth_mask_box = False
        modules.globals.compositing_extended_subject_mask = state.get(
            "compositing_extended_subject_mask",
            True,
        )
        modules.globals.compositing_show_subject_mask = state.get(
            "compositing_show_subject_mask",
            False,
        )
        modules.globals.opacity = state.get("opacity", 1.0)
        restore_quality_profile_runtime_state(modules.globals, state)
        modules.globals.mouth_mask = modules.globals.mouth_mask_size > 0
    except FileNotFoundError:
        pass
    except (OSError, json.JSONDecodeError):
        pass


# ─── thread-safe status bridge ───────────────────────────────────────────


class _UIBridge(QObject):
    """Single QObject that owns cross-thread signals."""

    statusChanged = Signal(str)
    modelDownloadFinished = Signal(int)


def _emit_status(text: str) -> None:
    if _BRIDGE is None:
        print(text)
        return
    _BRIDGE.statusChanged.emit(text)


# ─── public API ──────────────────────────────────────────────────────────


def update_status(text: str) -> None:
    """Thread-safe status update — uses signal if called off-UI thread."""
    _emit_status(_(text))
    if _APP is not None and QThread.currentThread() is _APP.thread():
        # Repaint status changes during synchronous preview/render work, but
        # defer mouse and keyboard events. Processing user input here can
        # re-enter Preview/Start Render while a model lock is already held,
        # leaving the UI waiting forever on its own non-reentrant lock.
        _APP.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)


def check_and_ignore_nsfw(target, destroy: Optional[Callable] = None) -> bool:
    from numpy import ndarray
    from modules.predicter import predict_frame, predict_image, predict_video

    check_nsfw = None
    if isinstance(target, str):
        check_nsfw = predict_image if has_image_extension(target) else predict_video
    elif isinstance(target, ndarray):
        check_nsfw = predict_frame

    if check_nsfw and check_nsfw(target):
        if destroy:
            destroy(to_quit=False)
        update_status("Processing ignored!")
        return True
    return False


def _load_source_face(source_path: str | None):
    from modules.face_analyser import get_one_face

    if not source_path:
        return None

    source_frame = read_image(source_path)
    if source_frame is None:
        update_status(f"Could not read source image: {source_path}")
        return None

    source_face = get_one_face(source_frame)
    if source_face is None:
        update_status(f"No face found in source image: {source_path}")
        return None

    return source_face


# ─── camera enumeration (unchanged from tk version) ──────────────────────


def get_available_cameras() -> Tuple[List[int], List[str]]:
    if platform.system() == "Windows":
        try:
            graph = FilterGraph()
            devices = graph.get_input_devices()
            if devices:
                return list(range(len(devices))), devices
            return [], ["No cameras found"]
        except Exception as exc:
            print(f"Error detecting cameras: {exc}")
            return [], ["No cameras found"]

    if platform.system() == "Darwin":
        return [0, 1], ["Camera 0", "Camera 1"]

    # Linux probe
    indices: List[int] = []
    names: List[str] = []
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            indices.append(i)
            names.append(f"Camera {i}")
            cap.release()
    return (indices, names) if names else ([], ["No cameras found"])


# ─── main window ─────────────────────────────────────────────────────────


def _make_image_drop(text: str, size: Tuple[int, int]) -> QLabel:
    label = QLabel(text)
    label.setObjectName("imageDrop")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFixedSize(size[0], size[1])
    label.setWordWrap(True)
    label.setText(text)
    return label


def _media_slot(
    title: str,
    hint: str,
    preview: QLabel,
    controls: QHBoxLayout | QPushButton,
) -> QFrame:
    slot = QFrame()
    slot.setObjectName("mediaSlot")
    slot.setFixedHeight(MEDIA_SLOT_HEIGHT)
    slot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    layout = QVBoxLayout(slot)
    layout.setContentsMargins(14, 14, 14, 16)
    layout.setSpacing(10)
    layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    title_row = QVBoxLayout()
    title_row.setSpacing(2)
    title_label = QLabel(title)
    title_label.setObjectName("mediaTitle")
    title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    hint_label = QLabel(hint)
    hint_label.setObjectName("mediaHint")
    hint_label.setWordWrap(True)
    hint_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    title_row.addWidget(title_label)
    title_row.addWidget(hint_label)

    layout.addLayout(title_row)
    layout.addWidget(preview, alignment=Qt.AlignmentFlag.AlignCenter)

    if isinstance(controls, QPushButton):
        layout.addWidget(controls, alignment=Qt.AlignmentFlag.AlignCenter)
    else:
        layout.addLayout(controls)

    return slot


def _quality_badge_text() -> str:
    try:
        profile = get_quality_profile(modules.globals.quality_mode)
        return f"Mode: {profile.label}"
    except ValueError:
        return "Mode: Balanced"


def _provider_badge_text() -> str:
    providers = modules.globals.execution_providers or ["CPUExecutionProvider"]
    provider_names = [
        provider[0] if isinstance(provider, tuple) else str(provider)
        for provider in providers
    ]
    compact = [name.replace("ExecutionProvider", "") for name in provider_names]
    return "Provider: " + " + ".join(compact[:2])


def _enhancer_badge_text() -> str:
    active_key = active_enhancer_key(modules.globals.fp_ui)
    if active_key is None:
        return "Enhancer: None"
    for enhancer_profile in get_enhancer_choices():
        if enhancer_profile.key == active_key:
            return f"Enhancer: {enhancer_profile.label}"
    return f"Enhancer: {active_key}"


class _Switch(QWidget):
    """Compact toggle switch with label + optional tooltip."""

    toggled = Signal(bool)

    def __init__(self, text: str, initial: bool, tooltip: str = ""):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._checkbox = QCheckBox(text)
        self._checkbox.setChecked(initial)
        self._checkbox.toggled.connect(self.toggled.emit)
        if tooltip:
            self._checkbox.setToolTip(tooltip)
        layout.addWidget(self._checkbox)
        layout.addStretch(1)

    def isChecked(self) -> bool:
        return self._checkbox.isChecked()

    def setChecked(self, value: bool) -> None:
        self._checkbox.setChecked(value)


class MainWindow(QMainWindow):
    def __init__(self, start_cb: Callable, destroy_cb: Callable):
        super().__init__()
        load_switch_states()
        self._start_cb = start_cb
        self._destroy_cb = destroy_cb

        self.setWindowTitle(
            f"{modules.metadata.name} {modules.metadata.version} {modules.metadata.edition}"
        )
        self.setWindowIcon(app_icon())
        self.setMinimumSize(ROOT_WIDTH, ROOT_HEIGHT)
        self.resize(ROOT_WIDTH, ROOT_HEIGHT)
        self._model_download_running = False
        self._file_operation_running = False
        self._exit_requested = False

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCentralWidget(scroll)

        root = QWidget()
        root.setMinimumSize(ROOT_WIDTH - 36, ROOT_HEIGHT - 70)
        scroll.setWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(14)
        layout.addWidget(self._build_header())

        self._body_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._body_layout.setSpacing(14)

        session_col = QVBoxLayout()
        session_col.setSpacing(12)
        session_col.addWidget(self._build_media_card(), 1)
        session_col.addLayout(self._build_action_row())

        controls_col = QVBoxLayout()
        controls_col.setSpacing(12)
        controls_col.addWidget(self._build_options_card())
        controls_col.addWidget(self._build_sliders_card())
        controls_col.addWidget(self._build_camera_card())
        controls_col.addStretch(1)

        self._body_layout.addLayout(session_col, 3)
        self._body_layout.addLayout(controls_col, 2)
        layout.addLayout(self._body_layout, 1)

        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.statusBar().addWidget(self._status_label, 1)

        footer = QLabel("Deep Live Cam")
        footer.setObjectName("linkLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer.setCursor(Qt.CursorShape.PointingHandCursor)
        footer.mousePressEvent = lambda _e: webbrowser.open("https://deeplivecam.net")
        self.statusBar().addPermanentWidget(footer)
        if _BRIDGE is not None:
            _BRIDGE.modelDownloadFinished.connect(self._on_model_download_finished)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("studioHeader")
        self._header_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, header)
        layout = self._header_layout
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        logo_path = app_logo_path()
        if logo_path:
            logo = QLabel()
            logo.setObjectName("logoLabel")
            logo.setFixedSize(46, 46)
            logo.setPixmap(
                QPixmap(logo_path).scaled(
                    46,
                    46,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Deep Live Cam Studio")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Native live-render control surface")
        subtitle.setObjectName("subtitleLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        layout.addLayout(title_col, 1)

        self.lbl_quality_badge = QLabel()
        self.lbl_quality_badge.setObjectName("pillLabel")
        self.lbl_provider_badge = QLabel()
        self.lbl_provider_badge.setObjectName("pillLabel")
        self.lbl_enhancer_badge = QLabel()
        self.lbl_enhancer_badge.setObjectName("pillLabel")
        self.btn_model_setup = QPushButton(_("Set Up Models"))
        self.btn_model_setup.setObjectName("secondary")
        self.btn_model_setup.setToolTip(
            _("Download and verify required model files")
        )
        self.btn_model_setup.clicked.connect(self._on_setup_models)

        layout.addWidget(self.btn_model_setup)
        layout.addWidget(self.lbl_quality_badge)
        layout.addWidget(self.lbl_provider_badge)
        layout.addWidget(self.lbl_enhancer_badge)
        self._refresh_studio_badges()
        return header

    # ── image row ────────────────────────────────────────────────────────

    def _build_media_card(self) -> QGroupBox:
        card = QGroupBox(_("Media"))
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 22, 16, 16)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(self._build_image_row())
        return card

    def _build_image_row(self) -> QBoxLayout:
        self._media_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        row = self._media_row
        row.setSpacing(20)

        self.source_label = _make_image_drop(
            _("Drop or select a face image"),
            (SOURCE_TARGET_PREVIEW_SIZE, SOURCE_TARGET_PREVIEW_SIZE),
        )
        src_row = QHBoxLayout()
        src_row.setSpacing(8)
        self.btn_select_source = QPushButton(_("Select Face"))
        self.btn_select_source.setFixedWidth(MEDIA_ACTION_WIDTH)
        self.btn_select_source.setToolTip(
            _("Choose the source face image to swap onto the target")
        )
        self.btn_select_source.clicked.connect(self._on_select_source)
        src_row.addWidget(self.btn_select_source)
        src_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        src_slot = _media_slot(
            _("Source face"),
            _("Identity image used for the swap"),
            self.source_label,
            src_row,
        )

        # Swap button column
        swap_col = QVBoxLayout()
        swap_col.addStretch(1)
        self.btn_swap = QPushButton(_("Swap"))
        self.btn_swap.setObjectName("secondary")
        self.btn_swap.setFixedSize(84, 40)
        self.btn_swap.setToolTip(_("Swap source and target images"))
        self.btn_swap.clicked.connect(self._on_swap_paths)
        swap_col.addWidget(self.btn_swap, alignment=Qt.AlignmentFlag.AlignCenter)
        swap_col.addStretch(1)

        self.target_label = _make_image_drop(
            _("Drop or select target media"),
            (SOURCE_TARGET_PREVIEW_SIZE, SOURCE_TARGET_PREVIEW_SIZE),
        )
        self.btn_select_target = QPushButton(_("Select Target"))
        self.btn_select_target.setToolTip(
            _("Choose the target image or video to apply face swap to")
        )
        self.btn_select_target.setFixedWidth(MEDIA_ACTION_WIDTH)
        self.btn_select_target.clicked.connect(self._on_select_target)
        tgt_slot = _media_slot(
            _("Target media"),
            _("Image or video that receives the face"),
            self.target_label,
            self.btn_select_target,
        )

        row.addWidget(src_slot, 1, alignment=Qt.AlignmentFlag.AlignTop)
        row.addLayout(swap_col)
        row.addWidget(tgt_slot, 1, alignment=Qt.AlignmentFlag.AlignTop)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)
        return row

    # ── options card ─────────────────────────────────────────────────────

    def _build_options_card(self) -> QGroupBox:
        card = QGroupBox(_("Render Controls"))
        grid = QGridLayout(card)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(6)

        def make(field, label, tip):
            sw = _Switch(_(label), getattr(modules.globals, field), _(tip))
            sw.toggled.connect(
                lambda v, f=field: (
                    setattr(modules.globals, f, v),
                    save_switch_states(),
                )
            )
            return sw

        self.sw_keep_fps = make("keep_fps", "Keep fps",
                                "Output video keeps the original frame rate")
        self.sw_keep_audio = make("keep_audio", "Keep audio",
                                  "Copy audio track from the source video to output")
        self.sw_keep_frames = make("keep_frames", "Keep frames",
                                   "Keep extracted frames on disk after processing")
        self.sw_many_faces = make("many_faces", "Many faces",
                                  "Swap every detected face, not just the primary one")
        self.sw_poisson = make("poisson_blend", "Poisson Blend",
                               "Blend face edges smoothly using Poisson blending")
        self.sw_color_fix = make("color_correction", "Fix Blueish Cam",
                                 "Fix blue/green color cast from some webcams")
        self.sw_show_fps = make("show_fps", "Show FPS",
                                "Display frames-per-second counter on the live preview")
        self.sw_extended_subject_mask = make(
            "compositing_extended_subject_mask",
            "Extended subject mask",
            "Expand blending into hairline, neck, shoulders, and upper chest",
        )
        self.sw_subject_mask_overlay = make(
            "compositing_show_subject_mask",
            "Show subject mask",
            "Overlay the active subject blend mask on preview/live output",
        )

        # Map faces is special — closes mapper when toggled off.
        self.sw_map_faces = _Switch(_("Map faces"), modules.globals.map_faces,
                                    _("Manually assign which source face maps to which target face"))
        self.sw_map_faces.toggled.connect(self._on_map_faces_toggled)

        # Layout: 2 columns of switches
        items = [
            self.sw_keep_fps, self.sw_keep_audio,
            self.sw_keep_frames, self.sw_many_faces,
            self.sw_map_faces, self.sw_show_fps,
            self.sw_poisson, self.sw_color_fix,
            self.sw_extended_subject_mask, self.sw_subject_mask_overlay,
        ]
        for i, w in enumerate(items):
            grid.addWidget(w, i // 2, i % 2)

        quality_row = len(items) // 2
        quality_label = QLabel(_("Quality Mode:"))
        grid.addWidget(quality_label, quality_row, 0)

        self.cb_quality_mode = QComboBox()
        for mode_name in QUALITY_MODE_NAMES:
            profile = get_quality_profile(mode_name)
            self.cb_quality_mode.addItem(_(profile.label), mode_name)
        current_quality_index = self.cb_quality_mode.findData(
            modules.globals.quality_mode
        )
        if current_quality_index >= 0:
            self.cb_quality_mode.setCurrentIndex(current_quality_index)
        self.cb_quality_mode.currentIndexChanged.connect(
            self._on_quality_mode_change
        )
        self.cb_quality_mode.setToolTip(
            _("Select a preset for latency, stability, and enhancement quality")
        )
        grid.addWidget(self.cb_quality_mode, quality_row, 1)

        # Face enhancer dropdown
        enhancer_label = QLabel(_("Face Enhancer:"))
        grid.addWidget(enhancer_label, quality_row + 1, 0)

        self.cb_enhancer = QComboBox()
        self.cb_enhancer.addItem("None", None)
        for enhancer_profile in get_enhancer_choices():
            self.cb_enhancer.addItem(enhancer_profile.label, enhancer_profile.key)
        initial_key = active_enhancer_key(modules.globals.fp_ui)
        initial_index = self.cb_enhancer.findData(initial_key)
        if initial_index >= 0:
            self.cb_enhancer.setCurrentIndex(initial_index)
        self.cb_enhancer.currentIndexChanged.connect(self._on_enhancer_change)
        self.cb_enhancer.setToolTip(_("Select a face enhancement model (None = no enhancement)"))
        grid.addWidget(self.cb_enhancer, quality_row + 1, 1)

        return card

    # ── sliders card ─────────────────────────────────────────────────────

    def _build_sliders_card(self) -> QGroupBox:
        card = QGroupBox(_("Refinement"))
        grid = QGridLayout(card)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        def slider(min_v, max_v, default, denom, on_change):
            s = QSlider(Qt.Orientation.Horizontal)
            s.setRange(int(min_v * denom), int(max_v * denom))
            s.setValue(int(default * denom))
            s.valueChanged.connect(lambda iv: on_change(iv / denom))
            return s

        # Transparency
        grid.addWidget(QLabel(_("Transparency")), 0, 0)
        self.s_transparency = slider(0.0, 1.0, modules.globals.opacity, 100, self._on_transparency_change)
        self.s_transparency.setToolTip(
            _("Blend between original and swapped face (0% = original, 100% = fully swapped)")
        )
        grid.addWidget(self.s_transparency, 0, 1)

        # Sharpness
        grid.addWidget(QLabel(_("Sharpness")), 1, 0)
        self.s_sharpness = slider(0.0, 5.0, modules.globals.sharpness, 10, self._on_sharpness_change)
        self.s_sharpness.setToolTip(_("Sharpen the enhanced face output"))
        grid.addWidget(self.s_sharpness, 1, 1)

        # Mouth mask
        grid.addWidget(QLabel(_("Mouth Mask")), 2, 0)
        self.s_mouth = slider(0.0, 100.0, modules.globals.mouth_mask_size, 1,
                              self._on_mouth_mask_change)
        self.s_mouth.sliderPressed.connect(self._on_mouth_mask_pressed)
        self.s_mouth.sliderReleased.connect(self._on_mouth_mask_released)
        self.s_mouth.setToolTip(
            _("0 = use swapped mouth, 100 = expose original mouth to chin area")
        )
        grid.addWidget(self.s_mouth, 2, 1)
        return card

    # ── action row ───────────────────────────────────────────────────────

    def _build_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        self.btn_start = QPushButton(_("Start Render"))
        self.btn_start.setToolTip(_("Begin processing the target image/video with selected face"))
        self.btn_start.clicked.connect(self._on_start)

        self.btn_destroy = QPushButton(_("Exit"))
        self.btn_destroy.setObjectName("danger")
        self.btn_destroy.setToolTip(_("Stop processing and close the application"))
        self.btn_destroy.clicked.connect(self._on_exit)

        self.btn_preview = QPushButton(_("Preview"))
        self.btn_preview.setObjectName("secondary")
        self.btn_preview.setToolTip(_("Show/hide a preview of the processed output"))
        self.btn_preview.clicked.connect(self._on_toggle_preview)

        row.addWidget(self.btn_preview)
        row.addStretch(1)
        row.addWidget(self.btn_destroy)
        row.addWidget(self.btn_start)
        return row

    # ── camera card ──────────────────────────────────────────────────────

    def _build_camera_card(self) -> QGroupBox:
        card = QGroupBox(_("Live Output"))
        layout = QHBoxLayout(card)

        layout.addWidget(QLabel(_("Camera")))
        self._camera_indices, self._camera_names = get_available_cameras()

        self.cb_camera = QComboBox()
        if not self._camera_names or self._camera_names[0] == "No cameras found":
            self.cb_camera.addItem("No cameras found")
            self.cb_camera.setEnabled(False)
            cam_ok = False
        else:
            self.cb_camera.addItems(self._camera_names)
            cam_ok = True
        self.cb_camera.setToolTip(_("Select which camera to use for live mode"))
        layout.addWidget(self.cb_camera, 1)

        self.btn_live = QPushButton(_("Start Live"))
        self.btn_live.setEnabled(cam_ok)
        self.btn_live.setToolTip(_("Start real-time face swap using webcam"))
        self.btn_live.clicked.connect(self._on_live)
        layout.addWidget(self.btn_live)

        return card

    # ── slot handlers ────────────────────────────────────────────────────

    def set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _run_file_operation(
        self,
        operation: Callable[[], None],
        failure_message: str,
    ) -> bool:
        """Run one preview/render action without allowing UI re-entry."""
        if self._file_operation_running:
            return False

        self._file_operation_running = True
        self.btn_start.setEnabled(False)
        self.btn_preview.setEnabled(False)
        try:
            operation()
        except Exception:
            traceback.print_exc()
            update_status(failure_message)
        finally:
            self._file_operation_running = False
            self.btn_start.setEnabled(True)
            self.btn_preview.setEnabled(True)
        return True

    def _on_setup_models(self) -> None:
        if self._model_download_running:
            return

        from modules.model_manager import missing_models, model_directory

        specs = missing_models()
        if not specs:
            QMessageBox.information(
                self,
                _("Models Ready"),
                _("All model files are already downloaded and verified."),
            )
            update_status(f"All model files are verified in {model_directory()}.")
            return

        names = "\n".join(f"- {spec.file_name}" for spec in specs)
        details = "\n\n".join(
            (
                f"{spec.file_name}\n"
                f"Source: {spec.source}\n"
                f"URL: {spec.url}\n"
                f"SHA256: {spec.sha256}\n"
                f"License note: {spec.license_note}"
            )
            for spec in specs
        )
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Question)
        message.setWindowTitle(_("Download Models"))
        message.setText(
            _(
                "Deep Live Cam Studio needs model files before face swapping can run."
            )
        )
        message.setInformativeText(
            _(
                "The installer does not include these files. Download and verify "
                "the missing models now?\n\n"
            )
            + names
            + "\n\n"
            + _("Models will be stored in:")
            + f"\n{model_directory()}"
        )
        message.setDetailedText(details)
        message.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        message.setDefaultButton(QMessageBox.StandardButton.Yes)
        if message.exec() != QMessageBox.StandardButton.Yes:
            update_status("Model download cancelled.")
            return

        self._model_download_running = True
        self.btn_model_setup.setEnabled(False)
        self.btn_model_setup.setText(_("Downloading..."))
        update_status("Downloading and verifying model files...")

        worker = threading.Thread(
            target=self._download_models_background,
            name="DeepLiveCamModelDownloader",
            daemon=True,
        )
        worker.start()

    def _download_models_background(self) -> None:
        try:
            from modules.model_manager import download_models

            exit_code = download_models(assume_yes=True)
        except Exception:
            traceback.print_exc()
            exit_code = 1

        if _BRIDGE is not None:
            _BRIDGE.modelDownloadFinished.emit(exit_code)

    def _on_model_download_finished(self, exit_code: int) -> None:
        self._model_download_running = False
        self.btn_model_setup.setEnabled(True)
        self.btn_model_setup.setText(_("Set Up Models"))
        if exit_code == 0:
            update_status("Model files downloaded and verified.")
            QMessageBox.information(
                self,
                _("Models Ready"),
                _("Model files were downloaded and verified successfully."),
            )
        elif exit_code == 2:
            update_status("Model download cancelled.")
        else:
            update_status("Model download failed. Check the desktop launch log for details.")
            QMessageBox.warning(
                self,
                _("Model Download Failed"),
                _(
                    "The model download did not complete. Check your internet "
                    "connection and try Set Up Models again."
                ),
            )

    def _refresh_studio_badges(self) -> None:
        if hasattr(self, "lbl_quality_badge"):
            self.lbl_quality_badge.setText(_quality_badge_text())
        if hasattr(self, "lbl_provider_badge"):
            self.lbl_provider_badge.setText(_provider_badge_text())
        if hasattr(self, "lbl_enhancer_badge"):
            self.lbl_enhancer_badge.setText(_enhancer_badge_text())

    def _on_select_source(self) -> None:
        global _RECENT_SOURCE_DIR
        if _PREVIEW is not None:
            _PREVIEW.hide()
        path, _filter = QFileDialog.getOpenFileName(
            self, _("select an source image"),
            _RECENT_SOURCE_DIR or "",
            IMAGE_FILE_FILTER,
        )
        if path and is_image(path):
            modules.globals.source_path = path
            _RECENT_SOURCE_DIR = os.path.dirname(path)
            self.source_label.setPixmap(
                render_image_preview(
                    path,
                    (SOURCE_TARGET_PREVIEW_SIZE, SOURCE_TARGET_PREVIEW_SIZE),
                )
            )
            self.source_label.setText("")
        elif not path:
            return
        else:
            modules.globals.source_path = None
            self.source_label.clear()
            self.source_label.setText(_("Drop or select a face image"))

    def _on_select_target(self) -> None:
        global _RECENT_TARGET_DIR
        if _PREVIEW is not None:
            _PREVIEW.hide()
        path, _filter = QFileDialog.getOpenFileName(
            self, _("select an target image or video"),
            _RECENT_TARGET_DIR or "",
            MEDIA_FILE_FILTER,
        )
        if not path:
            return
        if is_image(path):
            modules.globals.target_path = path
            _RECENT_TARGET_DIR = os.path.dirname(path)
            self.target_label.setPixmap(
                render_image_preview(
                    path,
                    (SOURCE_TARGET_PREVIEW_SIZE, SOURCE_TARGET_PREVIEW_SIZE),
                )
            )
            self.target_label.setText("")
        elif is_video(path):
            modules.globals.target_path = path
            _RECENT_TARGET_DIR = os.path.dirname(path)
            pm = render_video_preview(
                path,
                (SOURCE_TARGET_PREVIEW_SIZE, SOURCE_TARGET_PREVIEW_SIZE),
            )
            if pm:
                self.target_label.setPixmap(pm)
                self.target_label.setText("")
        else:
            modules.globals.target_path = None
            self.target_label.clear()
            self.target_label.setText(_("Drop or select target media"))

    def _on_swap_paths(self) -> None:
        global _RECENT_SOURCE_DIR, _RECENT_TARGET_DIR
        sp = modules.globals.source_path
        tp = modules.globals.target_path
        if not (sp and tp and is_image(sp) and is_image(tp)):
            return
        modules.globals.source_path, modules.globals.target_path = tp, sp
        _RECENT_SOURCE_DIR = os.path.dirname(tp)
        _RECENT_TARGET_DIR = os.path.dirname(sp)
        if _PREVIEW is not None:
            _PREVIEW.hide()
        preview_size = (SOURCE_TARGET_PREVIEW_SIZE, SOURCE_TARGET_PREVIEW_SIZE)
        self.source_label.setPixmap(render_image_preview(tp, preview_size))
        self.target_label.setPixmap(render_image_preview(sp, preview_size))
        self.source_label.setText("")
        self.target_label.setText("")

    def _on_map_faces_toggled(self, value: bool) -> None:
        modules.globals.map_faces = value
        save_switch_states()
        if not value:
            close_mapper_window()

    def _on_quality_mode_change(self) -> None:
        mode_name = self.cb_quality_mode.currentData()
        if not mode_name:
            return
        profile = apply_quality_profile(mode_name, modules.globals)
        self._sync_quality_controls()
        if _WEBCAM_PREVIEW is not None and _WEBCAM_PREVIEW.isVisible():
            from modules.processors.frame.core import (
                get_frame_processors_modules,
                reset_frame_processor_temporal_state,
            )

            reset_frame_processor_temporal_state(
                get_frame_processors_modules(modules.globals.frame_processors)
            )
        save_switch_states()
        update_status(f"Quality mode set to {profile.label}.")

    def _sync_quality_controls(self) -> None:
        if hasattr(self, "sw_poisson"):
            self.sw_poisson.setChecked(modules.globals.poisson_blend)

        if hasattr(self, "cb_enhancer"):
            enhancer_index = self.cb_enhancer.findData(
                active_enhancer_key(modules.globals.fp_ui)
            )
            if enhancer_index < 0:
                enhancer_index = 0
            self.cb_enhancer.blockSignals(True)
            self.cb_enhancer.setCurrentIndex(enhancer_index)
            self.cb_enhancer.blockSignals(False)

        if hasattr(self, "s_sharpness"):
            self.s_sharpness.setValue(int(modules.globals.sharpness * 10))
        if hasattr(self, "s_mouth"):
            self.s_mouth.setValue(int(modules.globals.mouth_mask_size))
        self._refresh_studio_badges()

    def _on_enhancer_change(self, *_args) -> None:
        for key in ENHANCER_KEYS:
            _update_tumbler(key, False)
        selected = self.cb_enhancer.currentData() if hasattr(self, "cb_enhancer") else None
        if selected:
            _update_tumbler(selected, True)
        self._refresh_studio_badges()
        save_switch_states()

    def _on_transparency_change(self, value: float) -> None:
        modules.globals.opacity = value
        pct = int(value * 100)
        if pct == 0:
            for key in ENHANCER_KEYS:
                modules.globals.fp_ui[key] = False
            self._sync_quality_controls()
            update_status("Transparency set to 0% - Face swapping disabled.")
        elif pct == 100:
            modules.globals.face_swapper_enabled = True
            update_status("Transparency set to 100%.")
        else:
            modules.globals.face_swapper_enabled = True
            update_status(f"Transparency set to {pct}%")

    def _on_sharpness_change(self, value: float) -> None:
        modules.globals.sharpness = value
        update_status(f"Sharpness set to {value:.1f}")

    def _on_mouth_mask_change(self, value: float) -> None:
        modules.globals.mouth_mask_size = value
        modules.globals.mouth_mask = value > 0
        if value <= 0:
            modules.globals.show_mouth_mask_box = False

    def _on_mouth_mask_pressed(self) -> None:
        if modules.globals.mouth_mask_size > 0:
            modules.globals.show_mouth_mask_box = True

    def _on_mouth_mask_released(self) -> None:
        modules.globals.show_mouth_mask_box = False

    def _on_start(self) -> None:
        if self._file_operation_running:
            return
        if _MAPPER is not None and _MAPPER.isVisible():
            update_status("Please complete pop-up or close it.")
            return
        if modules.globals.map_faces:
            from modules.face_analyser import (
                get_unique_faces_from_target_image,
                get_unique_faces_from_target_video,
            )

            modules.globals.source_target_map = []
            if is_image(modules.globals.target_path):
                update_status("Getting unique faces")
                get_unique_faces_from_target_image()
            elif is_video(modules.globals.target_path):
                update_status("Getting unique faces")
                get_unique_faces_from_target_video()
            if modules.globals.source_target_map:
                _open_mapper_dialog(self._start_cb, modules.globals.source_target_map)
            else:
                update_status("No faces found in target")
        else:
            self._select_output_and_start()

    def _select_output_and_start(self) -> None:
        global _RECENT_OUTPUT_DIR
        if is_image(modules.globals.target_path):
            path, _f = QFileDialog.getSaveFileName(
                self, _("save image output file"),
                os.path.join(_RECENT_OUTPUT_DIR or "", "output.png"),
                IMAGE_FILE_FILTER,
            )
        elif is_video(modules.globals.target_path):
            path, _f = QFileDialog.getSaveFileName(
                self, _("save video output file"),
                os.path.join(_RECENT_OUTPUT_DIR or "", "output.mp4"),
                "Videos (*.mp4 *.mkv)",
            )
        else:
            return
        if path:
            modules.globals.output_path = path
            _RECENT_OUTPUT_DIR = os.path.dirname(path)
            self._run_file_operation(
                self._start_cb,
                "Render failed. Check the desktop launch log for details.",
            )

    def _on_toggle_preview(self) -> None:
        if self._file_operation_running:
            return
        if _PREVIEW is None:
            return
        if _PREVIEW.isVisible():
            _PREVIEW.hide()
        elif modules.globals.source_path and modules.globals.target_path:
            def refresh_and_show_preview() -> None:
                _PREVIEW.init_for_target()
                _PREVIEW.refresh_frame(0)
                _PREVIEW.show()

            self._run_file_operation(
                refresh_and_show_preview,
                "Preview failed. Check the desktop launch log for details.",
            )

    def _on_live(self) -> None:
        idx = self.cb_camera.currentIndex()
        if idx < 0 or idx >= len(self._camera_indices):
            update_status("No camera available")
            return
        camera_index = self._camera_indices[idx]
        if _LIVE_MAPPER is not None and _LIVE_MAPPER.isVisible():
            update_status("Source x Target Mapper is already open.")
            _LIVE_MAPPER.raise_()
            return
        if not modules.globals.map_faces:
            if modules.globals.source_path is None:
                update_status("Please select a source image first")
                return
            modules.globals.virtual_cam = True
            update_status("Starting live output; models will load in the background.")
            _open_webcam_preview(camera_index)
        else:
            modules.globals.virtual_cam = True
            modules.globals.source_target_map = []
            _open_live_mapper_dialog(camera_index, modules.globals.source_target_map)

    def _shutdown_child_windows(self, block: bool = False) -> None:
        global _PREVIEW, _WEBCAM_PREVIEW
        if _WEBCAM_PREVIEW is not None:
            _WEBCAM_PREVIEW.shutdown(block=block)
            _WEBCAM_PREVIEW.close()
            _WEBCAM_PREVIEW = None
        if _PREVIEW is not None:
            _PREVIEW.close()
            _PREVIEW = None
        close_mapper_window()

    def _finish_exit(self) -> None:
        self.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _on_exit(self) -> None:
        if self._exit_requested:
            return
        self._exit_requested = True
        update_status("Closing Deep Live Cam Studio...")
        self._shutdown_child_windows(block=True)
        _destroy_without_quit(self._destroy_cb)
        QTimer.singleShot(0, self._finish_exit)

    def closeEvent(self, event):
        if not self._exit_requested:
            self._exit_requested = True
            self._shutdown_child_windows(block=True)
            _destroy_without_quit(self._destroy_cb)
        event.accept()
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(0, app.quit)


def _update_tumbler(var: str, value: bool) -> None:
    modules.globals.fp_ui[var] = value
    save_switch_states()
    # If we're currently in a live preview, refresh frame processors so
    # toggling enhancers takes effect immediately.
    if _WEBCAM_PREVIEW is not None and _WEBCAM_PREVIEW.isVisible():
        from modules.processors.frame.core import get_frame_processors_modules

        get_frame_processors_modules(modules.globals.frame_processors)


# ─── preview window (still-image / video scrub) ──────────────────────────


class PreviewWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_("Preview"))
        self.resize(PREVIEW_DEFAULT_WIDTH, PREVIEW_DEFAULT_HEIGHT)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._image_label, 1)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.valueChanged.connect(self.refresh_frame)
        layout.addWidget(self._slider)

    def init_for_target(self) -> None:
        if is_image(modules.globals.target_path):
            self._slider.hide()
        elif is_video(modules.globals.target_path):
            total = get_video_frame_total(modules.globals.target_path)
            self._slider.setRange(0, max(0, total - 1))
            self._slider.setValue(0)
            self._slider.show()

    def refresh_frame(self, frame_number: int = 0) -> None:
        if not (modules.globals.source_path and modules.globals.target_path):
            return
        update_status("Processing...")
        temp_frame = get_video_frame(modules.globals.target_path, frame_number)
        if modules.globals.nsfw_filter and check_and_ignore_nsfw(temp_frame):
            return
        from modules.processors.frame.core import get_frame_processors_modules as _gfpm
        source_face = _load_source_face(modules.globals.source_path)
        if source_face is None:
            update_status("Preview skipped because the source face could not be loaded.")
            return
        for fp in _gfpm(modules.globals.frame_processors):
            temp_frame = fp.process_frame(
                source_face, temp_frame
            )
        # Fit to current widget size while preserving aspect ratio.
        h, w = temp_frame.shape[:2]
        bound_w = min(PREVIEW_MAX_WIDTH, max(self.width(), PREVIEW_DEFAULT_WIDTH))
        bound_h = min(PREVIEW_MAX_HEIGHT, max(self.height(), PREVIEW_DEFAULT_HEIGHT))
        ratio = min(bound_w / w, bound_h / h)
        new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
        temp_frame = cv2.resize(temp_frame, new_size, interpolation=cv2.INTER_LANCZOS4)
        self._image_label.setPixmap(_bgr_to_qpixmap(temp_frame))
        update_status("Processing succeed!")


# ─── webcam preview window ───────────────────────────────────────────────


class _CaptureWorker(threading.Thread):
    """Reads frames from the camera into a bounded queue. Drops on overflow."""

    def __init__(
        self,
        cap,
        capture_queue: queue.Queue,
        stop_event: threading.Event,
        metrics: Optional[PipelineMetrics] = None,
    ):
        super().__init__(name="DeepLiveCamCapture", daemon=True)
        self._cap = cap
        self._queue = capture_queue
        self._stop_event = stop_event
        self._metrics = metrics

    def run(self) -> None:
        try:
            while not self._stop_event.is_set():
                ret, frame = self._cap.read()
                if not ret:
                    self._stop_event.set()
                    break
                dropped = put_latest(self._queue, frame)
                if dropped and self._metrics:
                    self._metrics.drop_frames("capture_input_queue", dropped)
        except Exception:
            self._stop_event.set()
            traceback.print_exc()


@dataclass
class _LiveProcessingRuntime:
    frame_processors: list[Any]
    face_tracker: FaceTracker | None
    detection_interval: int
    metrics: PipelineMetrics | None
    metrics_context: dict[str, Any]
    metrics_writer: MetricsJsonlWriter | None
    source_image: Any = None
    last_source_path: str | None = None
    previous_fps_time: float = 0.0
    frame_count: int = 0
    fps: float = 0.0
    detection_count: int = 0
    cached_target_face: Any = None
    cached_many_faces: list[Any] | None = None


def _live_face_tracker() -> FaceTracker | None:
    if not getattr(modules.globals, "face_tracking_enabled", True):
        return None
    return FaceTracker(
        current_weight=getattr(
            modules.globals, "face_tracking_current_weight", 0.7
        ),
        jump_reset_ratio=getattr(
            modules.globals, "face_tracking_reset_ratio", 1.2
        ),
        max_missed=getattr(modules.globals, "face_tracking_max_missed", 1),
        confidence_weight=getattr(
            modules.globals, "face_tracking_confidence_weight", 0.0
        ),
        confidence_reference=getattr(
            modules.globals, "face_tracking_confidence_reference", 0.75
        ),
        confidence_min_weight=getattr(
            modules.globals, "face_tracking_confidence_min_weight", 0.35
        ),
        min_detection_confidence=getattr(
            modules.globals, "face_tracking_min_detection_confidence", 0.0
        ),
        prediction_strength=getattr(
            modules.globals, "face_tracking_prediction_strength", 0.0
        ),
        prediction_decay=getattr(
            modules.globals, "face_tracking_prediction_decay", 0.5
        ),
    )


def _live_processor_names(frame_processors: list[Any]) -> list[str]:
    return [
        getattr(processor, "NAME", None)
        or getattr(processor, "__name__", type(processor).__name__).split(".")[-1]
        for processor in frame_processors
    ]


def _create_live_runtime(
    frame_processors: list[Any],
    camera_fps: float,
    capture_queue: queue.Queue,
    processed_queue: queue.Queue,
    virtual_cam: Optional[VirtualCameraSink],
    metrics: PipelineMetrics | None,
) -> _LiveProcessingRuntime:
    if metrics is None and getattr(modules.globals, "benchmark_pipeline", False):
        metrics = PipelineMetrics("live")
    context = {
        "quality_mode": getattr(modules.globals, "quality_mode", None),
        "frame_processors": _live_processor_names(frame_processors),
        "camera_fps": camera_fps,
        "virtual_cam": virtual_cam is not None,
        "mode": "live",
        "live_process_latest_frame": getattr(
            modules.globals, "live_process_latest_frame", True
        ),
        "capture_queue_maxsize": capture_queue.maxsize,
        "processed_queue_maxsize": processed_queue.maxsize,
        "execution_providers": list(modules.globals.execution_providers),
        "execution_provider_config": provider_config_summary(
            modules.globals.execution_providers
        ),
    }
    metrics_writer = (
        MetricsJsonlWriter(modules.globals.benchmark_output_path)
        if metrics and getattr(modules.globals, "benchmark_output_path", None)
        else None
    )
    detection_interval = max(
        1,
        round(
            camera_fps
            * getattr(modules.globals, "live_detection_interval_ratio", 0.08)
        ),
    )
    return _LiveProcessingRuntime(
        frame_processors=frame_processors,
        face_tracker=_live_face_tracker(),
        detection_interval=detection_interval,
        metrics=metrics,
        metrics_context=context,
        metrics_writer=metrics_writer,
        previous_fps_time=time.time(),
    )


def _dequeue_live_frame(
    capture_queue: queue.Queue, runtime: _LiveProcessingRuntime
) -> Any | None:
    started = time.perf_counter()
    try:
        if getattr(modules.globals, "live_process_latest_frame", True):
            frame, skipped = get_latest(capture_queue, timeout=0.05)
        else:
            frame = capture_queue.get(timeout=0.05)
            skipped = 0
    except queue.Empty:
        return None
    if runtime.metrics:
        runtime.metrics.observe("queue_wait", time.perf_counter() - started)
        runtime.metrics.drop_frames("capture_stale_queue", skipped)
        runtime.metrics.observe_queue_depth(
            "capture_queue_depth_after_get", capture_queue.qsize()
        )
    return frame


def _refresh_live_detection(
    runtime: _LiveProcessingRuntime,
    frame: np.ndarray,
    detect_many_faces_fast: Callable[[np.ndarray], list[Any]],
    detect_one_face_fast: Callable[[np.ndarray], Any],
    reset_temporal_state: Callable[[list[Any]], None],
) -> None:
    runtime.detection_count += 1
    if runtime.detection_count % runtime.detection_interval != 0:
        return
    started = time.perf_counter()
    if modules.globals.many_faces:
        if runtime.face_tracker is not None:
            runtime.face_tracker.reset()
            reset_temporal_state(runtime.frame_processors)
        runtime.cached_target_face = None
        runtime.cached_many_faces = detect_many_faces_fast(frame)
    else:
        detected_face = detect_one_face_fast(frame)
        runtime.cached_target_face = (
            runtime.face_tracker.update(detected_face, runtime.detection_count)
            if runtime.face_tracker is not None
            else detected_face
        )
        runtime.cached_many_faces = None
    if runtime.metrics:
        runtime.metrics.observe("detect_faces", time.perf_counter() - started)


def _cached_live_faces(runtime: _LiveProcessingRuntime) -> list[Any] | None:
    if runtime.cached_many_faces:
        return runtime.cached_many_faces
    if runtime.cached_target_face is not None:
        return [runtime.cached_target_face]
    return None


def _process_live_swapper(
    processor: Any,
    source_image: Any,
    frame: np.ndarray,
    runtime: _LiveProcessingRuntime,
) -> np.ndarray:
    if source_image is None:
        return frame
    swapped_bboxes = []
    swapped_faces = []
    if modules.globals.many_faces and runtime.cached_many_faces:
        result = frame.copy()
        for target_face in runtime.cached_many_faces:
            result = processor.swap_face(source_image, target_face, result)
            if hasattr(target_face, "bbox") and target_face.bbox is not None:
                swapped_bboxes.append(target_face.bbox.astype(int))
                swapped_faces.append(target_face)
        frame = result
    elif runtime.cached_target_face is not None:
        target_face = runtime.cached_target_face
        frame = processor.swap_face(source_image, target_face, frame)
        if hasattr(target_face, "bbox") and target_face.bbox is not None:
            swapped_bboxes.append(target_face.bbox.astype(int))
            swapped_faces.append(target_face)
    return processor.apply_post_processing(frame, swapped_bboxes, swapped_faces)


def _process_standard_live_frame(
    runtime: _LiveProcessingRuntime,
    frame: np.ndarray,
    detect_many_faces_fast: Callable[[np.ndarray], list[Any]],
    detect_one_face_fast: Callable[[np.ndarray], Any],
    reset_temporal_state: Callable[[list[Any]], None],
) -> np.ndarray:
    source_path = modules.globals.source_path
    if source_path and source_path != runtime.last_source_path:
        runtime.last_source_path = source_path
        runtime.source_image = _load_source_face(source_path)
        reset_temporal_state(runtime.frame_processors)
    _refresh_live_detection(
        runtime,
        frame,
        detect_many_faces_fast,
        detect_one_face_fast,
        reset_temporal_state,
    )
    cached_faces = _cached_live_faces(runtime)
    for processor in runtime.frame_processors:
        started = time.perf_counter()
        enhancer_key = enhancer_key_for_processor_name(processor.NAME)
        if enhancer_key is not None:
            if modules.globals.fp_ui.get(enhancer_key, False):
                frame = processor.process_frame(
                    None, frame, detected_faces=cached_faces
                )
        elif processor.NAME == "DLC.FACE-SWAPPER":
            if runtime.source_image is None:
                continue
            frame = _process_live_swapper(
                processor, runtime.source_image, frame, runtime
            )
        else:
            frame = processor.process_frame(runtime.source_image, frame)
        if runtime.metrics:
            runtime.metrics.observe(
                processor.NAME, time.perf_counter() - started
            )
    return frame


def _process_mapped_live_frame(
    runtime: _LiveProcessingRuntime, frame: np.ndarray
) -> np.ndarray:
    modules.globals.target_path = None
    for processor in runtime.frame_processors:
        started = time.perf_counter()
        enhancer_key = enhancer_key_for_processor_name(processor.NAME)
        if enhancer_key is None or modules.globals.fp_ui.get(enhancer_key, False):
            frame = processor.process_frame_v2(frame)
        if runtime.metrics:
            runtime.metrics.observe(
                processor.NAME, time.perf_counter() - started
            )
    return frame


def _update_live_fps(runtime: _LiveProcessingRuntime) -> float:
    now = time.time()
    runtime.frame_count += 1
    if now - runtime.previous_fps_time >= 0.5:
        runtime.fps = runtime.frame_count / (now - runtime.previous_fps_time)
        runtime.frame_count = 0
        runtime.previous_fps_time = now
    return runtime.fps


def _publish_live_frame(
    processed_queue: queue.Queue,
    virtual_cam: Optional[VirtualCameraSink],
    frame: np.ndarray,
    runtime: _LiveProcessingRuntime,
) -> None:
    if virtual_cam is not None:
        if runtime.metrics:
            with runtime.metrics.track("virtual_cam_send"):
                virtual_cam.send(frame)
        else:
            virtual_cam.send(frame)
    if runtime.metrics:
        runtime.metrics.observe_queue_depth(
            "processed_queue_depth_before_put", processed_queue.qsize()
        )
    try:
        processed_queue.put_nowait(frame)
    except queue.Full:
        try:
            processed_queue.get_nowait()
            if runtime.metrics:
                runtime.metrics.drop_frame("processed_output_queue")
        except queue.Empty:
            pass
        try:
            processed_queue.put_nowait(frame)
        except queue.Full:
            pass


def _record_live_frame_metrics(runtime: _LiveProcessingRuntime) -> None:
    if not runtime.metrics:
        return
    runtime.metrics.frame_complete()
    if runtime.metrics.should_report(modules.globals.benchmark_log_interval):
        print(format_metrics(runtime.metrics), flush=True)
        safe_write_metrics_snapshot(
            runtime.metrics_writer,
            runtime.metrics,
            event="periodic",
            extra=runtime.metrics_context,
        )
        runtime.metrics.mark_reported()


def _finalize_live_metrics(runtime: _LiveProcessingRuntime) -> None:
    if not runtime.metrics:
        return
    print(format_metrics(runtime.metrics), flush=True)
    safe_write_metrics_snapshot(
        runtime.metrics_writer,
        runtime.metrics,
        event="final",
        extra=runtime.metrics_context,
    )


class _ProcessingWorker(threading.Thread):
    """Pulls raw frames, runs detect/swap/enhance, pushes processed frames."""

    def __init__(
        self,
        capture_queue,
        processed_queue,
        stop_event,
        camera_fps: float,
        virtual_cam: Optional[VirtualCameraSink] = None,
        metrics: Optional[PipelineMetrics] = None,
    ):
        super().__init__(name="DeepLiveCamProcessing", daemon=True)
        self._cq = capture_queue
        self._pq = processed_queue
        self._stop_event = stop_event
        self._fps = camera_fps
        self._virtual_cam = virtual_cam
        self._metrics = metrics

    def run(self) -> None:
        try:
            from modules.face_analyser import detect_many_faces_fast, detect_one_face_fast
            from modules.processors.frame.core import (
                get_frame_processors_modules,
                reset_frame_processor_temporal_state,
            )

            frame_processors = get_frame_processors_modules(modules.globals.frame_processors)
            reset_frame_processor_temporal_state(frame_processors)
            runtime = _create_live_runtime(
                frame_processors,
                self._fps,
                self._cq,
                self._pq,
                self._virtual_cam,
                self._metrics,
            )

            while not self._stop_event.is_set():
                frame = _dequeue_live_frame(self._cq, runtime)
                if frame is None:
                    continue

                temp_frame = frame
                if modules.globals.live_mirror:
                    temp_frame = gpu_flip(temp_frame, 1)

                if not modules.globals.map_faces:
                    temp_frame = _process_standard_live_frame(
                        runtime,
                        temp_frame,
                        detect_many_faces_fast,
                        detect_one_face_fast,
                        reset_frame_processor_temporal_state,
                    )
                else:
                    temp_frame = _process_mapped_live_frame(runtime, temp_frame)

                live_fps = _update_live_fps(runtime)
                if modules.globals.show_fps:
                    cv2.putText(
                        temp_frame, f"FPS: {live_fps:.1f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
                    )
                _publish_live_frame(
                    self._pq, self._virtual_cam, temp_frame, runtime
                )
                _record_live_frame_metrics(runtime)
            _finalize_live_metrics(runtime)
        except Exception:
            self._stop_event.set()
            traceback.print_exc()


class WebcamPreviewWindow(QWidget):
    def __init__(self, camera_index: int):
        super().__init__()
        self.setWindowTitle("Deep-Live-Cam Live Preview")
        self.resize(PREVIEW_DEFAULT_WIDTH, PREVIEW_DEFAULT_HEIGHT)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._image_label, 1)

        self._virtual_cam: Optional[VirtualCameraSink] = None
        self._capture_worker: Optional[_CaptureWorker] = None
        self._processing_worker: Optional[_ProcessingWorker] = None
        self._timer: Optional[QTimer] = None
        self._shutdown_timer: Optional[QTimer] = None
        self._stop_event = threading.Event()
        self._shutdown_started = False
        self._close_ready = False
        capture_width = modules.globals.camera_width or PREVIEW_DEFAULT_WIDTH
        capture_height = modules.globals.camera_height or PREVIEW_DEFAULT_HEIGHT
        capture_fps = modules.globals.camera_fps or 60
        if modules.globals.virtual_cam:
            capture_width = modules.globals.camera_width or modules.globals.virtual_cam_width
            capture_height = modules.globals.camera_height or modules.globals.virtual_cam_height
            capture_fps = modules.globals.camera_fps or modules.globals.virtual_cam_fps
            self._virtual_cam = VirtualCameraSink.from_globals(
                status_callback=update_status
            )
            self._virtual_cam.start()

        self._cap = VideoCapturer(camera_index)
        if not self._cap.start(capture_width, capture_height, capture_fps):
            update_status("Failed to start camera")
            QTimer.singleShot(0, self.close)
            return

        camera_fps = self._cap.actual_fps
        print(
            f"[webcam] Camera running at {self._cap.actual_width}x"
            f"{self._cap.actual_height}@{camera_fps:.0f}fps"
        )

        self._capture_queue: queue.Queue = queue.Queue(maxsize=2)
        self._processed_queue: queue.Queue = queue.Queue(maxsize=2)
        self._metrics: Optional[PipelineMetrics] = (
            PipelineMetrics("live")
            if getattr(modules.globals, "benchmark_pipeline", False)
            else None
        )

        self._capture_worker = _CaptureWorker(
            self._cap, self._capture_queue, self._stop_event, self._metrics
        )
        self._processing_worker = _ProcessingWorker(
            self._capture_queue,
            self._processed_queue,
            self._stop_event,
            camera_fps,
            self._virtual_cam,
            self._metrics,
        )
        self._capture_worker.start()
        self._processing_worker.start()

        # Poll at ~2x camera fps so we never block but also don't burn CPU.
        poll_ms = max(1, min(16, int(500 / max(camera_fps, 1))))
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(poll_ms)

    def _tick(self) -> None:
        if self._stop_event.is_set():
            self.close()
            return
        try:
            bgr_frame = self._processed_queue.get_nowait()
        except queue.Empty:
            return
        bgr_frame = fit_image_to_size(bgr_frame, self.width(), self.height())
        self._image_label.setPixmap(_bgr_to_qpixmap(bgr_frame))

    def closeEvent(self, event) -> None:
        if not self._close_ready and self._workers_running():
            event.ignore()
            self.shutdown(block=False)
            return

        self.shutdown(block=True)
        self._finalize_shutdown()
        event.accept()

    def shutdown(self, block: bool = False) -> None:
        if not self._shutdown_started:
            self._shutdown_started = True
            self._stop_event.set()
            update_status("Stopping live preview...")

            if self._timer is not None:
                try:
                    self._timer.stop()
                except Exception:
                    pass

            try:
                self._cap.release()
            except Exception:
                pass

            if not block:
                self.hide()
                self._shutdown_timer = QTimer(self)
                self._shutdown_timer.timeout.connect(self._finish_async_shutdown)
                self._shutdown_timer.start(100)

        if block:
            self._wait_for_workers()

    def _finish_async_shutdown(self) -> None:
        if self._workers_running():
            return
        self._wait_for_workers()
        self._finalize_shutdown()
        self._close_ready = True
        self.close()

    def _wait_for_workers(self) -> None:
        for worker in self._worker_threads():
            if worker.is_alive():
                worker.join()

    def _workers_running(self) -> bool:
        return any(worker.is_alive() for worker in self._worker_threads())

    def _worker_threads(self) -> list[threading.Thread]:
        return [
            worker
            for worker in (self._capture_worker, self._processing_worker)
            if worker is not None
        ]

    def _finalize_shutdown(self) -> None:
        self._stop_event.set()
        try:
            if self._timer is not None:
                self._timer.stop()
            if self._shutdown_timer is not None:
                self._shutdown_timer.stop()
        except Exception:
            pass
        try:
            self._cap.release()
        except Exception:
            pass
        if self._virtual_cam is not None:
            self._virtual_cam.stop()
            self._virtual_cam = None
        global _WEBCAM_PREVIEW
        if _WEBCAM_PREVIEW is self:
            _WEBCAM_PREVIEW = None


def _open_webcam_preview(camera_index: int) -> None:
    global _WEBCAM_PREVIEW
    if _WEBCAM_PREVIEW is not None:
        _WEBCAM_PREVIEW.shutdown(block=True)
        _WEBCAM_PREVIEW.close()
    _WEBCAM_PREVIEW = WebcamPreviewWindow(camera_index)
    _WEBCAM_PREVIEW.show()


# ─── mapper dialogs (image/video + live) ────────────────────────────────


def _make_thumb(cv2_img: np.ndarray) -> QPixmap:
    rgb = gpu_cvt_color(cv2_img, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb).resize(
        (MAPPER_PREVIEW_SIZE, MAPPER_PREVIEW_SIZE), Image.LANCZOS
    )
    return _pil_to_qpixmap(image)


class MapperDialog(QDialog):
    """Source × Target mapper for image / video processing."""

    def __init__(self, start_cb: Callable, mapping: list):
        super().__init__(_MAIN)
        self._start_cb = start_cb
        self._map = mapping
        self.setWindowTitle(_("Source x Target Mapper"))
        self.resize(POPUP_WIDTH, POPUP_HEIGHT)
        layout = QVBoxLayout(self)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        layout.addWidget(self._scroll, 1)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        btn_submit = QPushButton(_("Submit"))
        btn_submit.clicked.connect(self._on_submit)
        layout.addWidget(btn_submit, alignment=Qt.AlignmentFlag.AlignCenter)

        self._rebuild()

    def set_status(self, text: str) -> None:
        self._status.setText(_(text))

    def _rebuild(self) -> None:
        body = QWidget()
        grid = QGridLayout(body)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for item in self._map:
            row = item["id"]
            btn = QPushButton(_("Select source image"))
            btn.setFixedWidth(200)
            btn.clicked.connect(lambda _c, n=row: self._select_source(n))
            grid.addWidget(btn, row, 0)

            src_label = QLabel(f"S-{row}")
            src_label.setFixedSize(MAPPER_PREVIEW_SIZE, MAPPER_PREVIEW_SIZE)
            src_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            src_label.setStyleSheet("border: 1px dashed #555;")
            grid.addWidget(src_label, row, 1)
            if "source" in item:
                src_label.setPixmap(_make_thumb(item["source"]["cv2"]))
                src_label.setText("")

            x_label = QLabel("×")
            x_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(x_label, row, 2)

            tgt_label = QLabel(f"T-{row}")
            tgt_label.setFixedSize(MAPPER_PREVIEW_SIZE, MAPPER_PREVIEW_SIZE)
            tgt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tgt_label.setStyleSheet("border: 1px solid #555;")
            grid.addWidget(tgt_label, row, 3)
            if "target" in item:
                tgt_label.setPixmap(_make_thumb(item["target"]["cv2"]))
                tgt_label.setText("")

        grid.setRowStretch(grid.rowCount(), 1)
        self._scroll.setWidget(body)

    def _select_source(self, row: int) -> None:
        from modules.face_analyser import get_one_face

        path, _f = QFileDialog.getOpenFileName(
            self, _("select an source image"),
            _RECENT_SOURCE_DIR or "",
            IMAGE_FILE_FILTER,
        )
        if not path:
            return
        cv2_img = read_image(path)
        face = get_one_face(cv2_img)
        if face is None:
            self.set_status("Face could not be detected in last upload!")
            return
        x_min, y_min, x_max, y_max = face["bbox"]
        self._map[row]["source"] = {
            "cv2": cv2_img[int(y_min):int(y_max), int(x_min):int(x_max)],
            "face": face,
        }
        self._rebuild()

    def _on_submit(self) -> None:
        from modules.face_analyser import has_valid_map

        if has_valid_map():
            self.accept()
            _MAIN._select_output_and_start()
        else:
            self.set_status("Atleast 1 source with target is required!")


class LiveMapperDialog(QDialog):
    """Source × Target mapper for live webcam mode."""

    def __init__(self, camera_index: int, mapping: list):
        super().__init__(_MAIN)
        self._camera_index = camera_index
        self._map = mapping
        self.setWindowTitle(_("Source x Target Mapper"))
        self.resize(POPUP_LIVE_WIDTH, POPUP_LIVE_HEIGHT)
        layout = QVBoxLayout(self)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        layout.addWidget(self._scroll, 1)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        btn_row = QHBoxLayout()
        for text, slot in (
            (_("Add"), self._on_add),
            (_("Clear"), self._on_clear),
            (_("Submit"), self._on_submit),
        ):
            b = QPushButton(text)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self._rebuild()

    def set_status(self, text: str) -> None:
        self._status.setText(_(text))

    def _rebuild(self) -> None:
        body = QWidget()
        grid = QGridLayout(body)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for item in self._map:
            row = item["id"]
            btn_s = QPushButton(_("Select source image"))
            btn_s.setFixedWidth(200)
            btn_s.clicked.connect(lambda _c, n=row: self._select_face(n, "source"))
            grid.addWidget(btn_s, row, 0)

            src_label = QLabel(f"S-{row}")
            src_label.setFixedSize(MAPPER_PREVIEW_SIZE, MAPPER_PREVIEW_SIZE)
            src_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            src_label.setStyleSheet("border: 1px dashed #555;")
            grid.addWidget(src_label, row, 1)
            if "source" in item:
                src_label.setPixmap(_make_thumb(item["source"]["cv2"]))
                src_label.setText("")

            x_label = QLabel("×")
            x_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(x_label, row, 2)

            btn_t = QPushButton(_("Select target image"))
            btn_t.setFixedWidth(200)
            btn_t.clicked.connect(lambda _c, n=row: self._select_face(n, "target"))
            grid.addWidget(btn_t, row, 3)

            tgt_label = QLabel(f"T-{row}")
            tgt_label.setFixedSize(MAPPER_PREVIEW_SIZE, MAPPER_PREVIEW_SIZE)
            tgt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tgt_label.setStyleSheet("border: 1px dashed #555;")
            grid.addWidget(tgt_label, row, 4)
            if "target" in item:
                tgt_label.setPixmap(_make_thumb(item["target"]["cv2"]))
                tgt_label.setText("")

        grid.setRowStretch(grid.rowCount(), 1)
        self._scroll.setWidget(body)

    def _select_face(self, row: int, kind: str) -> None:
        from modules.face_analyser import get_one_face

        path, _f = QFileDialog.getOpenFileName(
            self, _("select an source image"),
            _RECENT_SOURCE_DIR or "",
            IMAGE_FILE_FILTER,
        )
        if not path:
            return
        cv2_img = read_image(path)
        face = get_one_face(cv2_img)
        if face is None:
            self.set_status("Face could not be detected in last upload!")
            return
        x_min, y_min, x_max, y_max = face["bbox"]
        self._map[row][kind] = {
            "cv2": cv2_img[int(y_min):int(y_max), int(x_min):int(x_max)],
            "face": face,
        }
        self._rebuild()

    def _on_add(self) -> None:
        from modules.face_analyser import add_blank_map

        add_blank_map()
        self._rebuild()
        self.set_status("Please provide mapping!")

    def _on_clear(self) -> None:
        for item in self._map:
            item.pop("source", None)
            item.pop("target", None)
        self._rebuild()
        self.set_status("All mappings cleared!")

    def _on_submit(self) -> None:
        from modules.face_analyser import has_valid_map, simplify_maps

        if has_valid_map():
            simplify_maps()
            self.set_status("Mappings successfully submitted!")
            self.accept()
            _open_webcam_preview(self._camera_index)
        else:
            self.set_status("At least 1 source with target is required!")


def _open_mapper_dialog(start_cb: Callable, mapping: list) -> None:
    global _MAPPER
    close_mapper_window()
    _MAPPER = MapperDialog(start_cb, mapping)
    _MAPPER.show()


def _open_live_mapper_dialog(camera_index: int, mapping: list) -> None:
    global _LIVE_MAPPER
    close_mapper_window()
    _LIVE_MAPPER = LiveMapperDialog(camera_index, mapping)
    _LIVE_MAPPER.show()


def close_mapper_window() -> None:
    global _MAPPER, _LIVE_MAPPER
    if _MAPPER is not None:
        _MAPPER.close()
        _MAPPER = None
    if _LIVE_MAPPER is not None:
        _LIVE_MAPPER.close()
        _LIVE_MAPPER = None


# ─── entry point ─────────────────────────────────────────────────────────


class _Window:
    """Thin wrapper exposing .mainloop() for core.py compatibility."""

    def __init__(self, app: QApplication, main_window: MainWindow):
        self._app = app
        self._main = main_window

    def mainloop(self) -> None:
        self._main.show()
        self._app.exec()


def init(start: Callable[[], None], destroy: Callable[[], None]) -> _Window:
    global _APP, _MAIN, _PREVIEW, _BRIDGE

    if QApplication.instance() is None:
        _APP = QApplication(sys.argv)
    else:
        _APP = QApplication.instance()
    _APP.setStyleSheet(QSS)
    _APP.setWindowIcon(app_icon())

    _BRIDGE = _UIBridge()
    _MAIN = MainWindow(start, destroy)
    _PREVIEW = PreviewWindow()

    # Route status updates onto the UI thread regardless of caller.
    _BRIDGE.statusChanged.connect(_MAIN.set_status)

    return _Window(_APP, _MAIN)
