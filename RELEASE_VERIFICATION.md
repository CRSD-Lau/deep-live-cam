# Windows Release Verification

Generated: 2026-05-19T03:50:42Z from the assembled release-assets manifest and artifact sidecars
App version: `2.1.5`
Git HEAD: `6b229c7d0b248453d8d50674d0e7ff7d87606471`

This file records local release evidence for the Windows installer. It is not a legal opinion and does not replace the manual checks in `RELEASE_CHECKLIST.md`.

## Release Verdict

- Local installer automation passed: **YES**
- Draft source traceability available: **YES**
- Real model download/checksum verification recorded: **YES**
- Packaged CPU/CUDA processing verification recorded: **YES**
- Public-release source archive from clean Git ref: **YES, see `CLEAN_RELEASE_WORKTREE_VERIFICATION.md`**
- Release cutover status clean: **NO**
- Manual gate evidence complete: **NO**
- Ready to publish without remaining manual gates: **NO**

Current status: the installer and matching Git-ref source archive are locally verified, but this is not yet a publishable GitHub Release until the manual checklist gates are completed.

## Automated Evidence

- [x] Installer exists: `C:\Projects\deep-live-cam\build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe`
- [x] Installer SHA-256 sidecar matches
  - SHA-256: `C96FA88BB1F8C382D079EC407522B7114C6326ADC7E53547D3CF004C4E2E43A1`
  - Installer bytes: `431579555`
- [x] Windows bundle manifest was generated from the PyInstaller payload and included in the installer/source evidence as `LICENSES/WINDOWS_BUNDLE_MANIFEST.md`
- [x] Packaged payload contains no forbidden model/checkpoint files
- [x] Clean detached release checkout built the PyInstaller payload and passed packaged-runtime smoke testing
- [x] Corresponding-source archive exists
- [x] Corresponding-source SHA-256 sidecar matches
- [x] Corresponding-source manifest exists
- [x] Corresponding-source archive contains no forbidden model/checkpoint entries
- [x] Public-release source archive was created from a clean Git ref
- [x] Real model download/checksum verification exists: `C:\Projects\deep-live-cam\MODEL_DOWNLOAD_VERIFICATION.md`
- [x] Packaged processing verification exists: `C:\Projects\deep-live-cam\PROCESSING_VERIFICATION.md`

## Required Installed Release Files

- [x] `README.md`
- [x] `LICENSE`
- [x] `THIRD_PARTY_NOTICES.md`
- [x] `COMPLIANCE.md`
- [x] `RELEASE_CHECKLIST.md`
- [x] `RELEASE_REPORT.md`
- [x] `RELEASE_SOURCE_PREP.md`
- [x] `MODEL_DOWNLOAD_VERIFICATION.md`
- [x] `PROCESSING_VERIFICATION.md`
- [x] `docs/OBS_VIRTUAL_CAMERA.md`
- [x] `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md`
- [x] `LICENSES/MODEL_LICENSE_AUDIT.md`
- [x] `LICENSES/PYTHON_DEPENDENCIES.md`
- [x] `LICENSES/THIRD_PARTY_LICENSES/README.md`
- [x] `LICENSES/THIRD_PARTY_LICENSES/tensorflow-2.19.1/package/THIRD_PARTY_NOTICES.txt`
- [x] `LICENSES/THIRD_PARTY_LICENSES/onnxruntime-gpu-1.23.2/package/LICENSE`
- [x] `LICENSES/THIRD_PARTY_LICENSES/opencv-python-4.10.0.84/package/LICENSE-3RD-PARTY.txt`
- [x] `LICENSES/THIRD_PARTY_LICENSES/onnx-1.18.0/licenses/LICENSE`
- [x] `LICENSES/THIRD_PARTY_LICENSES/opennsfw2-0.10.2/LICENSE`
- [x] `LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/METADATA`
- [x] `LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/licenses/LicenseRef-Qt-Commercial.txt`
- [x] `LICENSES/THIRD_PARTY_LICENSES/shiboken6-6.11.1/METADATA`
- [x] `LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE`
- [x] `LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE`
- [x] `LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE`
- [x] `LICENSES/WINDOWS_BUNDLE_MANIFEST.md`

## Source Archive

- Latest source archive: `C:\Projects\deep-live-cam\build\windows\installer\DeepLiveCamStudio-2.1.5-source-6b229c7d0b24.zip`
- Source archive mode: `git-ref`
- Source archive SHA-256: `8A3FBFE51B5500C8C7DC8C66423FBF0495ECDC2018C198F22AA15B3D818C14A1`
- Source archive hash sidecar: `C:\Projects\deep-live-cam\build\windows\installer\DeepLiveCamStudio-2.1.5-source-6b229c7d0b24.zip.sha256`
- Source archive manifest: `C:\Projects\deep-live-cam\build\windows\installer\DeepLiveCamStudio-2.1.5-source-6b229c7d0b24.manifest.md`
- Source archive bytes: `67807508`

## Cutover Status

- Cutover status report: `C:\Projects\deep-live-cam\RELEASE_CUTOVER_STATUS.md`
- Dirty paths: `68`
- Release-owned dirty paths: `3`
- Staged release-owned paths: `0`
- Unstaged release-owned paths: `3`
- Mixed-scope dirty paths: `65`
- Unknown dirty paths: `0`
- Cutover report blocked: **YES**

## Manual Gates Still Required

- [ ] Clean Windows x64 VM install without admin rights
- [x] Real model download with user consent and checksum verification
- [x] CPU fallback processing with downloaded models
- [x] CUDA processing with downloaded models on a supported NVIDIA machine
- [ ] OBS Virtual Camera workflow with OBS installed and virtual camera enabled
- [ ] Final legal review for model licenses, pyvirtualcam metadata, LGPL/GPL obligations, and Inno Setup commercial-use position

## Manual Gate Evidence Files

- [ ] `CLEAN_VM_VERIFICATION.md` for Clean Windows x64 VM install without admin rights: `PENDING`
  - Open checklist items: `10`
- [ ] `OBS_VIRTUAL_CAMERA_VERIFICATION.md` for OBS Virtual Camera workflow with OBS installed and virtual camera enabled: `PENDING`
  - Open checklist items: `6`
- [ ] `LEGAL_REVIEW.md` for Final legal review for model licenses, pyvirtualcam metadata, LGPL/GPL obligations, and Inno Setup commercial-use position: `PENDING`
  - Open checklist items: `13`

## Blocking Publish Checks

- RELEASE_CUTOVER_STATUS.md reports unresolved cutover blockers.
- CLEAN_VM_VERIFICATION.md is `PENDING` with 10 open checklist item(s).
- OBS_VIRTUAL_CAMERA_VERIFICATION.md is `PENDING` with 6 open checklist item(s).
- LEGAL_REVIEW.md is `PENDING` with 13 open checklist item(s).

## Notes

- A dirty working tree is expected during local development, but a public AGPL binary release should be paired with source from the exact clean release tag or commit.
- Model files are intentionally excluded from the installer and should be downloaded only after user consent and checksum verification.
