import glob
import math
import mimetypes
import os
import shutil
import subprocess
import tempfile
import threading
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import List, Any
from urllib.parse import urlsplit

import cv2
import numpy
from PIL import Image, ImageOps
from tqdm import tqdm

import modules.globals

TEMP_FILE = "temp.mp4"
_TEMP_WORKSPACES: dict[str, str] = {}
_TEMP_WORKSPACES_LOCK = threading.RLock()
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".avif")
IMAGE_FILE_FILTER = "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.avif)"
MEDIA_FILE_FILTER = "Media (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.avif *.mp4 *.mkv)"

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/avif", ".avif")


def run_ffmpeg(args: List[str]) -> bool:
    """Run ffmpeg with hardware acceleration and optimized settings."""
    commands = [
        "ffmpeg",
        "-hide_banner",
        "-hwaccel", "auto",  # Auto-detect hardware acceleration
        "-hwaccel_output_format", "auto",  # Use hardware format when possible
        "-threads", str(modules.globals.execution_threads or 0),  # 0 = auto-detect optimal thread count
        "-loglevel", modules.globals.log_level,
    ]
    commands.extend(args)
    try:
        subprocess.check_output(commands, stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError as error:
        output = error.output.decode(errors="ignore").strip()
        if output:
            print(output)
    except Exception as error:
        print(f"ffmpeg execution failed: {error}")
    return False


def detect_fps(target_path: str) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        target_path,
    ]
    try:
        output = subprocess.check_output(command).decode().strip().split("/")
        numerator, denominator = map(int, output)
        fps = numerator / denominator
        if math.isfinite(fps) and fps > 0:
            return fps
    except (OSError, subprocess.CalledProcessError, ValueError, ZeroDivisionError):
        pass
    return 30.0


def extract_frames(target_path: str) -> bool:
    """Extract frames with hardware acceleration and optimized settings."""
    temp_directory_path = get_temp_directory_path(target_path)
    
    # Write a contiguous image sequence so the later "%04d.png" input pattern
    # used during encoding can consume every frame reliably.
    return run_ffmpeg(
        [
            "-y",
            "-i", target_path,
            "-vf", "format=rgb24",  # Use video filter for format conversion (faster)
            "-vsync", "0",  # Prevent frame duplication
            os.path.join(temp_directory_path, "%04d.png"),
        ]
    )


def create_video(target_path: str, fps: float = 30.0) -> bool:
    """Create video with hardware-accelerated encoding and optimized settings."""
    temp_output_path = get_temp_output_path(target_path)
    temp_directory_path = get_temp_directory_path(target_path)
    
    # Determine optimal encoder based on available hardware
    encoder = modules.globals.video_encoder
    encoder_options = []
    
    # GPU-accelerated encoding options
    if 'CUDAExecutionProvider' in modules.globals.execution_providers:
        # NVIDIA GPU encoding
        if encoder == 'libx264':
            encoder = 'h264_nvenc'
            encoder_options = [
                "-preset", "p7",  # Highest quality preset for NVENC
                "-tune", "hq",  # High quality tuning
                "-rc", "vbr",  # Variable bitrate
                "-cq", str(modules.globals.video_quality),  # Quality level
                "-b:v", "0",  # Let CQ control bitrate
                "-multipass", "fullres",  # Two-pass encoding for better quality
            ]
        elif encoder == 'libx265':
            encoder = 'hevc_nvenc'
            encoder_options = [
                "-preset", "p7",
                "-tune", "hq",
                "-rc", "vbr",
                "-cq", str(modules.globals.video_quality),
                "-b:v", "0",
            ]
    elif 'DmlExecutionProvider' in modules.globals.execution_providers:
        # AMD/Intel GPU encoding (DirectML on Windows)
        if encoder == 'libx264':
            # Try AMD AMF encoder
            encoder = 'h264_amf'
            encoder_options = [
                "-quality", "quality",  # Quality mode
                "-rc", "vbr_latency",
                "-qp_i", str(modules.globals.video_quality),
                "-qp_p", str(modules.globals.video_quality),
            ]
        elif encoder == 'libx265':
            encoder = 'hevc_amf'
            encoder_options = [
                "-quality", "quality",
                "-rc", "vbr_latency",
                "-qp_i", str(modules.globals.video_quality),
                "-qp_p", str(modules.globals.video_quality),
            ]
    else:
        # CPU encoding with optimized settings
        if encoder == 'libx264':
            encoder_options = [
                "-preset", "medium",  # Balance speed/quality
                "-crf", str(modules.globals.video_quality),
                "-tune", "film",  # Optimize for film content
            ]
        elif encoder == 'libx265':
            encoder_options = [
                "-preset", "medium",
                "-crf", str(modules.globals.video_quality),
                "-x265-params", "log-level=error",
            ]
        elif encoder == 'libvpx-vp9':
            encoder_options = [
                "-crf", str(modules.globals.video_quality),
                "-b:v", "0",  # Constant quality mode
                "-cpu-used", "2",  # Speed vs quality (0-5, lower=slower/better)
            ]
    
    # Build ffmpeg command
    ffmpeg_args = [
        "-r", str(fps),
        "-i", os.path.join(temp_directory_path, "%04d.png"),
        "-c:v", encoder,
    ]
    
    # Add encoder-specific options
    ffmpeg_args.extend(encoder_options)
    
    # Add common options
    ffmpeg_args.extend([
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",  # Enable fast start for web playback
        "-vf", "colorspace=bt709:iall=bt601-6-625:fast=1",
        "-y",
        temp_output_path,
    ])
    
    # Try with hardware encoder first, fallback to software if it fails
    success = run_ffmpeg(ffmpeg_args)
    
    if not success and encoder in ['h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf']:
        # Fallback to software encoding
        print(f"Hardware encoding with {encoder} failed, falling back to software encoding...")
        fallback_encoder = 'libx264' if 'h264' in encoder else 'libx265'
        ffmpeg_args_fallback = [
            "-r", str(fps),
            "-i", os.path.join(temp_directory_path, "%04d.png"),
            "-c:v", fallback_encoder,
            "-preset", "medium",
            "-crf", str(modules.globals.video_quality),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-vf", "colorspace=bt709:iall=bt601-6-625:fast=1",
            "-y",
            temp_output_path,
        ]
        success = run_ffmpeg(ffmpeg_args_fallback)
    return success and os.path.isfile(temp_output_path)


