# Security Review - 2026-05-19

Scope: repository-wide review of the Windows desktop app, model download flow, local media processing, release tooling, and Python dependency pins.

## Result

No exploitable first-party security finding survived validation in this pass. One dependency issue set did survive: the release pins referenced package versions with active advisories. Those pins are updated in `requirements.txt`.

## Changes Made

- Updated `onnx` from `1.18.0` to `1.21.0`.
- Updated `pillow` from `12.1.1` to `12.2.0`.
- Updated `protobuf` from `4.25.1` to `5.29.6`.
- Removed the UI's external Random face fetch, which also removed one unnecessary outbound network path from the desktop surface.

`pip-audit -r requirements.txt` now reports no known vulnerabilities.

## Reviewed Surfaces

- CLI-controlled media paths in `modules/core.py`.
- FFmpeg and FFprobe subprocess calls in `modules/utilities.py` and `modules/processors/frame/core.py`.
- Temporary frame directory creation, move, and cleanup in `modules/utilities.py`.
- Model download consent, URL list, SHA-256 verification, and atomic replacement in `modules/model_manager.py`.
- Runtime/user-data path selection in `modules/paths.py`.
- Desktop launcher logging and error dialog handling in `modules/desktop_launcher.py`.
- Release validation scripts under `tools/` and `build/windows/`.

## Validation Notes

- Model downloads use fixed repository-controlled URLs and verify SHA-256 before replacing model files.
- FFmpeg calls pass argument lists to `subprocess` without `shell=True`; user-selected file paths are passed as values, not shell text.
- Output and cleanup paths are local-user controlled. I did not find a remote or lower-privilege path that turns them into arbitrary file deletion for another user.
- `conditional_download()` still contains a macOS-only unverified TLS fallback, but no live call site was found in this repository. Treat it as cleanup debt if macOS download support returns.

## Commands Run

```powershell
venv\Scripts\python.exe -m pip_audit -r requirements.txt
venv\Scripts\python.exe -m pytest tests\test_desktop_launcher.py tests\test_no_avatar_surface.py
venv\Scripts\python.exe -m pytest tests\test_model_manager.py tests\test_windows_release_scripts.py tests\test_validate_windows_release_artifacts.py
```
