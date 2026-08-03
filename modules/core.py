import os
import sys
# single thread doubles cuda performance - needs to be set before torch import
if any(arg.startswith('--execution-provider') for arg in sys.argv):
    os.environ['OMP_NUM_THREADS'] = '6'
# reduce tensorflow log level
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import warnings
import platform
import signal
import shutil
import argparse

import modules.globals
import modules.metadata
from modules.enhancement_registry import ENHANCER_KEYS
from modules.execution_providers import (
    build_provider_config,
    encode_providers,
    missing_requested_providers,
    probe_execution_providers,
    resolve_execution_providers,
    supported_provider_aliases,
)
from modules.quality_profiles import QUALITY_MODE_NAMES, apply_quality_profile
from modules.utilities import has_image_extension, is_image, is_video, detect_fps, create_video, extract_frames, get_temp_frame_paths, restore_audio, create_temp, move_temp, clean_temp, normalize_output_path
from modules.diagnostics.overlays import parse_overlay_layers
from modules.visual_qa import parse_frame_selection

FRAME_PROCESSOR_CHOICES = ("face_swapper",) + ENHANCER_KEYS

warnings.filterwarnings('ignore', category=FutureWarning, module='insightface')
warnings.filterwarnings('ignore', category=UserWarning, module='torchvision')


