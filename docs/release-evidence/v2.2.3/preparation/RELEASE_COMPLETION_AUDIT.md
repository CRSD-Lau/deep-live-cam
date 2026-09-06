# Release Completion Audit

Release: `2.2.3`

Status: READY FOR FINAL ARTIFACT VERIFICATION

## Goal coverage

| Requirement | Evidence |
| --- | --- |
| AMD/Intel GPU support | DirectML runtime, strict provider probe, Radeon 6900 XT reporter validation, Radeon RX 9060 XT independent validation |
| NVIDIA behavior preserved | CUDA provider and render validation on RTX 4070 |
| Processed video Preview autoplay | Radeon RX 6900 XT PASS for autoplay, stable geometry, sequential no-skip playback, controls, seeking, and close; exact-head regression tests and DirectML package build |
| Preview throughput represented accurately | Low achieved FPS retained as a separate processing-throughput observation; no 30 FPS cap or real-time guarantee claimed |
| File render freeze fixed | Re-entry regression tests and local frozen-stack root-cause capture |
| Live Output preserved | Project owner, issue reporter, and independent Radeon tester confirmation |
| Reproducible Windows assets | Dual-job release workflow, portable packager, installer/source tooling |
| Unambiguous NVIDIA updates | Stable install directory, registered legacy migration, orphan cleanup, isolated upgrade fixture |
| Hidden runtime preserved | ZIP/artifact tests require `sklearn/.libs/vcomp140.dll` |
| Model weights excluded | Runtime, portable ZIP, source, and release-asset scans |
| Corresponding source | Git-ref source archive, hash, and manifest required by validator |
| Documentation | Modernized README hero, documentation index, governance policies, changelog, release notes, checklist, handoff |

## Automated evidence

- Full Python test suite passes.
- PowerShell release scripts parse.
- Release workflow YAML parses.
- DirectML portable validator tests cover required entries, hidden runtime
  DLL, SHA-256 sidecar, and forbidden model weights.
- CUDA and DirectML packaged provider/render checks passed before release
  preparation.
- The full final source suite passes 514 tests, including focused Preview
  lifecycle, sequential decoding, pacing, geometry, and temporal-state checks.

## Remaining publication step

The release is complete only after the exact merged commit is built, the combined asset
set passes strict validation, GitHub-hosted digests match, both public runtime
downloads pass post-upload smoke checks, and the draft release is published.
