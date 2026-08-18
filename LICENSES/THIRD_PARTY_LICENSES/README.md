# Collected Third-Party License Files

This folder is generated from the active build environment by `tools/collect_third_party_license_files.py`.
It collects high-attention license, notice, and package metadata files that PyInstaller may not copy into the application payload by default.

> [!IMPORTANT]
> Regenerate this folder before each Windows release candidate, then review the diff before publishing.

## Included Packages

- `tensorflow` `2.19.1`
- `opencv-python` `4.10.0.84`
- `onnxruntime-gpu` `1.24.4`
- `torch` `2.11.0+cu128`
- `onnx` `1.22.0`
- `opennsfw2` `0.18.0`
- `PySide6` `6.11.1`
- `PySide6_Addons` `6.11.1`
- `PySide6_Essentials` `6.11.1`
- `shiboken6` `6.11.1`
- `pyvirtualcam` `0.15.0`
- `cv2_enumerate_cameras` `1.1.15`
- `easydict` `1.13`

## Review Checklist

- Confirm package versions match the release build environment.
- Keep original license and notice text intact.
- Re-run the collector whenever dependencies change.
- Update `LICENSES/PYTHON_DEPENDENCIES.md` and `THIRD_PARTY_NOTICES.md` when the license posture changes.
