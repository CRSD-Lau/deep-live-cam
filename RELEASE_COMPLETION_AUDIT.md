# Release Completion Audit

Release: `2.2.0`

Status: READY FOR FINAL ARTIFACT VERIFICATION

## Goal coverage

| Requirement | Evidence |
| --- | --- |
| AMD/Intel GPU support | DirectML runtime, strict provider probe, Radeon 6900 XT reporter validation |
| NVIDIA behavior preserved | CUDA provider and render validation on RTX 4070 |
| File render freeze fixed | Re-entry regression tests and local frozen-stack root-cause capture |
| Live Output preserved | Project owner and external Radeon tester confirmation |
| Reproducible Windows assets | Dual-job release workflow, portable packager, installer/source tooling |
| Hidden runtime preserved | ZIP/artifact tests require `sklearn/.libs/vcomp140.dll` |
| Model weights excluded | Runtime, portable ZIP, source, and release-asset scans |
| Corresponding source | Git-ref source archive, hash, and manifest required by validator |
| Documentation | README, changelog, DirectML guide, release notes, checklist, handoff |

## Automated evidence

- Full Python test suite passes.
- PowerShell release scripts parse.
- Release workflow YAML parses.
- DirectML portable validator tests cover required entries, hidden runtime
  DLL, SHA-256 sidecar, and forbidden model weights.
- CUDA and DirectML packaged provider/render checks passed before release
  preparation.

## Remaining publication step

The release is complete only after the exact tag is built, the combined asset
set passes strict validation, GitHub-hosted digests match, both public runtime
downloads pass post-upload smoke checks, and the draft release is published.
