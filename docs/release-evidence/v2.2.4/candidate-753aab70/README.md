---
author: Neil Mitchell
creator: Neil Mitchell
last_modified_by: Neil Mitchell
date: 2026-09-06
---

# Superseded first 2.2.4 candidate

Status: SUPERSEDED — DO NOT PUBLISH THESE ASSETS

Source: `753aab70c34ae585d525a06b9f7de2d721b7f491`

Workflow: [34056909310](https://github.com/CRSD-Lau/deep-live-cam/actions/runs/34056909310).

These byte-exact snapshots preserve the first candidate's source, processing,
model, installer and compliance evidence. `snapshot-manifest.json` records each
snapshot's size and SHA-256. Relative links and local evidence references retain
their original wording; they are historical, not current release instructions.

The official CUDA installer upgraded the actual 2.2.3 installation to 2.2.4 while
preserving seven user-data files (1,558,270,376 bytes). CUDA/RTX 4070, DirectML/AMD
device 1 and CPU image processing passed their recorded subsets. This installed
copy is the first candidate; replacing it with rebuilt 2.2.4 is a separate
same-version replacement and must have its own receipt and preservation checks.

The later CUDA inspection found pip and setuptools modules in both executable
archives without dedicated package notices. The earlier DirectML inspection
covered runtime metadata and notices but did not establish embedded build-tool
exclusion or complete notice coverage. Its narrower PASS does not close this
finding. The main build used pinned pip 26.2.1/setuptools 83.0.0; the separate
CUDA DLL-source helper still used bootstrap pip 24.0. Both findings require a
new candidate with corrected build tooling and collected package/vendor notices.

All PASS statements here apply only to these old bytes. They cannot approve a
rebuild with the same 2.2.4 version number. Preserve the original files and hashes;
record new source, binary identities and validation separately. The CUDA report's
companion JSON remains local because it includes machine paths.

The public stable release remains v2.2.3. GUI Preview, physical-camera/Live Output
and clean-Windows manual checks were not completed for this candidate.