def restore_audio(target_path: str, output_path: str) -> bool:
    """Remux into a destination-side staging file before replacing an export."""
    temp_output_path = get_temp_output_path(target_path)
    try:
        with staged_output_path(output_path) as staging_path:
            done = run_ffmpeg(
                [
                    "-i", temp_output_path,
                    "-i", target_path,
                    "-c:v", "copy",
                    "-map", "0:v:0",
                    # Silent source videos are valid exports too.
                    "-map", "1:a:0?",
                    "-y", staging_path,
                ]
            )
            if not done or os.path.getsize(staging_path) == 0:
                return False
            os.replace(staging_path, output_path)
        return True
    except OSError as error:
        print(f"Failed to publish video with audio: {error}")
        return False


def get_temp_frame_paths(target_path: str) -> List[str]:
    temp_directory_path = get_temp_directory_path(target_path)
    return sorted(
        glob.glob(os.path.join(glob.escape(temp_directory_path), "*.png")),
        key=lambda path: (len(Path(path).stem), Path(path).stem),
    )


def get_temp_directory_path(target_path: str) -> str:
    """Return this process's private workspace, shared by mapping and render."""
    key = os.path.normcase(os.path.realpath(target_path))
    with _TEMP_WORKSPACES_LOCK:
        if key not in _TEMP_WORKSPACES:
            _TEMP_WORKSPACES[key] = tempfile.mkdtemp(prefix="deep-live-cam-")
        return _TEMP_WORKSPACES[key]


def get_temp_output_path(target_path: str) -> str:
    temp_directory_path = get_temp_directory_path(target_path)
    return os.path.join(temp_directory_path, TEMP_FILE)


def normalize_output_path(source_path: str, target_path: str, output_path: str | None) -> Any:
    if source_path and target_path and output_path:
        source_name, _ = os.path.splitext(os.path.basename(source_path))
        target_name, target_extension = os.path.splitext(os.path.basename(target_path))
        if os.path.isdir(output_path):
            return os.path.join(
                output_path, source_name + "-" + target_name + target_extension
            )
    return output_path


def create_temp(target_path: str) -> None:
    get_temp_directory_path(target_path)


@contextmanager
def staged_output_path(output_path: str):
    """Create a same-volume staging file and remove it if publication fails."""
    destination = Path(output_path).absolute()
    descriptor, staging_path = tempfile.mkstemp(
        prefix=f".{destination.stem}-", suffix=destination.suffix,
        dir=destination.parent,
    )
    os.close(descriptor)
    try:
        yield staging_path
    finally:
        Path(staging_path).unlink(missing_ok=True)


def move_temp(target_path: str, output_path: str) -> bool:
    """Publish safely even when the workspace and destination use different drives."""
    temp_output_path = get_temp_output_path(target_path)
    try:
        if not os.path.isfile(temp_output_path) or os.path.getsize(temp_output_path) == 0:
            return False
        with staged_output_path(output_path) as staging_path:
            shutil.copyfile(temp_output_path, staging_path)
            os.replace(staging_path, output_path)
        return True
    except OSError as error:
        print(f"Failed to publish video: {error}")
        return False


