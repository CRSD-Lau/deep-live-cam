---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Release Source Preparation

Release: `2.2.4`

Status: DRAFT — FINAL ASSET VERIFICATION PENDING

Binary and corresponding-source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

The corresponding-source archive must come from the same immutable merged
commit as both runtime builds. The corrected candidate must be tied to the final
manifest commit. Later documentation/evidence commits must not replace it with `HEAD`
or move the release tag. Publish those attestations separately and identify
their source commit separately from the binary/source commit.


The [first candidate](docs/release-evidence/v2.2.4/candidate-753aab70/README.md) is superseded for missing embedded-package
notices. Archive its tests and hashes; require new evidence for replacement bytes.
The corrected candidate is frozen at `617c733d42a10a2fcba036385e19d66fabcc2cc1`, with official
workflow [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).
The clean build checkout and both runtime/source jobs use that SHA. Later
documentation attestations do not change the frozen binaries or source;
use the recorded SHA rather than a later documentation checkout's HEAD.

## Inspect the source identity

```powershell
$ReleaseCommit = '617c733d42a10a2fcba036385e19d66fabcc2cc1' # Frozen binary/source commit
git status --short
git show --no-patch --decorate $ReleaseCommit
```

Use a clean release worktree. Local environments, build outputs, models, logs
and user data remain excluded. When the release tag exists, verify its peeled
commit matches the fixed SHA; do not use an unverified moving branch tip.

## Package exact source

The official candidate workflow packages source. If preparing it separately,
use the exact commit and a separate output directory; do not overwrite already
approved asset bytes just to refresh documentation.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.4 -GitRef $ReleaseCommit -OutputDir build\windows\source-verification\2.2.4
```

Required output:

- `DeepLiveCamStudio-2.2.4-source-<ref>.zip`
- matching `.zip.sha256`
- matching `.manifest.md`

Require `Archive mode: git-ref`, the exact resolved SHA, required source entries
and a passing forbidden-model scan. The archive includes application code,
build/installer scripts, both dependency profiles and workflows, tests, licences,
compliance records and packaging scripts from that commit. It excludes model
weights, secrets, local environments and build output.

## Validate the complete release set

```powershell
python tools\validate_windows_release_artifacts.py --app-version 2.2.4 --output-dir build\windows\release-assets\2.2.4 --release-assets-dir build\windows\release-assets\2.2.4 --require-git-ref-source --require-directml-portable
```

This command assumes the complete approved combined asset set is at the shown
path, including installer, portable ZIP, source and required evidence. It is
not a source-only command. Use the real combined directory for both options.
Corresponding source stays beside both runtime downloads; a repository link
alone does not identify the exact source used for the shipped binaries.

Older release instructions inside the fixed source archive are historical
content of that commit. The current external handoff supersedes those procedures
without altering the source archive or claiming that later documentation was
compiled into the binaries.
