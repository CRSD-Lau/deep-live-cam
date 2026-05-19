# Final Legal Review

Status: PENDING

This file records the final release legal/compliance review. It is a release
management artifact, not legal advice by itself. Change `Status` to `PASS` only
after an authorized reviewer confirms the release is acceptable for the intended
distribution context. The release verifier only treats this file as passed when
`Status: PASS` is present and no unchecked `- [ ]` checklist rows remain.

## Artifact Under Review

- Installer: `DeepLiveCamStudio-2.1.5-x64-setup.exe`
- Installer SHA-256: `97FFFB8DB2BC151AC30365AF59D220CC3A6551376AD61D7A63093BCEEF23F7E3`
- Source commit/tag: see `build/windows/release-assets/2.1.5/RELEASE_ASSETS.md`
- Reviewer:
- Date:
- Intended distribution context:

## Required Review Items

- [ ] AGPL-3.0 obligations are satisfied by linking or attaching complete corresponding source for the exact binary release.
- [ ] Original Deep-Live-Cam attribution is preserved.
- [ ] Release notes include source availability and AGPL notices.
- [ ] Installer includes `LICENSE`, `COMPLIANCE.md`, `THIRD_PARTY_NOTICES.md`, `LICENSES/BUNDLED_BINARY_OBLIGATIONS.md`, `LICENSES/MODEL_LICENSE_AUDIT.md`, `LICENSES/PYTHON_DEPENDENCIES.md`, `LICENSES/THIRD_PARTY_LICENSES/`, and `LICENSES/WINDOWS_BUNDLE_MANIFEST.md`.
- [ ] No model/checkpoint files are bundled in the installer.
- [ ] Model downloader source URLs, license notes, and SHA-256 checksums are acceptable for the intended distribution context.
- [ ] `inswapper`, GPEN, and GFPGAN model redistribution remains excluded unless separately authorized.
- [ ] PySide6/shiboken6 LGPL/GPL/commercial-license posture is acceptable.
- [ ] `pyvirtualcam` GPLv2 metadata is reviewed for binary distribution compatibility.
- [ ] `cv2_enumerate_cameras` GPL-3.0 metadata is reviewed for binary distribution compatibility.
- [ ] Inno Setup commercial-use position is accepted by the publisher.
- [ ] ffmpeg is not bundled, or any future ffmpeg bundling plan has its own redistribution review.
- [ ] Remaining `UNKNOWN` or unusual dependency metadata in `LICENSES/PYTHON_DEPENDENCIES.md` is reviewed.

## Review Notes

Record conclusions, exceptions, required release-note language, or approval
links here.

### Automated Evidence Packet

Run the helper below against the exact release-candidate source archive listed
in `build\windows\release-assets\<version>\RELEASE_ASSETS.md`. The generated
packet records installer/source hashes, required compliance documents, a
forbidden model/checkpoint scan, high-attention dependency metadata, model
redistribution notes, and bundled binary obligations.

The packet intentionally remains `Status: REVIEW-REQUIRED`; it is evidence for
an authorized reviewer, not approval. `Status: PASS` still requires reviewer
decisions, especially AGPL corresponding-source handling, model downloader
license posture, PySide6/shiboken6 posture, GPL metadata for
`pyvirtualcam`/`cv2_enumerate_cameras`, Inno Setup commercial-use position,
ffmpeg exclusion, and unknown/unusual dependency metadata.

The helper fails closed if the corresponding source archive, `.sha256` sidecar,
or `.manifest.md` file is missing, mismatched, not generated from a Git ref, or
does not record the forbidden model/checkpoint scan. Latest generated packet:
`build/windows/manual-evidence/legal-review/legal-review-2.1.5-20260519-024137.md`.

Automated evidence helper for the reviewer packet:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\verify_legal_review_gate.ps1 -AppVersion 2.1.5
```

Attach or summarize the generated
`build\windows\manual-evidence\legal-review\*.md` file, then complete the
reviewer decisions above before changing this file to `Status: PASS`.
