# Project Governance

Deep Live Cam Studio is maintained as a Windows-focused derivative of Deep-Live-Cam. This document explains how scope, support, and release decisions are made.

## Maintainer

The repository owner, [@CRSD-Lau](https://github.com/CRSD-Lau), is the current project maintainer and final decision maker for releases, security responses, repository administration, and project scope.

## Project Scope

The project prioritizes:

- reliable Windows desktop packaging;
- CUDA and DirectML execution profiles;
- file rendering and OBS/virtual-camera workflows;
- explicit model consent and checksum verification;
- reproducible dependency locks and release assets;
- AGPL corresponding-source and third-party licence compliance.

Cross-platform changes are welcome when they preserve the supported Windows paths and include a realistic maintenance plan.

## Decisions and Contributions

Small fixes are decided through focused pull requests. Larger features or architectural changes should begin with an issue or Discussion that defines the user problem, affected surfaces, risks, and validation evidence.

The maintainer may defer, split, or reject work that lacks reproducible evidence, expands the support burden without ownership, weakens security or compliance, or mixes unrelated changes.

## Hardware Claims

Automated tests can prove dependency resolution, packaging, and provider activation on available runners. They cannot replace every physical camera, driver, GPU, render, or OBS test.

A hardware-specific claim is considered validated only when the evidence identifies the physical GPU and driver, confirms the requested provider in an actual session, and exercises the affected Preview, Render, or Live Output workflow. When physical evidence is unavailable, documentation and release notes must state the limitation instead of treating an assumption as validation.

## Releases

Stable releases require the gates in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md). Release candidates may be used to gather missing hardware evidence, but they must not be promoted to stable while a required manual or legal gate remains open.

## Security and Conduct

Security reports follow [SECURITY.md](SECURITY.md). Community participation follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Maintainers will keep sensitive reports private and communicate public decisions when doing so does not compromise a reporter, user, or coordinated disclosure.

## Upstream Relationship

Useful upstream fixes should retain attribution and be structured so they can be shared where practical. This derivative may make different Windows packaging or release decisions from upstream; those differences must remain visible in documentation and source history.
