# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parents[1]
ACCELERATOR = os.environ.get("DLC_BUILD_ACCELERATOR", "cuda").lower()
BUNDLE_NAME = os.environ.get("DLC_BUNDLE_NAME", "DeepLiveCamStudio")


def existing_datas(paths):
    datas = []
    for source, target in paths:
        path = ROOT / source
        if path.exists():
            datas.append((str(path), target))
    return datas


def cuda_runtime_binaries():
    """Bundle CUDA/cuDNN DLLs needed by onnxruntime-gpu on Windows.

    We intentionally keep the Python torch package excluded, but its wheel
    carries the CUDA runtime DLLs that onnxruntime-gpu needs at inference time.
    """
    if ACCELERATOR != "cuda":
        return []

    torch_lib = Path(sys.prefix) / "Lib" / "site-packages" / "torch" / "lib"
    names = (
        "cublas64_12.dll",
        "cublasLt64_12.dll",
        "cudart64_12.dll",
        "cudnn64_9.dll",
        "cudnn_adv64_9.dll",
        "cudnn_cnn64_9.dll",
        "cudnn_engines_precompiled64_9.dll",
        "cudnn_engines_runtime_compiled64_9.dll",
        "cudnn_graph64_9.dll",
        "cudnn_heuristic64_9.dll",
        "cudnn_ops64_9.dll",
        "cufft64_11.dll",
        "cufftw64_11.dll",
        "curand64_10.dll",
        "cusolver64_11.dll",
        "cusolverMg64_11.dll",
        "cusparse64_12.dll",
        "nvrtc-builtins64_128.dll",
        "nvrtc64_120_0.dll",
        "nvToolsExt64_1.dll",
        "zlibwapi.dll",
    )
    binaries = []
    for name in names:
        path = torch_lib / name
        if path.exists():
            binaries.append((str(path), "."))
    return binaries


datas = []
datas += collect_data_files("insightface")
datas += collect_data_files("cv2")
datas += existing_datas(
    [
        ("Logo.png", "."),
        ("modules/ui.json", "modules"),
    ]
)

hiddenimports = []
hiddenimports += collect_submodules("insightface")
hiddenimports += collect_submodules("modules.processors.frame")
hiddenimports += collect_submodules("pyvirtualcam")
hiddenimports += [
    "onnxruntime.capi.onnxruntime_pybind11_state",
    "pygrabber.dshow_graph",
    "PIL._avif",
    "PIL._webp",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

block_cipher = None

a = Analysis(
    [str(ROOT / "DeepLiveCamStudio.pyw")],
    pathex=[str(ROOT)],
    binaries=cuda_runtime_binaries(),
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "models",
        "tests",
        "pytest",
        "IPython",
        "jupyter",
        "torch",
        "torchvision",
        "torchaudio",
        "triton",
        "onnxruntime.tools",
        "onnxruntime.transformers",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.binaries = [
    item for item in a.binaries
    if not str(item[0]).lower().replace("/", "\\").startswith("torch\\lib\\")
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

gui_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DeepLiveCamStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ROOT / "build" / "windows" / "assets" / "Logo.ico"),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="x86_64",
    codesign_identity=None,
    entitlements_file=None,
)

cli_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DeepLiveCamStudioCLI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(ROOT / "build" / "windows" / "assets" / "Logo.ico"),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="x86_64",
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    gui_exe,
    cli_exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=BUNDLE_NAME,
)
