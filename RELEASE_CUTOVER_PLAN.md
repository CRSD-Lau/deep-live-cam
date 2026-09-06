---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Windows 2.2.4 Release Cutover Plan

Status: DRAFT — FINAL ARTIFACT AND MANUAL VERIFICATION PENDING

## Scope

Release the export-integrity, Unicode-path, temporary-workspace, model-transfer,
settings and camera-lifecycle fixes as `v2.2.4`. CUDA and DirectML remain separate
downloads. The binary and corresponding-source commit is fixed at
`753aab70c34ae585d525a06b9f7de2d721b7f491`. Later documentation/attestation commits
do not change this artifact identity. Preserve `v2.2.3` as rollback.

## Complete the current candidate

1. Confirm the exact merged source's required CI and CodeQL results. Candidate
   workflow [34056909310](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34056909310)
   must finish successfully for both runtime profiles and source packaging.
2. Download and hash the complete official asset set. Require both binary jobs
   and the source manifest to identify the fixed commit above.
3. Validate CUDA and DirectML separately, including provider identity, real
   processing, Unicode exports, video/audio integrity and failure retention.
4. Verify the exact official installer and stable 2.2.3 upgrade with user-data
   preservation. Keep clean-Windows, legacy migration and uninstall evidence
   separate from that host upgrade and from the rebuilt test-GUID fixture.
5. Complete the final packaged GUI/Preview/Live Output, receiving-application,
   model-setup and compliance gates in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).
6. Record honest current-release evidence in the documentation follow-up.
   Archive older preparation snapshots; do not relabel historical PASS claims.
   Keep the original verified binaries and git-ref source archive unchanged.
7. Verify the annotated `v2.2.4` tag resolves to the binary/source commit.
   Complete the existing draft's asset set and reviewed release notes.
8. Compare hosted digests and download both draft-hosted runtime assets for
   repeat official-byte checks.
9. Recheck the repository queue and security alerts, then publish only when
   the strict 2.2.4 manual summary and generated publish-readiness report pass.
10. Verify public downloads and retain the recorded `v2.2.3` rollback path.

## Stop conditions

Keep the draft unpublished if required tests, jobs, provider or artifact checks
fail; source or hashes do not match; model/checkpoint weights are distributed;
the DirectML ZIP lacks `_internal/sklearn/.libs/vcomp140.dll`; or any required
current-release manual gate remains pending. Historical hardware reports,
synthetic virtual-camera tests, and an upgrade on a configured workstation
cannot close the distinct final-GUI and clean-Windows checks.

The complete handling and rollback procedure is in
[RELEASE_PUBLISH_HANDOFF.md](RELEASE_PUBLISH_HANDOFF.md).
