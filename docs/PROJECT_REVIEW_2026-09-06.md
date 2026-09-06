---
author: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Project review — 6 September 2026

This review prioritizes reliable exports, preservation of existing files, and
recovery from failed operations. The fixes were merged in [PR #62](https://github.com/CRSD-Lau/deep-live-cam/pull/62)
and [PR #63](https://github.com/CRSD-Lau/deep-live-cam/pull/63).
The initial review used default-branch commit `8ce01f795b0558e77de255b9fa1c839a8a6a738b`;
release preparation incorporates the subsequent `9bdb9cf` audit documentation fix.
This is source-review evidence, not a new binary release approval.

## Coverage and approach

The project-wide pass covered the CLI and desktop entry points, file rendering,
Preview and live-output lifecycle, camera capture, processor dispatch, analysis,
tracking/compositing/quality modules, model downloads, settings, diagnostic
reports, dependency profiles, Windows packaging scripts, CI, and public docs.
First-party tests and release validators were reviewed alongside implementation.
Third-party library internals were inspected only where needed to trace behavior;
bundled third-party code, models, licences, and binary assets were not rewritten.

Three independent review passes and two anonymized peer reviews agreed that
output-integrity defects offered the strongest immediate improvement. All used
the same model; these were independent inspections, not cross-provider review.
Temporary-directory ownership received extra scrutiny because face mapping
extracts frames before rendering starts. No performance or visual-quality gains
are claimed from the source changes.

## Implemented findings

| Area | Previous failure | Change |
| --- | --- | --- |
| FFmpeg diagnostics | Undrained stderr pipes could fill and block an export. | Owned temporary diagnostic files avoid pipe saturation; error output is limited to a 64 KiB tail. |
| Decode completion | A successful encoder could conceal a failed decoder or incomplete final frame. | Check both process exit statuses, accumulate short reads, and reject partial frames. |
| Process cleanup | Startup, metrics, or QA failures could leave children and streams open. | Close and reap children across success and failure paths. |
| Image rendering | Failed preparation or image writes could be reported as success. | Process into a destination-side staging file, require processor success, decode-check the result, then replace the requested file. |
| Video publication | The existing destination was deleted before moving the new file. Audio restoration wrote directly to it. | Stage copy/remux beside the destination and replace only on success; silent source videos use optional audio mapping. |
| Temporary frames | Predictable input-adjacent directories could collide with existing folders, retained frames, or another video with the same stem. | Track unique process-owned workspaces, preserve the mapper-to-render handoff, and print retained-frame locations. |
| Settings | Valid JSON with invalid types could crash startup; interrupted saves could truncate the prior settings. | Validate values and preserve valid choices; save atomically. |
| Live startup | Camera construction and partially opened backends could leave resources active after failure. | Release partial capture/virtual-output state and report startup failure. |
| Operation overlap | File rendering and live output could use shared processor state concurrently. | Gate overlapping operations while preserving the active operation. |
| Model transfers | Interrupted downloads left partial files; final-URL checking happened after insecure redirects were followed. | Use unique temporary downloads, clean them on failure, and reject insecure redirects before the redirected request. |
| CLI and probes | Missing output normalization could raise a TypeError; invalid resource values and missing ffprobe failed unclearly. | Handle absent output safely, validate resource inputs, and check both FFmpeg executables. |

## Validation

The unchanged baseline passed all 514 tests. Ruff's CI-critical selection and
Bandit's medium/high checks also passed before modification.

The initial integrated review suite passed **619 tests**, including **105 additional
regression/integration cases**, in 11.83 seconds. It used Python 3.11.9, ONNX
Runtime DirectML 1.23.0, and pinned pytest 9.1.1/Ruff 0.16.5 tools in an isolated
overlay. CI-critical Ruff checks passed; Bandit found no medium/high issues
(32 low-severity findings remain). The existing CUDA development environment was
used for the baseline and focused regressions; it is not a freshly locked CUDA
installation.

The real media integration tests generate non-personal 96×64 clips with twelve
frames at 12 FPS. They exercise the FFmpeg pipe export, destination replacement,
audio and silent-video remux, ffprobe frame/dimension/duration checks, full output
decode, and workspace cleanup. Separate real subprocess regressions write 2 MiB
of stderr from each child to exercise the previous pipe-capacity failure.
An additional physical D: to C: publication check verified cross-volume output
replacement and private-workspace cleanup. No inference or personal media was
used in these I/O checks.

Dependency-lock regeneration in check mode reports current locks. The CUDA and
DirectML runtime lock audits report no known vulnerabilities. The existing
build-only Torch audit passes with its one pre-existing `PYSEC-2025-194`
exception; this review neither adds nor broadens that exception.

## Remaining limits and follow-up

- **Dependency-managed model setup remains separate.** Current InsightFace
  `FaceAnalysis` can fetch the missing `buffalo_l` analysis bundle automatically.
  Optional OpenNSFW2 model initialization can also fetch missing weights. These
  paths are outside the application's reviewed download catalogue. README now
  states this limitation. Integrating them requires reviewed sources/checksums,
  consent UX, and compatibility testing with existing caches; it is not solved
  by the transfer-cleanup patch.
- **Physical hardware and packaged builds need release validation.** Camera
  failure tests use mocks; Qt runs offscreen. No claim is made about a new
  physical-camera/OBS stability run, face-swap visual quality, NVIDIA/AMD/Intel
  performance, clean-VM installation, or published binary behavior. Existing
  release evidence remains historical.
- **Large UI and processor modules remain.** Splitting them and tuning inference
  or temporal behavior would require broader characterization and representative
  media. Their size alone does not justify combining a redesign with these fixes.
- **Per-frame inference recovery is unchanged.** Disk-based frame processors can
  still log and recover from individual processing failures. The explicit image
  success contract and FFmpeg completion checks do not establish that every
  rendered video frame underwent a successful face transformation.
- FFmpeg diagnostic capture uses temporary disk space. Error reads are bounded,
  but unusually verbose failing decoders can grow those temporary files until
  processing ends. No new watchdog for hung GPU drivers or native camera calls
  is introduced.

At the end of the initial source-review pass, the installed application, model
caches, settings, recordings, other projects, tags, and hosted releases had not
been modified. The subsequently authorized release work is recorded separately
below and in the current release evidence.

## Subsequent release validation and improvements

Release preparation added strict version-matched manual-evidence checks and an
immutable source resolver for the CUDA, DirectML, and corresponding-source jobs.
Packaging now uses the actual build environment for dependency/license snapshots.
Hooks advance to 2026.7 and Ruff to 0.16.5; runtime dependency versions retain the
reviewed locks and the scoped build-only Torch exception remains documented.

Real Windows inference exposed an additional Unicode export defect: OpenCV's
filename-based writer could create a mojibake sibling while the requested output
remained unchanged. Shared Unicode-safe encoding and atomic publication now cover
all four processors, mapper images, visual QA, and export tools. Regressions also
confirm that an unsupported output format preserves an existing Unicode-named file.

The resulting source at `753aab70c34ae585d525a06b9f7de2d721b7f491` passed
**722 local tests**; exact-commit hosted CI passed **720 tests with 2 skipped**.
The official and freshly draft-downloaded DirectML bytes passed real AMD device-1
inference, with full image/video and failure-preservation evidence for the same
ZIP hash. Separate current evidence covers fresh model downloads and the actual
OBS virtual-camera driver/receiver subset. These are scoped checks, not a claim
that physical-camera, clean-Windows, or packaged GUI/manual gates are complete.

See [the current release report](../RELEASE_REPORT.md),
[publication handoff](../RELEASE_PUBLISH_HANDOFF.md), and
[first-candidate DirectML inspection](release-evidence/v2.2.4/candidate-753aab70/DIRECTML_COMPLIANCE_TECHNICAL.md).
The 2.2.4 candidate remains a draft while mandatory release checks are pending;
historical 2.2.3 evidence is retained under `docs/release-evidence/v2.2.3/`.

The first official CUDA installer subsequently passed an actual 2.2.3-to-2.2.4
upgrade with seven unchanged user-data files, real NVIDIA CUDA image/audio/silent
video processing, and CPU image fallback. Deeper executable inspection then found
embedded pip/setuptools modules without dedicated notices. The first candidate is
superseded; its byte-exact evidence is archived under
`docs/release-evidence/v2.2.4/candidate-753aab70/`.

The corrected candidate collects package/vendor notices, uses the locked main pip
for the CUDA DLL-source helper, and speeds up only the isolated installer test
fixture's compression. The public installer retains its compression settings and
all migration/uninstall assertions remain required. Replacement bytes require
fresh source, hash, payload and runtime validation; the shared 2.2.4 version does
not transfer earlier PASS claims.