def parse_args() -> None:
    signal.signal(signal.SIGINT, lambda _signal_number, _frame: destroy())
    program = argparse.ArgumentParser()
    program.add_argument('-s', '--source', help='select an source image', dest='source_path')
    program.add_argument('-t', '--target', help='select an target image or video', dest='target_path')
    program.add_argument('-o', '--output', help='select output file or directory', dest='output_path')
    program.add_argument('--frame-processor', help='pipeline of frame processors', dest='frame_processor', default=['face_swapper'], choices=FRAME_PROCESSOR_CHOICES, nargs='+')
    program.add_argument('--keep-fps', help='keep original fps', dest='keep_fps', action='store_true', default=False)
    program.add_argument('--keep-audio', help='keep original audio', dest='keep_audio', action='store_true', default=True)
    program.add_argument('--keep-frames', help='keep temporary frames', dest='keep_frames', action='store_true', default=False)
    program.add_argument('--many-faces', help='process every face', dest='many_faces', action='store_true', default=False)
    program.add_argument('--nsfw-filter', help='filter the NSFW image or video', dest='nsfw_filter', action='store_true', default=False)
    program.add_argument('--map-faces', help='map source target faces', dest='map_faces', action='store_true', default=False)
    program.add_argument('--mouth-mask', help='mask the mouth region', dest='mouth_mask', action='store_true', default=False)
    program.add_argument('--quality-mode', help='quality/performance profile', dest='quality_mode', choices=QUALITY_MODE_NAMES)
    program.add_argument('--benchmark-pipeline', help='print live/video pipeline stage timing summaries', dest='benchmark_pipeline', action='store_true', default=False)
    program.add_argument('--benchmark-log-interval', help='seconds between benchmark summaries', dest='benchmark_log_interval', type=float, default=5.0)
    program.add_argument('--benchmark-output', help='append benchmark snapshots as JSONL at the selected path', dest='benchmark_output_path')
    program.add_argument('--visual-qa-dir', help='export before/after QA snapshots during in-memory video processing', dest='visual_qa_output_dir')
    program.add_argument('--visual-qa-frames', help='comma-separated zero-based frames to capture when --visual-qa-dir is set', dest='visual_qa_frames', default='0')
    program.add_argument('--visual-qa-temporal', help='export temporal flicker/jitter QA across selected --visual-qa-frames', dest='visual_qa_temporal', action='store_true', default=False)
    program.add_argument('--diagnostic-overlay', help='draw debug overlays on processed face frames', dest='diagnostic_overlay', action='store_true', default=False)
    program.add_argument('--diagnostic-overlay-layers', help='comma-separated overlay layers: bbox,kps,landmarks,mouth,eyes,mask,profile,all', dest='diagnostic_overlay_layers', default='bbox,kps,profile')
    program.add_argument('--video-encoder', help='adjust output video encoder', dest='video_encoder', default='libx264', choices=['libx264', 'libx265', 'libvpx-vp9'])
    program.add_argument('--video-quality', help='adjust output video quality', dest='video_quality', type=int, default=18, choices=range(52), metavar='[0-51]')
    program.add_argument('--live-mirror', help='The live camera display as you see it in the front-facing camera frame', dest='live_mirror', action='store_true', default=False)
    program.add_argument('--live-resizable', help='The live camera frame is resizable', dest='live_resizable', action='store_true', default=False)
    program.add_argument('--camera-width', help='live camera capture width; overrides the virtual camera width for processing', dest='camera_width', type=positive_int)
    program.add_argument('--camera-height', help='live camera capture height; overrides the virtual camera height for processing', dest='camera_height', type=positive_int)
    program.add_argument('--camera-fps', help='live camera capture fps; overrides the virtual camera fps for processing', dest='camera_fps', type=positive_int)
    program.add_argument('--virtual-cam', help='send processed live preview frames to a virtual camera', dest='virtual_cam', action='store_true', default=False)
    program.add_argument('--virtual-cam-name', help='virtual camera device name to use, for example "OBS Virtual Camera"', dest='virtual_cam_name')
    program.add_argument('--virtual-cam-width', help='virtual camera output width', dest='virtual_cam_width', type=positive_int, default=1280)
    program.add_argument('--virtual-cam-height', help='virtual camera output height', dest='virtual_cam_height', type=positive_int, default=720)
    program.add_argument('--virtual-cam-fps', help='virtual camera output fps', dest='virtual_cam_fps', type=positive_int, default=30)
    program.add_argument('--max-memory', help='maximum amount of RAM in GB', dest='max_memory', type=int, default=suggest_max_memory())
    program.add_argument('--execution-provider', help=f'execution provider ({", ".join(suggest_execution_providers())})', dest='execution_provider', default=[suggest_default_execution_provider()], metavar='PROVIDER', nargs='+')
    program.add_argument('--directml-device-id', help='DirectML adapter index (0 is the Windows default GPU)', dest='directml_device_id', type=non_negative_int, default=0)
    program.add_argument('--execution-threads', help='number of execution threads', dest='execution_threads', type=int)
    program.add_argument('--check-execution-provider', help='run a real ONNX inference with the requested provider and exit', dest='check_execution_provider', action='store_true', default=False)
    program.add_argument('--download-models', help='review model sources, download models, and verify checksums', dest='download_models', action='store_true', default=False)
    program.add_argument('--yes', help='assume yes for non-interactive setup commands such as --download-models', dest='assume_yes', action='store_true', default=False)
    program.add_argument('-v', '--version', action='version', version=f'{modules.metadata.name} {modules.metadata.version}')

    # register deprecated args
    program.add_argument('-f', '--face', help=argparse.SUPPRESS, dest='source_path_deprecated')
    program.add_argument('--cpu-cores', help=argparse.SUPPRESS, dest='cpu_cores_deprecated', type=int)
    program.add_argument('--gpu-vendor', help=argparse.SUPPRESS, dest='gpu_vendor_deprecated')
    program.add_argument('--gpu-threads', help=argparse.SUPPRESS, dest='gpu_threads_deprecated', type=int)

    args = program.parse_args()
    try:
        visual_qa_frame_indices = parse_frame_selection(args.visual_qa_frames)
    except ValueError as exc:
        program.error(f"invalid --visual-qa-frames: {exc}")
    if args.visual_qa_temporal and not args.visual_qa_output_dir:
        program.error("--visual-qa-temporal requires --visual-qa-dir")
    try:
        diagnostic_overlay_layers = parse_overlay_layers(args.diagnostic_overlay_layers)
    except ValueError as exc:
        program.error(f"invalid --diagnostic-overlay-layers: {exc}")

    modules.globals.download_models = args.download_models
    modules.globals.assume_yes = args.assume_yes
    modules.globals.source_path = args.source_path
    modules.globals.target_path = args.target_path
    modules.globals.output_path = normalize_output_path(modules.globals.source_path, modules.globals.target_path, args.output_path)
    modules.globals.frame_processors = args.frame_processor
    modules.globals.headless = bool(
        args.source_path
        or args.target_path
        or args.output_path
        or args.check_execution_provider
    )
    modules.globals.keep_fps = args.keep_fps
    modules.globals.keep_audio = args.keep_audio
    modules.globals.keep_frames = args.keep_frames
    modules.globals.many_faces = args.many_faces
    modules.globals.mouth_mask = args.mouth_mask
    modules.globals.nsfw_filter = args.nsfw_filter
    modules.globals.map_faces = args.map_faces
    modules.globals.quality_mode = args.quality_mode or modules.globals.quality_mode
    modules.globals.benchmark_pipeline = args.benchmark_pipeline or bool(args.benchmark_output_path)
    modules.globals.benchmark_log_interval = max(0.5, args.benchmark_log_interval)
    modules.globals.benchmark_output_path = args.benchmark_output_path
    modules.globals.visual_qa_output_dir = args.visual_qa_output_dir
    modules.globals.visual_qa_frame_indices = sorted(visual_qa_frame_indices)
    modules.globals.visual_qa_temporal = args.visual_qa_temporal
    modules.globals.diagnostic_overlay = args.diagnostic_overlay
    modules.globals.diagnostic_overlay_layers = diagnostic_overlay_layers
    modules.globals.video_encoder = args.video_encoder
    modules.globals.video_quality = args.video_quality
    modules.globals.live_mirror = args.live_mirror
    modules.globals.live_resizable = args.live_resizable
    modules.globals.camera_width = args.camera_width
    modules.globals.camera_height = args.camera_height
    modules.globals.camera_fps = args.camera_fps
    modules.globals.virtual_cam = args.virtual_cam
    modules.globals.virtual_cam_name = args.virtual_cam_name
    modules.globals.virtual_cam_width = args.virtual_cam_width
    modules.globals.virtual_cam_height = args.virtual_cam_height
    modules.globals.virtual_cam_fps = args.virtual_cam_fps
    modules.globals.max_memory = args.max_memory
    modules.globals.requested_execution_providers = list(args.execution_provider)
    modules.globals.execution_providers = decode_execution_providers(args.execution_provider)
    modules.globals.directml_device_id = args.directml_device_id
    modules.globals.check_execution_provider = args.check_execution_provider
    modules.globals.execution_threads = (
        args.execution_threads
        if args.execution_threads is not None
        else suggest_execution_threads(modules.globals.execution_providers)
    )
    #for ENHANCER tumblers:
    for enhancer_key in ENHANCER_KEYS:
        modules.globals.fp_ui[enhancer_key] = enhancer_key in args.frame_processor
    if args.quality_mode:
        apply_quality_profile(args.quality_mode, modules.globals)

    # translate deprecated args
    if args.source_path_deprecated:
        print('\033[33mArgument -f and --face are deprecated. Use -s and --source instead.\033[0m')
        modules.globals.source_path = args.source_path_deprecated
        modules.globals.output_path = normalize_output_path(args.source_path_deprecated, modules.globals.target_path, args.output_path)
    if args.cpu_cores_deprecated:
        print('\033[33mArgument --cpu-cores is deprecated. Use --execution-threads instead.\033[0m')
        modules.globals.execution_threads = args.cpu_cores_deprecated
    if args.gpu_vendor_deprecated == 'apple':
        print('\033[33mArgument --gpu-vendor apple is deprecated. Use --execution-provider coreml instead.\033[0m')
        modules.globals.requested_execution_providers = ['coreml']
        modules.globals.execution_providers = decode_execution_providers(['coreml'])
    if args.gpu_vendor_deprecated == 'nvidia':
        print('\033[33mArgument --gpu-vendor nvidia is deprecated. Use --execution-provider cuda instead.\033[0m')
        modules.globals.requested_execution_providers = ['cuda']
        modules.globals.execution_providers = decode_execution_providers(['cuda'])
    if args.gpu_vendor_deprecated == 'amd':
        amd_provider = 'directml' if platform.system().lower() == 'windows' else 'rocm'
        print(f'\033[33mArgument --gpu-vendor amd is deprecated. Use --execution-provider {amd_provider} instead.\033[0m')
        modules.globals.requested_execution_providers = [amd_provider]
        modules.globals.execution_providers = decode_execution_providers([amd_provider])
    if args.gpu_threads_deprecated:
        print('\033[33mArgument --gpu-threads is deprecated. Use --execution-threads instead.\033[0m')
        modules.globals.execution_threads = args.gpu_threads_deprecated
    elif args.execution_threads is None:
        modules.globals.execution_threads = suggest_execution_threads(
            modules.globals.execution_providers
        )


