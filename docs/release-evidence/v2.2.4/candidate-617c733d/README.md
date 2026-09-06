---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
---

# Corrected 2.2.4 candidate

Source: `617c733d42a10a2fcba036385e19d66fabcc2cc1`.

Official workflow: [34063403042](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34063403042).

The merged source passed 742 hosted tests with two skips, dependency audits and
CodeQL; the combined local suite passed 744 tests. The build-only Torch advisory
exception remains documented and does not mean the wheel is patched.

- [DirectML runtime/model checks](DIRECTML_VALIDATION.md): PASS within the recorded scope.
- [DirectML static notice/payload audit](DIRECTML_COMPLIANCE_TECHNICAL.md): PASS, including all 77 added notice files matched to pinned upstream bytes.
- CUDA packaging, installed replacement, matching source and final hosted-asset checks are still pending.
- Packaged GUI Preview, physical-camera/Live Output and clean-Windows manual checks remain unperformed.

The [first candidate](../candidate-753aab70/README.md) remains archived separately.
Reports here identify the corrected binaries; later evidence commits do not
change their source identity. Model weights, raw logs and user paths remain local.
The release stays a draft until all required gates pass; v2.2.3 remains public stable.
