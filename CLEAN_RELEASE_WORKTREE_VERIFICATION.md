# Clean Release Worktree Verification

Release: `2.2.0`

Status: READY FOR RELEASE-CANDIDATE BUILD

The release was prepared in an isolated worktree. Unrelated local work and the
prior DirectML test worktree were outside the release scope.

## Completed source proof

- [x] Release preparation started from the production branch after PR #4 was
  merged.
- [x] Only release-owned source, tests, workflow, version, and documentation
  files are changed in this worktree.
- [x] Model/checkpoint files are not staged.
- [x] Full tests pass before release-branch publication.

## Post-merge proof

The release operator must still verify that the preparation PR is merged,
annotated tag `v2.2.0` resolves to the final production commit, source
packaging runs from that tag in `git-ref` mode, and the tag checkout is clean.
Those results belong in the generated `RELEASE_VERIFICATION.md` distributed
with the final asset set; this source document intentionally does not claim
that future work has already happened.
