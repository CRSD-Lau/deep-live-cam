import os
import subprocess
import sys
import importlib
import time
from concurrent.futures import ThreadPoolExecutor
from types import ModuleType
from typing import Any, List, Callable

import numpy as np
from tqdm import tqdm

import modules
import modules.globals
from modules.enhancement_registry import ENHANCER_KEYS
from modules.execution_providers import provider_config_summary
from modules.face_analyser import get_one_face
from modules.pipeline_metrics import (
    MetricsJsonlWriter,
    PipelineMetrics,
    format_metrics,
    safe_write_metrics_snapshot,
)
from modules.processors.frame.processor_dispatch import process_frame_with_target
from modules.tracking.face_track import FaceTracker
from modules.visual_qa import TemporalQACaptureSession, VisualQACaptureSession
from modules.utilities import read_image

FRAME_PROCESSORS_MODULES: List[ModuleType] = []
FRAME_PROCESSORS_INTERFACE = [
    'pre_check',
    'pre_start',
    'process_frame',
    'process_image',
    'process_video'
]

ALLOWED_PROCESSORS = {'face_swapper', *ENHANCER_KEYS}

def load_frame_processor_module(frame_processor: str) -> Any:
    if frame_processor not in ALLOWED_PROCESSORS:
        print(f"Frame processor {frame_processor} is not allowed")
        sys.exit()
    try:
        frame_processor_module = importlib.import_module(f'modules.processors.frame.{frame_processor}')
        for method_name in FRAME_PROCESSORS_INTERFACE:
            if not hasattr(frame_processor_module, method_name):
                sys.exit()
    except ImportError:
        print(f"Frame processor {frame_processor} not found")
        sys.exit()
    return frame_processor_module


def get_frame_processors_modules(frame_processors: List[str]) -> List[ModuleType]:
    global FRAME_PROCESSORS_MODULES

    if not FRAME_PROCESSORS_MODULES:
        for frame_processor in frame_processors:
            frame_processor_module = load_frame_processor_module(frame_processor)
            FRAME_PROCESSORS_MODULES.append(frame_processor_module)
    set_frame_processors_modules_from_ui(frame_processors)
    return FRAME_PROCESSORS_MODULES

def set_frame_processors_modules_from_ui(frame_processors: List[str]) -> None:
    global FRAME_PROCESSORS_MODULES
    current_processor_names = [proc.__name__.split('.')[-1] for proc in FRAME_PROCESSORS_MODULES]

    for frame_processor, state in modules.globals.fp_ui.items():
        if state == True and frame_processor not in current_processor_names:
            try:
                frame_processor_module = load_frame_processor_module(frame_processor)
                FRAME_PROCESSORS_MODULES.append(frame_processor_module)
                if frame_processor not in modules.globals.frame_processors:
                     modules.globals.frame_processors.append(frame_processor)
            except SystemExit:
                 print(f"Warning: Failed to load frame processor {frame_processor} requested by UI state.")
            except Exception as e:
                 print(f"Warning: Error loading frame processor {frame_processor} requested by UI state: {e}")

        elif state == False and frame_processor in current_processor_names:
            try:
                module_to_remove = next((mod for mod in FRAME_PROCESSORS_MODULES if mod.__name__.endswith(f'.{frame_processor}')), None)
                if module_to_remove:
                    FRAME_PROCESSORS_MODULES.remove(module_to_remove)
                if frame_processor in modules.globals.frame_processors:
                    modules.globals.frame_processors.remove(frame_processor)
            except Exception as e:
                 print(f"Warning: Error removing frame processor {frame_processor}: {e}")


def reset_frame_processor_temporal_state(frame_processors: List[Any]) -> None:
    for frame_processor in frame_processors:
        if hasattr(frame_processor, 'PREVIOUS_FRAME_RESULT'):
            frame_processor.PREVIOUS_FRAME_RESULT = None
        reset_compositing = getattr(
            frame_processor,
            "reset_compositing_temporal_state",
            None,
        )
        if callable(reset_compositing):
            reset_compositing()