def positive_int(value: str) -> int:
    try:
        integer = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value} is not an integer") from exc
    if integer < 1:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return integer


def non_negative_int(value: str) -> int:
    try:
        integer = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value} is not an integer") from exc
    if integer < 0:
        raise argparse.ArgumentTypeError("value must be 0 or greater")
    return integer


def encode_execution_providers(execution_providers: list[str]) -> list[str]:
    return encode_providers(execution_providers)


def decode_execution_providers(execution_providers: list[str]) -> list[str]:
    return resolve_execution_providers(
        execution_providers,
        logger=lambda message: print(f"[DLC.CORE] {message}", flush=True),
    )


def suggest_max_memory() -> int:
    if platform.system().lower() == 'darwin':
        return 4
    return 16


def suggest_default_execution_provider() -> str:
    from modules.execution_providers import suggest_default_execution_provider as suggest
    return suggest()


def suggest_execution_providers() -> list[str]:
    return supported_provider_aliases()


def suggest_execution_threads(execution_providers: list[str] | None = None) -> int:
    """Suggest optimal thread count based on hardware and execution provider."""
    import os
    providers = execution_providers or modules.globals.execution_providers
    
    # Get CPU count
    cpu_count = os.cpu_count() or 4
    
    if 'DmlExecutionProvider' in providers:
        return 1
    if 'ROCMExecutionProvider' in providers:
        return 1
    if 'CUDAExecutionProvider' in providers:
        return 2
    
    # For CPU execution, use most cores but leave some for system
    return max(4, min(cpu_count - 2, 16))


