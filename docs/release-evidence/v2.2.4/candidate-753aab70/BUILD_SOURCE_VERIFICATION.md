---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Official 2.2.4 build and source verification

Status: AUTOMATED BUILD/SOURCE SUBSET PASS

Verified UTC: `2026-09-06T21:28:40.822202+00:00`

Binary/source commit: `753aab70c34ae585d525a06b9f7de2d721b7f491`

[Workflow 34056909310](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34056909310) completed successfully for source resolution,
DirectML and CUDA. GitHub records combined artifact `9997372846` for this
commit. This attestation records local file hashes and read-only source/log
checks; it does not approve publication.

| Verified official file | Bytes | SHA256 |
| --- | ---: | --- |
| `DeepLiveCamStudio-2.2.4-x64-setup.exe` | 1716357882 | `797f15a50cef7522374c5bf4f1880b047e6fe0f1cd165c39a1639bc36189c31d` |
| `DeepLiveCamStudio-2.2.4-source-753aab70c34a.zip` | 3863377 | `43e9ab8a6e71a938d57b82661598cdae1092e69cfb010efb8d78e4eff5bf64df` |

Both sidecars match. The source manifest and successful build log match the
source hash and fixed commit; the build log also matches the installer hash.

The source ZIP contains **255 files / 6,467,977 uncompressed bytes**.
All 119 required manifest entries exist. Member CRCs, paths, case-insensitive
uniqueness, prefix and version pass. No model/checkpoint members or local
environment/build payload directories were found. All file names and uncompressed
bytes match a fresh **in-memory native `git archive` of the fixed commit** using
the same prefix. Model-policy exclusions from the native archive: 0.
No checkout or extracted source tree was written.

The hosted log records the 2.2.1 legacy fixture install, isolated 2.2.4 upgrade,
installed CLI version, successful upgrade checks, silent uninstall and successful
continuation to the next release step. The exact archived script confirms that
this checks legacy/orphan cleanup, candidate registration/path/version, required
payload files, excluded weights/Torch Python payload, model-sentinel preservation,
and removal of the fixture registration/directory after uninstall.

**Installer scope:** this is the recompiled test-GUID fixture, not execution of
the official installer EXE above or an actual stable 2.2.3 upgrade. The script
emits no separate post-uninstall PASS line; successful continuation and its
throw-on-failure assertions establish that subset. Complete real user-data
preservation, actual hosted-installer execution, GPU/GUI/receiver behavior and
clean-Windows/manual gates require separate evidence.

Portable event timestamps, log line references, input evidence hashes and exact
check scope are recorded in `build-source-verification.json`. The outer Actions
ZIP digest is service-reported metadata; this audit did not independently hash
that outer container. No installer, runtime or model execution, tracked edit,
external mutation or publication was performed by this audit.
