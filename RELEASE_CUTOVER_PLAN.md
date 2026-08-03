# Windows 2.2.1 Release Cutover Plan

## Scope

Release the dependency, pipeline, and repository-maintenance work as `v2.2.1`,
with separate CUDA and DirectML downloads from one exact source commit.

## Sequence

1. Merge the dependency, orchestration, and repository-administration PRs.
2. Prepare version, changelog, documentation, and dual-runtime release CI on a
   clean release branch.
3. Run the full test suite and static/script checks.
4. Review dependency, model, and source-distribution deltas.
5. Merge the release preparation PR.
6. Dispatch `windows-release.yml` for `v2.2.1` and the exact merged commit.
7. Verify the release assets, then create annotated tag `v2.2.1` on that same
   production commit.
8. Download the combined release-candidate asset set.
9. Run strict installer, DirectML ZIP, hash, source, and manual-gate
   validation.
10. Create a draft GitHub Release, upload every listed asset, and verify live
    GitHub digests.
11. Download both public runtime files and repeat smoke/provider checks.
12. Close issue #8, verify every issue/PR/security queue is empty, publish the
    release, and preserve `v2.2.0` as rollback.

## Stop conditions

Do not publish if any of the following is true:

- automated tests or a required workflow job fails;
- CUDA or DirectML provider checks fall back unexpectedly;
- the DirectML ZIP lacks `_internal/sklearn/.libs/vcomp140.dll`;
- any runtime or source archive contains model/checkpoint weights;
- source archive mode is not `git-ref` or does not resolve to the exact merged
  release commit;
- manual gate summary is not fully passed;
- public GitHub asset hashes differ from the local verified files.

## Rollback

If a post-publication smoke test fails, return `v2.2.0` to latest-stable status,
mark `v2.2.1` as pre-release or draft, and open a regression issue with the
affected asset name and digest. Never replace a public binary in place without
also replacing its source archive, manifests, hashes, and release notes.
