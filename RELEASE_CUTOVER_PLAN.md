# Windows 2.2.3 Release Cutover Plan

## Scope

Release the processed video Preview autoplay and sequential-playback repair as
`v2.2.3`, with separate CUDA and DirectML downloads from one exact source
commit. Dependency sets, installer behavior, models, and OBS implementation are
unchanged from `v2.2.2`.

## Sequence

1. Merge Preview PR #53 after its physical AMD test gate passes.
2. Prepare version, changelog, documentation, and release defaults on a
   clean release branch.
3. Run the full test suite and static/script checks.
4. Review dependency, model, and source-distribution deltas.
5. Merge the release preparation PR.
6. Wait for the exact merged production commit's required CI and CodeQL checks.
7. Create annotated tag `v2.2.3` on that exact production commit.
8. Dispatch `windows-release.yml` at the tag with the exact tagged source ref.
9. Download the combined release-candidate asset set.
10. Run strict installer, DirectML ZIP, hash, source, and manual-gate
   validation.
11. Create a draft GitHub Release, upload every listed asset, and verify live
    GitHub digests.
12. Download both draft-hosted runtime files and repeat smoke/provider checks.
13. Recheck the issue, PR, and security queues, publish the release, and
    preserve `v2.2.2` as rollback.

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

If a post-publication smoke test fails, return `v2.2.2` to latest-stable status,
mark `v2.2.3` as pre-release or draft, and open a regression issue with the
affected asset name and digest. Never replace a public binary in place without
also replacing its source archive, manifests, hashes, and release notes.
