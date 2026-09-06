---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Official 2.2.4 build and source verification

Status: AUTOMATED BUILD/SOURCE SUBSET PASS

Verified UTC: `2026-09-06T23:12:52.361594+00:00`

Binary/source commit: `617c733d42a10a2fcba036385e19d66fabcc2cc1`

[Workflow 34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042) completed successfully for source resolution,
DirectML and CUDA. GitHub records combined artifact `9998973014` for this
commit. This attestation records local file hashes and read-only source/log
checks; it does not approve publication.

| Verified official file | Bytes | SHA256 |
| --- | ---: | --- |
| `DeepLiveCamStudio-2.2.4-x64-setup.exe` | 1716394725 | `d91080bef32a6bb731830599bfda90eeca4844d20af6d34e67957c0bda2b48bf` |
| `DeepLiveCamStudio-2.2.4-source-617c733d42a1.zip` | 3953139 | `ec59a3be3ffc4b4b58baafbc4fd4867ceeedea3fa66e3d86038dcb4dc4af7f8e` |

Both sidecars match. The source manifest and successful build log match the
source hash and fixed commit; the build log also matches the installer hash.

The source ZIP contains **287 files / 6,691,483 uncompressed bytes**.
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
the official installer EXE above or an upgrade of the actual user installation. The script
emits no separate post-uninstall PASS line; successful continuation and its
throw-on-failure assertions establish that subset. Complete real user-data
preservation, actual hosted-installer execution, GPU/GUI/receiver behavior and
clean-Windows/manual gates require separate evidence.

Portable event timestamps, log line references, input evidence hashes and exact
check scope are recorded in `BUILD_SOURCE_VALIDATION.json`. The original downloaded Actions ZIP was independently hashed: `5b28c6ddbe9b708c3650d9f9a81f78a07501459b714b897e49469dd4ddbd13d5` (2,359,303,119 bytes). Both SHA-256 and size match the saved service metadata.
No installer, runtime or model execution, tracked edit,
external mutation or publication was performed by this audit.

Portable derivative: local input paths in `BUILD_SOURCE_VALIDATION.json` were replaced with portable evidence identifiers. All original verdicts, measured values, hashes, and limitations remain unchanged. This Markdown copy changes the JSON basename and adds this provenance statement only.

Original JSON report SHA-256: `dba511cf92448e6322a7ae43279b16976fd6ef1e63ac9f40abaf347adcf53b87`.
