# Release Source Preparation

Release: `2.2.1`

The AGPL corresponding-source archive must be created from the exact merged
release commit after all release-owned source and documentation changes are
merged. The annotated tag is created on that same commit after asset
verification.

## Prepare

```powershell
git fetch crsd --tags
git status --short
git show --no-patch --decorate RELEASE_COMMIT
```

The release tree must contain only committed files. Build outputs, virtual
environments, model files, logs, and user data remain untracked and excluded.

## Package exact source

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.2.1 -GitRef RELEASE_COMMIT
```

Required output:

- `DeepLiveCamStudio-2.2.1-source-<ref>.zip`
- matching `.zip.sha256`
- matching `.manifest.md`

The manifest must report `Archive mode: git-ref`, the resolved tag commit, all
required source entries, and a passing forbidden-model scan.

## Validate

```powershell
python tools\validate_windows_release_artifacts.py --app-version 2.2.1 --require-git-ref-source
```

The source must include application code, build and installer scripts, CUDA
and DirectML dependency definitions, both GitHub workflows, tests, licences,
compliance documents, and the portable packaging script. It must not include
`.onnx`, `.pth`, `.safetensors`, `models/`, `checkpoints/`, secrets, local
virtual environments, or build output.

Publish the exact source archive beside both binary runtime downloads. A green
repository source link alone is not a substitute for identifying the exact
corresponding source used for the release.