def limit_resources() -> None:
    if modules.globals.nsfw_filter:
        _configure_tensorflow_memory_growth()
    # limit memory usage
    if modules.globals.max_memory:
        memory = modules.globals.max_memory * 1024 ** 3
        if platform.system().lower() == 'darwin':
            memory = modules.globals.max_memory * 1024 ** 6
        if platform.system().lower() == 'windows':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, ctypes.c_size_t(memory), ctypes.c_size_t(memory))
        else:
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def release_resources() -> None:
    if 'CUDAExecutionProvider' in modules.globals.execution_providers:
        torch = _try_import_torch()
        if torch is not None:
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass


def _try_import_torch():
    try:
        import torch
        return torch
    except Exception:
        return None


def _configure_tensorflow_memory_growth() -> None:
    try:
        import tensorflow
    except Exception:
        return

    try:
        gpus = tensorflow.config.experimental.list_physical_devices('GPU')
        for gpu in gpus:
            tensorflow.config.experimental.set_memory_growth(gpu, True)
    except Exception:
        pass


def check_execution_provider() -> int:
    """Verify that the requested provider runs inference without CPU-only fallback."""
    configured = build_provider_config(
        modules.globals.execution_providers,
        directml_device_id=modules.globals.directml_device_id,
    )
    try:
        active = probe_execution_providers(configured)
    except Exception as exc:
        update_status(f'Execution provider probe failed: {exc}')
        return 3

    missing = missing_requested_providers(
        modules.globals.requested_execution_providers,
        active,
    )
    update_status(f'Execution provider probe active providers: {active}')
    if missing:
        update_status(
            'Execution provider check failed; requested provider(s) were not active: '
            + ', '.join(missing)
        )
        return 2
    update_status('Execution provider check passed.')
    return 0


def pre_check() -> bool:
    if sys.version_info < (3, 9):
        update_status('Python version is not supported - please upgrade to 3.9 or higher.')
        return False
    if not shutil.which('ffmpeg'):
        message = (
            'ffmpeg is not installed or not on PATH. Video processing and audio '
            'restore require ffmpeg. Install ffmpeg or place ffmpeg.exe and '
            'ffprobe.exe beside the application.'
        )
        update_status(message)
        if modules.globals.headless:
            return False
        return True
    return True


def update_status(message: str, scope: str = 'DLC.CORE') -> None:
    print(f'[{scope}] {message}')
    if not modules.globals.headless:
        import modules.ui as ui
        ui.update_status(message)

