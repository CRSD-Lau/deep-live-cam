# Windows Release Verification

App version: `2.2.0`

Status: RELEASE PREPARATION

This committed report describes the source state before the final tagged build.
The generated copy in the GitHub Release asset set contains the exact binary
and source hashes used for publication.

- Local installer automation passed: PENDING FINAL TAGGED BUILD
- DirectML portable runtime validation passed: PENDING FINAL TAGGED BUILD
- Public-release source archive from clean Git ref: PENDING `v2.2.0`
- Manual clean-install gate: PASS (risk-based delta revalidation required on final asset)
- Manual OBS/Live Output gate: PASS (CUDA and Radeon DirectML hardware evidence)
- Manual legal/compliance gate: PASS (DirectML dependency delta documented)
- Ready to publish without remaining manual gates: NO — FINAL ASSET AND PUBLIC-DOWNLOAD VERIFICATION REQUIRED

The final release workflow and strict local checks overwrite this preparation
report in the assembled upload set. Publication is blocked unless that generated
report says `Ready to publish without remaining manual gates: YES`.
