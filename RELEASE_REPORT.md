---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows Release Report

Release: `2.2.4`

Status: DRAFT — FINAL ARTIFACT AND MANUAL VERIFICATION PENDING

Binary/source commit: `753aab70c34ae585d525a06b9f7de2d721b7f491`

The candidate contains export-integrity, Unicode-path, temporary-workspace,
settings, model-transfer and camera-lifecycle fixes. CUDA remains an Inno Setup
installer and DirectML a separate portable ZIP. The current scope and dependency
delta are described in [RELEASE_NOTES_TEMPLATE.md](RELEASE_NOTES_TEMPLATE.md).

Use [RELEASE_PUBLISH_HANDOFF.md](RELEASE_PUBLISH_HANDOFF.md),
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) and
[RELEASE_SOURCE_PREP.md](RELEASE_SOURCE_PREP.md) for current commands and gates.
The [original 2.2.3 report](docs/release-evidence/v2.2.3/preparation/RELEASE_REPORT.md)
is retained unchanged; its old build commands and validation claims are historical.

Final artifact hashes, licence inventories, processing/installer evidence and
publication status belong in the reviewed asset attestations. This draft report
does not mark any pending check as passed. Keep `v2.2.3` available as rollback.
