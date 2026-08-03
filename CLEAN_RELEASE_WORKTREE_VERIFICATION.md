# Clean Release Worktree Verification

Release: `2.2.1`

Status: READY FOR RELEASE-CANDIDATE BUILD

The release was prepared in an isolated worktree. Unrelated local work and the
prior DirectML test worktree were outside the release scope.

## Completed source proof

- [x] Release preparation started from the production branch after PRs #20,
  #27, #34, #35, #41, and #42 were merged.
- [x] Only release-owned source, tests, workflow, version, and documentation
  files are changed in this worktree.
- [x] Model/checkpoint files are not staged.
- [x] Full tests pass before release-branch publication.

## Post-merge proof

The release operator must still verify that the preparation PR is merged,
annotated tag `v2.2.1` resolves to the final production commit, source
packaging runs from that exact commit in `git-ref` mode, and the checkout is
clean.
Those results belong in the generated `RELEASE_VERIFICATION.md` distributed
with the final asset set; this source document intentionally does not claim
that future work has already happened.
