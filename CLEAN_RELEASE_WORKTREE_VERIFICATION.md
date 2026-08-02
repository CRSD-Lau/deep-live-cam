# Clean Release Worktree Verification

Release: `2.2.0`

Status: PENDING FINAL TAG

The release is prepared in the isolated worktree
`C:\Projects\deep-live-cam-release-2.2.0`. The original checkout's Voice Lab
work and the prior DirectML test worktree are outside this release scope.

## Required final proof

- [x] Release preparation started from the production branch after PR #4 was
  merged.
- [x] Only release-owned source, tests, workflow, version, and documentation
  files are changed in this worktree.
- [x] Model/checkpoint files are not staged.
- [x] Full tests pass before release-branch publication.
- [ ] Release preparation PR is merged.
- [ ] Annotated tag `v2.2.0` resolves to the final production commit.
- [ ] Source packaging runs from `v2.2.0` in `git-ref` mode.
- [ ] Final production branch and tag worktrees are clean.

This file is finalized immediately before tagging and is included in the exact
corresponding-source archive.
