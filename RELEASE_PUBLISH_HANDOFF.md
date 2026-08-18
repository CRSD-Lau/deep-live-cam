# Windows Release Publish Handoff

Release: `2.2.2`

Status: RELEASE-CANDIDATE UNTIL FINAL ASSET VERIFICATION

## Intended public downloads

- `DeepLiveCamStudio-2.2.2-x64-setup.exe` — NVIDIA/CUDA installer
- `DeepLiveCamStudio-2.2.2-DirectML-x64-portable.zip` — AMD/Intel DirectML
- matching SHA-256 sidecars
- exact corresponding-source ZIP, SHA-256 sidecar, and source manifest
- the compliance and release evidence listed by `RELEASE_ASSETS.md`

Model/checkpoint files are intentionally excluded from every artifact.

## Build automation

Dispatch `.github/workflows/windows-release.yml` with:

- `app_version`: `2.2.2`
- `git_ref`: the exact merged release commit

The workflow builds the DirectML ZIP first, then the CUDA installer and source
asset set. The final combined artifact is validated with
`--require-directml-portable` so the hidden scikit-learn runtime DLL and model
exclusion are checked before upload.

Hosted CI intentionally does not grant publish approval. Final approval comes
from the repository's strict local/manual gates.

## Final local gates

```powershell
python tools\summarize_manual_release_gates.py --strict
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.2.2 -GitRef RELEASE_COMMIT -RequireFfmpeg -RequireCuda -RequireObsVirtualCam -RequirePublishReady
python tools\validate_windows_release_artifacts.py --app-version 2.2.2 --release-assets-dir build\windows\release-assets\2.2.2 --require-git-ref-source --require-directml-portable
```

All three commands must pass against the exact files intended for GitHub.

## Publish and verify

1. Create annotated tag `v2.2.2` on the fully verified merged commit, then
   create a draft release from that tag.
2. Use `RELEASE_NOTES.md` as the release body.
3. Upload every file listed in `RELEASE_ASSETS.md`.
4. Compare GitHub's live asset digests with `SHA256SUMS.txt`.
5. Download both public runtime assets into clean temporary folders.
6. Run the CUDA installer smoke test and DirectML provider/runtime checks.
7. Publish the draft only after those public-download checks pass.
8. Verify there are no open issues, PRs, or security alerts.

## Rollback

If a post-release check fails, keep or restore `v2.2.1` as the latest stable
release, mark `v2.2.2` as a pre-release or draft, and document the failed asset
and hash. Do not replace files under the same version without updating every
binary, source, manifest, checksum, and release note that identifies it.
