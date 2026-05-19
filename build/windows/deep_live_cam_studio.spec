# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parents[1]


def existing_datas(paths):
    datas = []
    for source, target in paths:
        path = ROOT / source
        if path.exists():
            datas.append((str(path), target))
    return datas


datas = []
datas += collect_data_files("insightface")
datas += collect_data_files("cv2")
datas += existing_datas(
    [
        ("locales", "locales"),
        ("media", "media"),
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
    binaries=[],
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
    if "\\torch\\lib\\" not in item[1].lower() and "/torch/lib/" not in item[1].lower()
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
    name="DeepLiveCamStudio",
)
