# Windows 2.2.0 Release Cutover Plan

## Scope

Release the validated DirectML/AMD support and Preview/Render deadlock fix as
`v2.2.0`, with separate CUDA and DirectML downloads from one exact source tag.

## Sequence

1. Merge the runtime fix and reporter-validated PR.
2. Prepare version, changelog, documentation, and dual-runtime release CI on a
   clean release branch.
3. Run the full test suite and static/script checks.
4. Review dependency, model, and source-distribution deltas.
5. Merge the release preparation PR.
6. Create annotated tag `v2.2.0` on the production release commit.
7. Dispatch `windows-release.yml` for `v2.2.0` and the exact tag.
8. Download the combined release-candidate asset set.
9. Run strict installer, DirectML ZIP, hash, source, and manual-gate
   validation.
10. Create a draft GitHub Release, upload every listed asset, and verify live
    GitHub digests.
11. Download both public runtime files and repeat smoke/provider checks.
12. Publish the release, close issue #3, and preserve `v2.1.9` as rollback.

## Stop conditions

Do not publish if any of the following is true:

- automated tests or a required workflow job fails;
- CUDA or DirectML provider checks fall back unexpectedly;
- the DirectML ZIP lacks `_internal/sklearn/.libs/vcomp140.dll`;
- any runtime or source archive contains model/checkpoint weights;
- source archive mode is not `git-ref` or does not resolve to the release tag;
- manual gate summary is not fully passed;
- public GitHub asset hashes differ from the local verified files.

## Rollback

If a post-publication smoke test fails, return `v2.1.9` to latest-stable status,
mark `v2.2.0` as pre-release or draft, and open a regression issue with the
affected asset name and digest. Never replace a public binary in place without
also replacing its source archive, manifests, hashes, and release notes.
