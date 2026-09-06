---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Publish Handoff

Release: `2.2.4`

Status: DRAFT — FINAL ARTIFACT AND MANUAL VERIFICATION PENDING

Binary and corresponding-source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

Rollback release: `v2.2.3`

Set the release draft target to the frozen corrected build commit when its
complete verified replacement assets are uploaded. Keep it unpublished while any required check remains pending. A later
documentation/evidence commit does not
change the commit used for these binaries or their corresponding-source archive.
The first candidate and its embedded documentation remain historical. Preserve
its bytes separately while preparing the corrected candidate.


The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded for missing embedded-package
notices. Archive its tests and hashes; require new evidence for replacement bytes.
The corrected candidate is frozen at `617c733d42a10a2fcba036385e19d66fabcc2cc1`, with official
workflow [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
The clean build checkout and both runtime/source jobs use that SHA. Later
documentation attestations do not change the frozen binaries or source;
use the recorded SHA rather than a later documentation checkout's HEAD.

## Intended downloads

- `DeepLiveCamStudio-2.2.4-x64-setup.exe` — NVIDIA/CUDA installer
- `DeepLiveCamStudio-2.2.4-DirectML-x64-portable.zip` — AMD/Intel DirectML
- matching SHA-256 sidecars
- exact corresponding-source ZIP, SHA-256 sidecar, and source manifest
- complete compliance and evidence files listed by the final `RELEASE_ASSETS.md`

A partial draft upload is not the complete release. Model/checkpoint files must
be absent from every distributed runtime and source archive.

## Build identity

The corrected candidate workflow
uses `.github/workflows/windows-release.yml` with `app_version: 2.2.4` and the
frozen commit as `git_ref`. Both binary jobs and source packaging must
resolve to that commit. Check their manifests before accepting the final assets.
Hosted workflow success does not approve publication.

`run_release_checks.ps1` is a build-stage command: it copies documentation and
licences, repackages the installer, and regenerates evidence/source outputs.
Run it in a release worktree before freezing the asset bytes. Do not use it as
a read-only smoke test of an already downloaded or installed official artifact.
For the prepared build-stage checks, see [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## Final artifact and manual gates

Run the checks against the actual final CUDA installer/bundle, DirectML ZIP,
and matching source archive. Record exact artifact hashes with the evidence.

```powershell
python tools\summarize_manual_release_gates.py --app-version 2.2.4 --strict
python tools\validate_windows_release_artifacts.py --app-version 2.2.4 --output-dir build\windows\release-assets\2.2.4 --release-assets-dir build\windows\release-assets\2.2.4 --require-git-ref-source --require-directml-portable
```

The second command assumes the complete combined asset set is staged at the
shown path; use the actual approved asset directory for both directory options.
It checks artifact integrity and required evidence structure. It does not
replace the strict current-release manual summary or publish-readiness report.

Confirm the generated `RELEASE_VERIFICATION.md` reports
`Ready to publish without remaining manual gates: YES` only after all current
gates are satisfied. Preserve earlier failed attempts and historical records.
Required evidence includes:

- strict CUDA and DirectML provider checks and real processing on identified
  NVIDIA/AMD adapters using the final runtimes;
- actual official installer execution, a stable 2.2.3-to-2.2.4 upgrade with
  user-data preservation, and separate clean-Windows and migration/uninstall
  coverage; the rebuilt test-GUID fixture is distinct evidence;
- final packaged Preview, Live Output lifecycle and processed output in a
  receiving application; synthetic sender tests establish only their subset;
- current model-setup/transfer and compliance checks, with all five gate
  documents explicitly PASS for 2.2.4 and no unchecked items.

## Complete the draft and publish

1. Verify the annotated `v2.2.4` tag resolves to
   `617c733d42a10a2fcba036385e19d66fabcc2cc1`; do not retarget it to a later
   documentation commit.
2. Update the existing draft with the reviewed `RELEASE_NOTES.md` and every file
   listed in `RELEASE_ASSETS.md`. Keep binary/source provenance separate from
   the commit containing later validation attestations.
3. Compare GitHub asset digests with the complete `SHA256SUMS.txt`.
4. Download both draft-hosted runtime assets into separate owned folders,
   verify their hashes, and repeat official-byte provider/runtime/upgrade checks.
5. Recheck this repository's issues, PRs and security alerts, and record any
   unresolved or inaccessible checks.
6. Publish only after all required gates pass. Then verify public download
   availability and hashes without changing the already verified payloads.

## Rollback

Keep `v2.2.3` available as the stable rollback release. If candidate validation
fails, leave `v2.2.4` as a draft and record the failed asset and hash. If a defect
is discovered after publication, stop promoting the affected release and record
the recovery decision. A local reinstall or downgrade requires its own explicit
execution decision and verified user-data backup; there is no automatic rollback.

Do not silently replace a published binary or change its source identity.
Any replacement release must carry matching binaries, corresponding source,
manifests, hashes and release notes.
