---
author: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Model Download Verification

Status: PENDING

Release: `2.2.4`

The historical real-download/checksum run is preserved in
`docs/release-evidence/v2.2.3/MODEL_DOWNLOAD_VERIFICATION.md`.
This patch changes staging, failed-transfer cleanup and redirect handling.

## Current release checks

- [ ] Verify packaged consent/cancel behavior leaves no downloaded files.
- [ ] Verify a current authorized download succeeds with the catalogue checksum.
- [ ] Verify interrupted or failed transfers preserve existing model files and remove owned partial files.

The source regression suite covers failed transfers and HTTPS redirect rejection.
Existing locally verified models may be used for inference smoke tests without
redistributing them. Historical successful downloads are not fresh packaged
transfer evidence, and a provider probe is not a model download test.
