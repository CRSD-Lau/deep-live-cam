---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Documentation

Use this index to find the right guide without searching through release and compliance files.

## Use Deep Live Cam Studio

| Guide | Purpose |
| --- | --- |
| [Project README](../README.md) | Download selection, quick start, requirements, and project overview |
| [DirectML testing](DIRECTML_TESTING.md) | AMD/Intel setup, adapter selection, and strict provider verification |
| [OBS Virtual Camera](OBS_VIRTUAL_CAMERA.md) | Live-output setup, routing, and troubleshooting |
| [Support](../SUPPORT.md) | Where to ask questions, report bugs, or disclose vulnerabilities |

## Develop and Test

| Guide | Purpose |
| --- | --- |
| [Build from source](BUILDING.md) | CUDA and DirectML environments, tests, packaging, and local verification |
| [Dependency locks](DEPENDENCY_LOCKS.md) | Supported Windows matrix and reproducible dependency updates |
| [Contributing](../CONTRIBUTING.md) | Contribution scope, required evidence, and pull-request expectations |
| [Engineering audit](../REPOSITORY_AUDIT.md) | Current architecture, quality findings, and deferred technical work |
| [September 2026 project review](PROJECT_REVIEW_2026-09-06.md) | Export integrity and lifecycle fixes, validation, and remaining limits |

## Maintain and Release

| Guide | Purpose |
| --- | --- |
| [Governance](../GOVERNANCE.md) | Project scope, decision-making, support promises, and hardware claims |
| [Release checklist](../RELEASE_CHECKLIST.md) | Required technical, hardware, legal, and publication gates |
| [Source preparation](../RELEASE_SOURCE_PREP.md) | Exact source for the fixed binary commit, separate from later attestations |
| [Historical release preparation](release-evidence/v2.2.3/preparation/README.md) | Archived 2.2.3 snapshots; their PASS and READY claims do not approve 2.2.4 |
| [Release handoff](../RELEASE_PUBLISH_HANDOFF.md) | Current 2.2.4 draft, fixed artifact commit, remaining publication gates and 2.2.3 rollback |
| [Compliance](../COMPLIANCE.md) | AGPL corresponding-source and third-party obligations |
| [Licence evidence](../LICENSES/README.md) | Model, package, and bundled-binary licence records |
| [Security policy](../SECURITY.md) | Supported releases and private reporting process |

Files ending in `VERIFICATION.md`, `REPORT.md`, or `AUDIT.md` are evidence records. They support release decisions but are not the starting point for ordinary users.

The current candidate is **2.2.4**. A corrected build is being prepared because
the first candidate was missing embedded-package notices. It stays a draft while required
artifact or manual checks remain pending; `v2.2.3` remains the rollback release.
Later documentation commits record attestations without changing that build
identity. The [first candidate's evidence](release-evidence/v2.2.4/candidate-753aab70/README.md)
is retained with its original hashes and does not approve replacement binaries.