def start() -> None:
    """Start processing with performance monitoring."""
    import time
    import modules.ui as ui
    from modules.processors.frame.core import (
        get_frame_processors_modules,
        process_video_in_memory,
    )
    
    start_time = time.time()
    
    for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
        if not frame_processor.pre_start():
            return
    update_status('Processing...')
    
    # process image to image
    if has_image_extension(modules.globals.target_path):
        if modules.globals.nsfw_filter and ui.check_and_ignore_nsfw(modules.globals.target_path, destroy):
            return
        try:
            shutil.copy2(modules.globals.target_path, modules.globals.output_path)
        except Exception as e:
            print("Error copying file:", str(e))
        for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_image(modules.globals.source_path, modules.globals.output_path, modules.globals.output_path)
            release_resources()
        if is_image(modules.globals.target_path):
            elapsed = time.time() - start_time
            update_status(f'Processing to image succeed! (Time: {elapsed:.2f}s)')
        else:
            update_status('Processing to image failed!')
        return
    
    # process image to videos
    if modules.globals.nsfw_filter and ui.check_and_ignore_nsfw(modules.globals.target_path, destroy):
        return

    # Detect FPS early (needed by both pipelines)
    if modules.globals.keep_fps:
        update_status('Detecting fps...')
        fps = detect_fps(modules.globals.target_path)
    else:
        fps = 30.0

    video_created = False

    # --- In-memory pipeline (non-map_faces only) ---
    # Reads frames from FFmpeg pipe, processes in memory, encodes directly.
    # Eliminates all per-frame PNG disk I/O for a major speed-up.
    if not modules.globals.map_faces:
        update_status(f'Processing video in-memory at {fps} fps...')
        create_temp(modules.globals.target_path)

        processing_start = time.time()
        video_created = process_video_in_memory(
            modules.globals.source_path,
            modules.globals.target_path,
            fps,
        )
        processing_time = time.time() - processing_start
        release_resources()

        if video_created:
            update_status(f'In-memory processing + encoding completed in {processing_time:.2f}s')

    # --- Disk-based fallback (required for map_faces, or if pipe failed) ---
    if not video_created:
        if not modules.globals.map_faces:
            update_status('Falling back to disk-based processing...')

        if not modules.globals.map_faces:
            create_temp(modules.globals.target_path)
            update_status('Extracting frames...')
            extract_frames(modules.globals.target_path)

        temp_frame_paths = get_temp_frame_paths(modules.globals.target_path)
        total_frames = len(temp_frame_paths)
        update_status(f'Processing {total_frames} frames with {modules.globals.execution_threads} threads...')

        processing_start = time.time()
        for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_video(modules.globals.source_path, temp_frame_paths)
            release_resources()
        processing_time = time.time() - processing_start
        fps_processing = total_frames / processing_time if processing_time > 0 else 0
        update_status(f'Frame processing completed in {processing_time:.2f}s ({fps_processing:.2f} fps)')

        encoding_start = time.time()
        update_status(f'Creating video with {fps} fps...')
        video_created = create_video(modules.globals.target_path, fps)
        encoding_time = time.time() - encoding_start
        if video_created:
            update_status(f'Video encoding completed in {encoding_time:.2f}s')

    if not video_created:
        update_status('Video encoding failed. No temporary output video was created.')
        clean_temp(modules.globals.target_path)
        return
    
    # handle audio
    if modules.globals.keep_audio:
        if modules.globals.keep_fps:
            update_status('Restoring audio...')
        else:
            update_status('Restoring audio might cause issues as fps are not kept...')
        restore_audio(modules.globals.target_path, modules.globals.output_path)
    else:
        move_temp(modules.globals.target_path, modules.globals.output_path)
    
    # clean and validate
    clean_temp(modules.globals.target_path)
    
    total_time = time.time() - start_time
    if is_video(modules.globals.target_path) and modules.globals.output_path and os.path.isfile(modules.globals.output_path):
        update_status(f'Video processing succeeded! Total time: {total_time:.2f}s')
    else:
        update_status('Processing to video failed!')


def destroy(to_quit=True) -> None:
    if modules.globals.target_path:
        clean_temp(modules.globals.target_path)
    if to_quit: quit()


def run() -> None:
    parse_args()
    if getattr(modules.globals, "check_execution_provider", False):
        raise SystemExit(check_execution_provider())
    if getattr(modules.globals, "download_models", False):
        from modules.model_manager import download_models
        raise SystemExit(download_models(assume_yes=modules.globals.assume_yes))
    if not pre_check():
        return
    if modules.globals.headless:
        from modules.processors.frame.core import get_frame_processors_modules

        for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
            if not frame_processor.pre_check():
                return
    # Pre-load face analyser in main thread before GUI starts
    #from modules.face_analyser import get_face_analyser
    #get_face_analyser()
    limit_resources()
    if modules.globals.headless:
        start()
    else:
        import modules.ui as ui

        window = ui.init(start, destroy)
        window.mainloop()