def clean_temp(target_path: str) -> bool:
    # Never derive a deletion target from a user's input path. Only directories
    # allocated by this process are eligible for cleanup.
    key = os.path.normcase(os.path.realpath(target_path))
    with _TEMP_WORKSPACES_LOCK:
        temp_directory_path = _TEMP_WORKSPACES.get(key)
        if temp_directory_path is None:
            return True
        if not os.path.lexists(temp_directory_path):
            _TEMP_WORKSPACES.pop(key)
            return True
        if modules.globals.keep_frames:
            print(f"Temporary frames retained in: {temp_directory_path}", flush=True)
        else:
            try:
                shutil.rmtree(temp_directory_path)
            except OSError as error:
                # Keep ownership for a later retry. A sharing violation after
                # publication must not turn an otherwise successful export into
                # a failure, or cause the next render to reuse stale frames.
                print(f"Temporary cleanup failed for {temp_directory_path}: {error}", flush=True)
                return False
        _TEMP_WORKSPACES.pop(key)
        return True


def clean_all_temp() -> None:
    """Release registered workspaces, including abandoned face-mapping sessions."""
    with _TEMP_WORKSPACES_LOCK:
        targets = list(_TEMP_WORKSPACES)
    for target_path in targets:
        clean_temp(target_path)


def read_image(image_path: str, flags: int = cv2.IMREAD_COLOR) -> Any:
    """Read image uploads as OpenCV arrays, including formats OpenCV may not decode."""
    if not image_path or not os.path.isfile(image_path):
        return None

    try:
        image = cv2.imdecode(numpy.fromfile(image_path, dtype=numpy.uint8), flags)
        if image is not None:
            return image
    except Exception:
        pass

    try:
        with Image.open(image_path) as pil_image:
            pil_image = ImageOps.exif_transpose(pil_image)
            if flags == cv2.IMREAD_GRAYSCALE:
                return numpy.array(pil_image.convert("L"))
            if flags == cv2.IMREAD_UNCHANGED and pil_image.mode in ("RGBA", "LA"):
                return cv2.cvtColor(numpy.array(pil_image.convert("RGBA")), cv2.COLOR_RGBA2BGRA)
            return cv2.cvtColor(numpy.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def has_image_extension(image_path: str) -> bool:
    return bool(image_path) and image_path.lower().endswith(IMAGE_EXTENSIONS)


def is_image(image_path: str) -> bool:
    if image_path and os.path.isfile(image_path):
        mimetype, _ = mimetypes.guess_type(image_path)
        return bool(mimetype and mimetype.startswith("image/")) or has_image_extension(image_path)
    return False


def is_video(video_path: str) -> bool:
    if video_path and os.path.isfile(video_path):
        mimetype, _ = mimetypes.guess_type(video_path)
        return bool(mimetype and mimetype.startswith("video/"))
    return False


def conditional_download(download_directory_path: str, urls: List[str]) -> None:
    if not os.path.exists(download_directory_path):
        os.makedirs(download_directory_path)
    for url in urls:
        _require_https_download_url(url)
        file_name = os.path.basename(urlsplit(url).path)
        if not file_name:
            raise ValueError(f"Download URL does not contain a file name: {url}")
        download_file_path = os.path.join(
            download_directory_path, file_name
        )
        if not os.path.exists(download_file_path):
            request = urllib.request.Request(url)
            # The input and final redirect target are restricted to HTTPS.
            with urllib.request.urlopen(request, timeout=60) as response:  # nosec B310
                _require_https_download_url(response.geturl())
                total = int(response.headers.get("Content-Length", 0))
                with tqdm(
                    total=total,
                    desc="Downloading",
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as progress:
                    with open(download_file_path, "wb") as f:
                        while True:
                            buffer = response.read(8192)
                            if not buffer:
                                break
                            f.write(buffer)
                            progress.update(len(buffer))


def _require_https_download_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise ValueError(f"Refusing non-HTTPS download URL: {url}")


def resolve_relative_path(path: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


def get_video_dimensions(target_path: str) -> tuple:
    """Get video width and height using ffprobe."""
    command = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
        target_path,
    ]
    output = subprocess.check_output(command).decode().strip()
    width, height = map(int, output.split("x"))
    return width, height


def estimate_frame_count(target_path: str, fps: float = None) -> int:
    """Estimate total frame count from video duration and fps."""
    if fps is None:
        fps = detect_fps(target_path)
    command = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        target_path,
    ]
    try:
        output = subprocess.check_output(command).decode().strip()
        duration = float(output)
        return int(duration * fps)
    except Exception:
        return 0
