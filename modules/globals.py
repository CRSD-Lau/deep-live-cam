# --- START OF FILE globals.py ---

import os
from typing import List, Dict, Any

from modules.enhancement_registry import default_enhancer_state

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_DIR = os.path.join(ROOT_DIR, "workflow")

file_types = [
    ("Image", ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp")),
    ("Video", ("*.mp4", "*.mkv")),
]

# Face Mapping Data
source_target_map: List[Dict[str, Any]] = [] # Stores detailed map for image/video processing
simple_map: Dict[str, Any] = {}             # Stores simplified map (embeddings/faces) for live/simple mode

# Paths
source_path: str | None = None
target_path: str | None = None
output_path: str | None = None

# Processing Options
frame_processors: List[str] = []
quality_mode: str = "balanced"
keep_fps: bool = True
keep_audio: bool = True
keep_frames: bool = False
many_faces: bool = False         # Process all detected faces with default source
map_faces: bool = False          # Use source_target_map or simple_map for specific swaps
poisson_blend: bool = False      # Enable Poisson Blending for smoother face swaps
color_correction: bool = False   # Enable color correction (implementation specific)
nsfw_filter: bool = False

# Video Output Options
video_encoder: str | None = None
video_quality: int | None = None # Typically a CRF value or bitrate

# Live Mode Options
live_mirror: bool = False
live_resizable: bool = True
live_process_latest_frame: bool = True
camera_input_combobox: Any | None = None # Placeholder for UI element if needed
webcam_preview_running: bool = False
show_fps: bool = False
camera_width: int | None = None
camera_height: int | None = None
camera_fps: int | None = None

# Virtual Camera Output Options
virtual_cam: bool = False
virtual_cam_name: str | None = None
virtual_cam_width: int = 1280
virtual_cam_height: int = 720
virtual_cam_fps: int = 30

# System Configuration
max_memory: int | None = None        # Memory limit in GB? (Needs clarification)
execution_providers: List[str] = []  # e.g., ['CUDAExecutionProvider', 'CPUExecutionProvider']
requested_execution_providers: List[str] = []
directml_device_id: int = 0
execution_threads: int | None = None # Number of threads for CPU execution
headless: bool | None = None         # Run without UI?
log_level: str = "error"             # Logging level (e.g., 'debug', 'info', 'warning', 'error')
download_models: bool = False
assume_yes: bool = False
check_execution_provider: bool = False
benchmark_pipeline: bool = False
benchmark_log_interval: float = 5.0
benchmark_output_path: str | None = None
visual_qa_output_dir: str | None = None
visual_qa_frame_indices: List[int] = [0]
visual_qa_temporal: bool = False
diagnostic_overlay: bool = False
diagnostic_overlay_layers: List[str] = ["bbox", "kps", "profile"]

# Face Processor UI Toggles (Example)
fp_ui: Dict[str, bool] = default_enhancer_state()

# Face Swapper Specific Options
face_swapper_enabled: bool = True # General toggle for the swapper processor
opacity: float = 1.0              # Blend factor for the swapped face (0.0-1.0)
sharpness: float = 0.0            # Sharpness enhancement for swapped face (0.0-1.0+)
postprocess_sharpness_motion_reduction: float = 0.0
postprocess_sharpness_blur_reduction: float = 0.0

# Mouth Mask Options
mouth_mask: bool = False           # Enable mouth area masking/pasting
show_mouth_mask_box: bool = False  # Visualize the mouth mask area (for debugging)
mask_feather_ratio: int = 12       # Denominator for feathering calculation (higher = smaller feather)
mask_down_size: float = 0.1        # Expansion factor for lower lip mask (relative)
mask_size: float = 1.0             # Expansion factor for upper lip mask (relative)
mouth_mask_size: float = 0.0       # Mouth mask size (0-100; 0=off, 100=mouth to chin)
expression_mouth_min_confidence: float = 0.0  # Gate original-mouth paste on landmark stability
expression_eye_min_confidence: float = 0.0    # Gate eye/blink temporal weighting on landmark stability
mouth_mask_temporal_smoothing: float = 0.0    # Per-track mouth mask geometry history weight
mouth_mask_temporal_motion_reduction: float = 0.0

# --- START: Added for Frame Interpolation ---
enable_interpolation: bool = True # Toggle temporal smoothing
interpolation_weight: float = 0  # Blend weight for current frame (0.0-1.0). Lower=smoother.
temporal_smoothing_region_expansion: float = 0.18
temporal_smoothing_feather_ratio: float = 0.18
temporal_smoothing_mask_strength: float = 0.0
temporal_smoothing_motion_threshold: float = 0.08
temporal_smoothing_high_motion_threshold: float = 0.35
temporal_smoothing_motion_weight_boost: float = 0.0
temporal_smoothing_expression_region_boost: float = 0.0
temporal_smoothing_expression_mouth_strength: float = 0.0
temporal_smoothing_expression_eye_strength: float = 0.0
temporal_smoothing_expression_feather_ratio: float = 0.018
expression_temporal_smoothing: bool = False
expression_temporal_stable_weight_multiplier: float = 1.0
expression_temporal_motion_threshold: float = 0.035
expression_temporal_high_motion_threshold: float = 0.09
expression_temporal_motion_weight_boost: float = 0.0
expression_temporal_unilateral_eye_motion_scale: float = 1.0
expression_region_temporal_smoothing: float = 0.0
expression_region_temporal_motion_reduction: float = 0.0
live_detection_interval_ratio: float = 0.08  # Fraction of live FPS between detector refreshes.
face_tracking_enabled: bool = True
face_tracking_current_weight: float = 0.7
face_tracking_reset_ratio: float = 1.2
face_tracking_max_missed: int = 1
face_tracking_confidence_weight: float = 0.0
face_tracking_confidence_reference: float = 0.75
face_tracking_confidence_min_weight: float = 0.35
face_tracking_min_detection_confidence: float = 0.0
face_tracking_prediction_strength: float = 0.0
face_tracking_prediction_decay: float = 0.5
compositing_color_match_strength: float = 0.0
compositing_color_match_trim_percentile: float = 0.0
compositing_color_chroma_trim_percentile: float = 0.0
compositing_color_temporal_smoothing: float = 0.0
compositing_color_temporal_motion_threshold: float = 0.08
compositing_color_temporal_high_motion_threshold: float = 0.35
compositing_color_temporal_motion_reduction: float = 0.0
compositing_lighting_match_strength: float = 0.0
compositing_lighting_contrast_strength: float = 0.35
compositing_lighting_max_shift: float = 12.0
compositing_mask_erode_ratio: float = 0.10
compositing_mask_blur_ratio: float = 0.05
compositing_mask_scale_strength: float = 0.35
compositing_mask_edge_strength: float = 0.35
compositing_mask_motion_blur_strength: float = 0.0
compositing_mask_motion_strength: float = 0.0
compositing_mask_profile_strength: float = 0.0
compositing_landmark_mask_strength: float = 0.0
compositing_landmark_mask_dilation_ratio: float = 0.025
compositing_landmark_mask_feather_ratio: float = 0.018
compositing_landmark_mask_profile_taper: float = 0.0
compositing_extended_subject_mask: bool = True
compositing_extended_subject_hairline_ratio: float = 0.32
compositing_extended_subject_side_ratio: float = 0.24
compositing_extended_subject_shoulder_ratio: float = 0.48
compositing_extended_subject_chest_ratio: float = 0.58
compositing_show_subject_mask: bool = False
compositing_skin_mask_strength: float = 0.0
compositing_skin_mask_chroma_threshold: float = 1.8
compositing_skin_mask_max_reduction: float = 0.45
compositing_skin_mask_blur_ratio: float = 0.015
compositing_skin_mask_luma_threshold: float = 0.0
compositing_skin_mask_luma_max_reduction: float = 0.0
compositing_boundary_mismatch_strength: float = 0.0
compositing_boundary_mismatch_threshold: float = 0.18
compositing_boundary_mismatch_max_reduction: float = 0.45
compositing_boundary_mismatch_band_ratio: float = 0.035
compositing_boundary_mismatch_blur_ratio: float = 0.012
compositing_alpha_temporal_smoothing: float = 0.0
compositing_alpha_temporal_motion_threshold: float = 0.08
compositing_alpha_temporal_high_motion_threshold: float = 0.35
compositing_alpha_temporal_motion_reduction: float = 0.0
compositing_occlusion_edge_strength: float = 0.0
compositing_occlusion_edge_threshold: float = 0.35
compositing_occlusion_edge_max_reduction: float = 0.55
compositing_occlusion_edge_blur_ratio: float = 0.015
compositing_occlusion_edge_min_contrast: float = 24.0
compositing_occlusion_detail_strength: float = 0.0
compositing_occlusion_detail_threshold: float = 0.12
compositing_occlusion_region_boost: float = 0.0
compositing_occlusion_mouth_region_strength: float = 0.0
compositing_occlusion_eye_region_strength: float = 0.0
compositing_occlusion_region_feather_ratio: float = 0.018
compositing_occlusion_region_temporal_smoothing: float = 0.0
compositing_occlusion_region_temporal_motion_reduction: float = 0.0
# --- END: Added for Frame Interpolation ---

# --- END OF FILE globals.py ---

import threading
dml_lock = threading.Lock()