def multi_process_frame(source_path: str, temp_frame_paths: List[str], process_frames: Callable[[str, List[str], Any], None], progress: Any = None) -> None:
    """Process frames in parallel with optimized batching and memory management."""
    max_workers = modules.globals.execution_threads
    
    # Determine optimal batch size based on available memory and thread count
    # Process frames in batches to avoid memory overflow
    batch_size = max(1, min(32, len(temp_frame_paths) // max(1, max_workers)))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Process in batches to manage memory better
        for i in range(0, len(temp_frame_paths), batch_size):
            batch = temp_frame_paths[i:i + batch_size]
            futures = []
            
            for path in batch:
                future = executor.submit(process_frames, source_path, [path], progress)
                futures.append(future)
            
            # Wait for batch to complete before starting next batch
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing frame: {e}")


def process_video(source_path: str, frame_paths: list[str], process_frames: Callable[[str, List[str], Any], None]) -> None:
    progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    total = len(frame_paths)
    with tqdm(total=total, desc='Processing', unit='frame', dynamic_ncols=True, bar_format=progress_bar_format) as progress:
        progress.set_postfix({'execution_providers': modules.globals.execution_providers, 'execution_threads': modules.globals.execution_threads, 'max_memory': modules.globals.max_memory})
        multi_process_frame(source_path, frame_paths, process_frames, progress)


def process_video_in_memory(source_path: str, target_path: str, fps: float) -> bool:
    """Process video frames in-memory using FFmpeg pipes, eliminating disk I/O.

    Reads raw frames from the source video via an FFmpeg decoder pipe, runs each
    frame through all active frame processors sequentially, and writes the
    result directly to an FFmpeg encoder pipe.  This avoids extracting frames to
    PNG on disk, which is the biggest I/O bottleneck in the disk-based pipeline.

    Returns True on success, False on failure (caller should fall back to the
    disk-based pipeline).
    """
    from modules.face_analyser import get_one_face
    from modules.utilities import (
        get_video_dimensions,
        estimate_frame_count,
        get_temp_output_path,
    )

    temp_output_path = get_temp_output_path(target_path)

    # --- Pre-load source face (needed by face_swapper in simple mode) ---
    source_face = None
    if source_path and os.path.exists(source_path):
        source_img = read_image(source_path)
        if source_img is not None:
            source_face = get_one_face(source_img)
            del source_img
        if source_face is None:
            print("[DLC.CORE] Warning: No face detected in source image. "
                  "Face swapping will be skipped.")

    # --- Collect frame processors & reset per-video state ---
    frame_processors = get_frame_processors_modules(modules.globals.frame_processors)
    reset_frame_processor_temporal_state(frame_processors)

    # --- Video metadata ---
    try:
        width, height = get_video_dimensions(target_path)
    except Exception as e:
        print(f"[DLC.CORE] Failed to get video dimensions: {e}")
        return False

    total_frames = estimate_frame_count(target_path, fps)
    frame_size = width * height * 3

    # --- Build encoder arguments ---
    encoder = modules.globals.video_encoder
    encoder_options: List[str] = []
    is_hw_encoder = False

    if 'CUDAExecutionProvider' in modules.globals.execution_providers:
        if encoder == 'libx264':
            encoder = 'h264_nvenc'
            is_hw_encoder = True
            encoder_options = [
                '-preset', 'p4', '-tune', 'hq', '-rc', 'vbr',
                '-cq', str(modules.globals.video_quality), '-b:v', '0',
            ]
        elif encoder == 'libx265':
            encoder = 'hevc_nvenc'
            is_hw_encoder = True
            encoder_options = [
                '-preset', 'p4', '-tune', 'hq', '-rc', 'vbr',
                '-cq', str(modules.globals.video_quality), '-b:v', '0',
            ]
    elif 'DmlExecutionProvider' in modules.globals.execution_providers:
        if encoder == 'libx264':
            encoder = 'h264_amf'
            is_hw_encoder = True
            encoder_options = [
                '-quality', 'quality', '-rc', 'vbr_latency',
                '-qp_i', str(modules.globals.video_quality),
                '-qp_p', str(modules.globals.video_quality),
            ]
        elif encoder == 'libx265':
            encoder = 'hevc_amf'
            is_hw_encoder = True
            encoder_options = [
                '-quality', 'quality', '-rc', 'vbr_latency',
                '-qp_i', str(modules.globals.video_quality),
                '-qp_p', str(modules.globals.video_quality),
            ]

    if not is_hw_encoder:
        if encoder == 'libx264':
            encoder_options = [
                '-preset', 'medium',
                '-crf', str(modules.globals.video_quality),
                '-tune', 'film',
            ]
        elif encoder == 'libx265':
            encoder_options = [
                '-preset', 'medium',
                '-crf', str(modules.globals.video_quality),
                '-x265-params', 'log-level=error',
            ]
        elif encoder == 'libvpx-vp9':
            encoder_options = [
                '-crf', str(modules.globals.video_quality),
                '-b:v', '0', '-cpu-used', '2',
            ]

    # --- Attempt pipeline (hw encoder first, then sw fallback) ---
    encoders_to_try = [(encoder, encoder_options)]
    if is_hw_encoder:
        # Software fallback
        sw_encoder = 'libx264'
        sw_options = [
            '-preset', 'medium',
            '-crf', str(modules.globals.video_quality),
            '-tune', 'film',
        ]
        encoders_to_try.append((sw_encoder, sw_options))

    for attempt, (enc, enc_opts) in enumerate(encoders_to_try):
        # Reset interpolation state on retry
        if attempt > 0:
            reset_frame_processor_temporal_state(frame_processors)

        success = _run_pipe_pipeline(
            target_path, temp_output_path, fps,
            source_face, frame_processors,
            width, height, frame_size, total_frames,
            enc, enc_opts,
        )
        if success:
            return True

        if attempt == 0 and is_hw_encoder:
            print(f"[DLC.CORE] Hardware encoder '{enc}' failed, "
                  f"retrying with software encoder...")

    return False


def _run_pipe_pipeline(
    target_path: str,
    temp_output_path: str,
    fps: float,
    source_face: Any,
    frame_processors: List[Any],
    width: int,
    height: int,
    frame_size: int,
    total_frames: int,
    encoder: str,
    encoder_options: List[str],
) -> bool:
    """Run the FFmpeg-pipe read → process → encode pipeline once."""

    # --- Reader: decode source video to raw BGR24 on stdout ---
    reader_cmd = [
        'ffmpeg', '-hide_banner',
        '-hwaccel', 'auto',
        '-i', target_path,
        '-f', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-v', 'error',
        '-',
    ]

    # --- Writer: encode raw BGR24 from stdin ---
    writer_cmd = [
        'ffmpeg', '-hide_banner',
        '-f', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f'{width}x{height}',
        '-r', str(fps),
        '-i', '-',
        '-c:v', encoder,
    ]
    writer_cmd.extend(encoder_options)
    writer_cmd.extend([
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-vf', 'colorspace=bt709:iall=bt601-6-625:fast=1',
        '-v', 'error',
        '-y', temp_output_path,
    ])

    reader = None
    writer = None
    try:
        reader = subprocess.Popen(
            reader_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        writer = subprocess.Popen(
            writer_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(f"[DLC.CORE] Failed to start FFmpeg pipes: {e}")
        for proc in (reader, writer):
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
        return False

    processed_count = 0
    metrics = (
        PipelineMetrics("video")
        if getattr(modules.globals, "benchmark_pipeline", False)
        else None
    )
    metrics_context = {
        "quality_mode": getattr(modules.globals, "quality_mode", None),
        "frame_processors": [
            getattr(fp, "NAME", None)
            or getattr(fp, "__name__", type(fp).__name__).split(".")[-1]
            for fp in frame_processors
        ],
        "target_path": target_path,
        "encoder": encoder,
        "fps": fps,
        "resolution": [width, height],
        "mode": "in-memory",
        "execution_providers": list(modules.globals.execution_providers),
        "execution_provider_config": provider_config_summary(
            modules.globals.execution_providers
        ),
    }
    metrics_writer = (
        MetricsJsonlWriter(modules.globals.benchmark_output_path)
        if metrics
        and getattr(modules.globals, "benchmark_output_path", None)
        else None
    )
    visual_qa_session = None
    temporal_qa_session = None
    visual_qa_output_dir = getattr(modules.globals, "visual_qa_output_dir", None)
    if visual_qa_output_dir:
        visual_qa_notes = {
            "quality_mode": getattr(modules.globals, "quality_mode", None),
            "frame_processors": [
                getattr(fp, "NAME", None)
                or getattr(fp, "__name__", type(fp).__name__).split(".")[-1]
                for fp in frame_processors
            ],
            "target_path": target_path,
            "encoder": encoder,
            "fps": fps,
        }
        visual_qa_session = VisualQACaptureSession(
            visual_qa_output_dir,
            getattr(modules.globals, "visual_qa_frame_indices", [0]),
            notes=visual_qa_notes,
        )
        if getattr(modules.globals, "visual_qa_temporal", False):
            temporal_qa_session = TemporalQACaptureSession(
                visual_qa_output_dir,
                getattr(modules.globals, "visual_qa_frame_indices", [0]),
                notes=visual_qa_notes,
            )
    bar_fmt = ('{l_bar}{bar}| {n_fmt}/{total_fmt} '
               '[{elapsed}<{remaining}, {rate_fmt}{postfix}]')

    try:
        with tqdm(total=total_frames, desc='Processing', unit='frame',
                  dynamic_ncols=True, bar_format=bar_fmt) as progress:
            progress.set_postfix({
                'execution_providers': modules.globals.execution_providers,
                'threads': modules.globals.execution_threads,
                'mode': 'in-memory',
            })

            # Pipelined detection: while processing frame N (swap on
            # ANE), start detecting the face in the next frame
            # (detection on GPU).  They use different hardware units
            # so the work overlaps.
            detect_executor = ThreadPoolExecutor(max_workers=1)
            pending_detect = None
            use_pipeline = not modules.globals.many_faces
            face_tracker = (
                FaceTracker(
                    current_weight=getattr(
                        modules.globals, "face_tracking_current_weight", 0.7
                    ),
                    jump_reset_ratio=getattr(
                        modules.globals, "face_tracking_reset_ratio", 1.2
                    ),
                    max_missed=getattr(
                        modules.globals, "face_tracking_max_missed", 1
                    ),
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
                )
                if use_pipeline
                and getattr(modules.globals, "face_tracking_enabled", True)
                else None
            )

            while True:
                frame_index = processed_count
                read_started = time.perf_counter()
                raw = reader.stdout.read(frame_size)
                if metrics:
                    metrics.observe("decode_read", time.perf_counter() - read_started)
                if len(raw) != frame_size:
                    break

                frame = np.frombuffer(raw, dtype=np.uint8).reshape(
                    (height, width, 3)
                ).copy()
                visual_qa_before = (
                    frame.copy()
                    if visual_qa_session
                    and visual_qa_session.should_capture(frame_index)
                    else None
                )

                # Get the detection result for THIS frame
                if use_pipeline:
                    if pending_detect is not None:
                        pending_future, detection_frame_index = pending_detect
                        detect_wait_started = time.perf_counter()
                        detected_face = pending_future.result()
                        if metrics:
                            metrics.observe(
                                "detect_wait",
                                time.perf_counter() - detect_wait_started,
                            )
                    else:
                        detection_frame_index = frame_index
                        detect_started = time.perf_counter()
                        detected_face = get_one_face(frame)
                        if metrics:
                            metrics.observe(
                                "detect_direct",
                                time.perf_counter() - detect_started,
                            )
                    if face_tracker is not None:
                        target_face = face_tracker.update(
                            detected_face, detection_frame_index
                        )
                    else:
                        target_face = detected_face
                    # Start detecting on THIS frame eagerly — the result
                    # will be used for the next iteration.  At video
                    # frame rates the face barely moves between frames.
                    # Hand the detector its own copy: the frame processors
                    # below mutate `frame` in place (paste-back), which
                    # would otherwise race with detection.
                    pending_detect = (
                        detect_executor.submit(get_one_face, frame.copy()),
                        frame_index,
                    )
                else:
                    target_face = None

                # Run frame through every active processor
                for fp in frame_processors:
                    processor_started = time.perf_counter()
                    try:
                        frame = process_frame_with_target(
                            fp, source_face, frame, target_face
                        )
                    finally:
                        if metrics:
                            metrics.observe(
                                fp.NAME,
                                time.perf_counter() - processor_started,
                            )

                if visual_qa_before is not None:
                    try:
                        visual_qa_session.capture(
                            frame_index, visual_qa_before, frame
                        )
                    except Exception as exc:
                        print(
                            f"[DLC.CORE] Visual QA capture failed for "
                            f"frame {frame_index}: {exc}",
                            flush=True,
                        )
                if temporal_qa_session and temporal_qa_session.should_capture(frame_index):
                    try:
                        temporal_qa_session.capture(frame_index, frame)
                    except Exception as exc:
                        print(
                            f"[DLC.CORE] Temporal QA capture failed for "
                            f"frame {frame_index}: {exc}",
                            flush=True,
                        )

                encode_started = time.perf_counter()
                writer.stdin.write(frame.tobytes())
                if metrics:
                    metrics.observe("encode_write", time.perf_counter() - encode_started)
                    metrics.frame_complete()
                    if metrics.should_report(modules.globals.benchmark_log_interval):
                        print(format_metrics(metrics), flush=True)
                        safe_write_metrics_snapshot(
                            metrics_writer,
                            metrics,
                            event="periodic",
                            extra=metrics_context,
                        )
                        metrics.mark_reported()
                processed_count += 1
                progress.update(1)

            detect_executor.shutdown(wait=True)

        # Graceful shutdown
        writer.stdin.close()
        writer.wait()
        reader.wait()

        if writer.returncode != 0:
            stderr_out = writer.stderr.read().decode(errors='ignore').strip()
            if stderr_out:
                print(f"[DLC.CORE] FFmpeg encoder error: {stderr_out}")
            return False

        if temporal_qa_session is not None:
            try:
                temporal_result = temporal_qa_session.export()
                if temporal_result is not None:
                    print(
                        f"[DLC.CORE] Temporal QA export written to "
                        f"{temporal_result.output_dir}",
                        flush=True,
                    )
            except Exception as exc:
                print(f"[DLC.CORE] Temporal QA export failed: {exc}", flush=True)

        if metrics:
            print(format_metrics(metrics), flush=True)
            safe_write_metrics_snapshot(
                metrics_writer,
                metrics,
                event="final",
                extra=metrics_context,
            )
        return processed_count > 0 and os.path.isfile(temp_output_path)

    except BrokenPipeError:
        print("[DLC.CORE] FFmpeg pipe broken (encoder may not be available).")
        return False
    except Exception as e:
        print(f"[DLC.CORE] In-memory processing error: {e}")
        return False
    finally:
        for proc in (reader, writer):
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
