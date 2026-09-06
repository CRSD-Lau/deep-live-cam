---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# 2.2.4 release evidence

The [first candidate](candidate-753aab70/README.md) is superseded because final
payload inspection found missing embedded-package notices. Its original evidence
is preserved with file hashes. The corrected candidate must have its own exact
source SHA, artifact identities, notice inspection and runtime validation.

Active gate documents at the repository root remain PENDING until corresponding
checks are completed against the replacement bytes. Matching the version string
alone does not transfer a previous candidate's approval. Keep v2.2.4 as a draft
until all current release gates pass; v2.2.3 remains public stable.
