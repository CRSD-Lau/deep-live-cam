param(
    [string]$AppVersion = "2.2.0",
    [string]$GitRef = "HEAD",
    [string]$OutputDir = "",
    [switch]$AllowDirty,
    [switch]$FromWorkingTree
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if (-not $OutputDir) {
    $OutputDir = Join-Path $PSScriptRoot "installer"
}

Set-Location $RepoRoot
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-ArchiveRelativePath {
    param(
        [string]$BasePath,
        [string]$ChildPath
    )

    $BaseFullPath = [System.IO.Path]::GetFullPath($BasePath)
    if (-not $BaseFullPath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $BaseFullPath += [System.IO.Path]::DirectorySeparatorChar
    }
    $BaseUri = [System.Uri]::new($BaseFullPath)
    $ChildUri = [System.Uri]::new([System.IO.Path]::GetFullPath($ChildPath))
    return [System.Uri]::UnescapeDataString($BaseUri.MakeRelativeUri($ChildUri).ToString()).Replace("\", "/")
}

$Git = Get-Command git -ErrorAction SilentlyContinue
if (-not $Git) {
    throw "git was not found on PATH."
}

$Status = git status --porcelain
if ($Status) {
    if (-not $AllowDirty -and -not $FromWorkingTree) {
        throw "Working tree is dirty. Commit or stash release changes before creating the corresponding-source archive, pass -FromWorkingTree for a draft local source archive, or pass -AllowDirty only for GitRef diagnostics."
    }
    if ($FromWorkingTree) {
        Write-Warning "-FromWorkingTree creates a draft archive from the current worktree, including uncommitted and untracked files. Use a clean GitRef archive for public GitHub Releases."
    } else {
        Write-Warning "-AllowDirty permits the dirty workspace check to continue, but the source archive is still created from GitRef '$GitRef'. Uncommitted files are not included."
    }
}

$ResolvedRef = (git rev-parse --verify $GitRef).Trim()
if (-not $ResolvedRef) {
    throw "Could not resolve git ref: $GitRef"
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$ShortRef = $ResolvedRef.Substring(0, 12)
$ArchiveLabel = $ShortRef
if ($FromWorkingTree) {
    $ArchiveLabel = "worktree-$ShortRef"
}
$Archive = Join-Path $OutputDir "DeepLiveCamStudio-$AppVersion-source-$ArchiveLabel.zip"
$SourceManifest = Join-Path $OutputDir "DeepLiveCamStudio-$AppVersion-source-$ArchiveLabel.manifest.md"
$ArchivePrefix = "DeepLiveCamStudio-$AppVersion-source/"
$ForbiddenSourceSuffixes = @(".onnx", ".pth", ".safetensors")
$ForbiddenSourceDirectoryNames = @("models", "checkpoints", "model-cache", "model_cache")

$RequiredEntries = @(
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "COMPLIANCE.md",
    "Logo.png",
    "THIRD_PARTY_NOTICES.md",
    "RELEASE_CHECKLIST.md",
    "RELEASE_COMPLETION_AUDIT.md",
    "RELEASE_CUTOVER_PLAN.md",
    "RELEASE_CUTOVER_STATUS.md",
    "CLEAN_RELEASE_WORKTREE_VERIFICATION.md",
    "RELEASE_NOTES_TEMPLATE.md",
    "RELEASE_PUBLISH_HANDOFF.md",
    "RELEASE_REPORT.md",
    "RELEASE_SOURCE_PREP.md",
    "CLEAN_VM_VERIFICATION.md",
    "OBS_VIRTUAL_CAMERA_VERIFICATION.md",
    "LEGAL_REVIEW.md",
    "MODEL_DOWNLOAD_VERIFICATION.md",
    "PROCESSING_VERIFICATION.md",
    "docs/OBS_VIRTUAL_CAMERA.md",
    "docs/DIRECTML_TESTING.md",
    "LICENSES/BUNDLED_BINARY_OBLIGATIONS.md",
    "LICENSES/MODEL_LICENSE_AUDIT.md",
    "LICENSES/PYTHON_DEPENDENCIES.md",
    "LICENSES/README.md",
    "LICENSES/WINDOWS_BUNDLE_MANIFEST.md",
    "LICENSES/THIRD_PARTY_LICENSES/README.md",
    "LICENSES/THIRD_PARTY_LICENSES/tensorflow-2.19.1/package/THIRD_PARTY_NOTICES.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-gpu-1.23.2/package/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-directml-1.23.0/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/onnxruntime-directml-1.23.0/package/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opencv-python-4.10.0.84/package/LICENSE-3RD-PARTY.txt",
    "LICENSES/THIRD_PARTY_LICENSES/onnx-1.22.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/opennsfw2-0.10.2/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/PySide6-6.11.1/licenses/LicenseRef-Qt-Commercial.txt",
    "LICENSES/THIRD_PARTY_LICENSES/shiboken6-6.11.1/METADATA",
    "LICENSES/THIRD_PARTY_LICENSES/pyvirtualcam-0.15.0/licenses/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/cv2_enumerate_cameras-1.1.15/LICENSE",
    "LICENSES/THIRD_PARTY_LICENSES/easydict-1.13/LICENSE",
    ".github/workflows/windows-release.yml",
    ".github/workflows/windows-directml-test.yml",
    "DeepLiveCamStudio.pyw",
    "build/windows/build_windows.ps1",
    "build/windows/assemble_release_assets.ps1",
    "build/windows/clean_build.ps1",
    "build/windows/package_installer.ps1",
    "build/windows/package_portable.ps1",
    "build/windows/package_source.ps1",
    "build/windows/prepare_release_staging.ps1",
    "build/windows/run_release_checks.ps1",
    "build/windows/test_environment.ps1",
    "build/windows/test_packaged_runtime.ps1",
    "build/windows/test_installer.ps1",
    "build/windows/verify_clean_vm_gate.ps1",
    "build/windows/verify_legal_review_gate.ps1",
    "build/windows/verify_obs_virtualcam_gate.ps1",
    "build/windows/deep_live_cam_studio.spec",
    "build/windows/installer.iss",
    "tools/check_cuda_provider.py",
    "tools/check_obs_virtualcam.py",
    "tools/check_windows_release_cutover.py",
    "tools/collect_third_party_license_files.py",
    "tools/generate_python_dependency_licenses.py",
    "tools/generate_windows_logo_assets.py",
    "tools/prune_windows_dist.py",
    "tools/generate_windows_bundle_manifest.py",
    "tools/generate_windows_release_verification.py",
    "tools/install_windows_desktop_app.ps1",
    "tools/setup_directml.ps1",
    "tools/validate_windows_release_artifacts.py",
    "tools/summarize_manual_release_gates.py",
    "requirements.txt",
    "requirements-directml.txt",
    "run-directml.bat",
    "run.py",
    "modules/core.py",
    "modules/globals.py",
    "modules/execution_providers.py",
    "modules/face_analyser.py",
    "modules/desktop_launcher.py",
    "modules/model_manager.py",
    "modules/paths.py",
    "modules/ui.py",
    "modules/utilities.py",
    "modules/processors/frame/_onnx_enhancer.py",
    "modules/processors/frame/core.py",
    "modules/processors/frame/face_enhancer.py",
    "modules/processors/frame/face_enhancer_gpen256.py",
    "modules/processors/frame/face_enhancer_gpen512.py",
    "modules/processors/frame/face_swapper.py",
    "tests/test_image_upload_formats.py",
    "tests/test_directml_support.py",
    "tests/test_execution_providers.py",
    "tests/test_model_manager.py",
    "tests/test_validate_windows_release_artifacts.py",
    "tests/test_release_report.py",
    "tests/test_summarize_manual_release_gates.py",
    "tests/test_windows_release_scripts.py",
    "tests/test_windows_release_cutover.py",
    "tests/test_windows_release_verification.py"
)

$MissingRequiredEntries = @()
if ($FromWorkingTree) {
    foreach ($RequiredEntry in $RequiredEntries) {
        if (-not (Test-Path (Join-Path $RepoRoot $RequiredEntry))) {
            $MissingRequiredEntries += $RequiredEntry
        }
    }
} else {
    foreach ($RequiredEntry in $RequiredEntries) {
        $GitTreeEntry = git ls-tree -r --name-only $ResolvedRef -- $RequiredEntry
        if ($LASTEXITCODE -ne 0 -or $GitTreeEntry -notcontains $RequiredEntry) {
            $MissingRequiredEntries += $RequiredEntry
        }
    }
}
if ($MissingRequiredEntries) {
    $MissingRequiredEntries | ForEach-Object {
        if ($FromWorkingTree) {
            Write-Host "Missing from current worktree: $_"
        } else {
            Write-Host "Missing from source Git ref: $_"
        }
    }
    if ($FromWorkingTree) {
        throw "Current worktree does not contain required corresponding-source files. Regenerate release evidence before creating the draft source archive."
    }
    throw "Selected Git ref does not contain required corresponding-source files. Regenerate release evidence if needed, commit the packaging/compliance files, and rerun package_source.ps1 against that exact release tag or commit."
}

if ($FromWorkingTree) {
    if (Test-Path $Archive) {
        Remove-Item -LiteralPath $Archive -Force
    }
    $ExcludedDirectoryNames = @(
        ".git",
        ".superpowers",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        ".venv-build-windows",
        "venv",
        "__pycache__",
        "dist",
        "runtime"
    )
    $ExcludedRelativePrefixes = @(
        "build/windows/installer",
        "build/windows/manual-evidence",
        "build/windows/pyinstaller-work"
    )
    $SourceFiles = @(
        Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -Force |
            Where-Object {
                $Relative = Get-ArchiveRelativePath -BasePath $RepoRoot -ChildPath $_.FullName
                $Parts = @($Relative -split "/")
                $HasExcludedDirectory = @($Parts | Where-Object { $ExcludedDirectoryNames -contains $_ }).Count -gt 0
                $HasForbiddenDirectory = @($Parts | Where-Object { $ForbiddenSourceDirectoryNames -contains $_ }).Count -gt 0
                $HasExcludedPrefix = @($ExcludedRelativePrefixes | Where-Object { $Relative.StartsWith($_ + "/") -or $Relative -eq $_ }).Count -gt 0
                -not $HasExcludedDirectory -and
                    -not $HasForbiddenDirectory -and
                    -not $HasExcludedPrefix -and
                    ($ForbiddenSourceSuffixes -notcontains $_.Extension.ToLowerInvariant())
            }
    )

    if (-not $SourceFiles) {
        throw "No source files selected for draft worktree archive."
    }

    $ZipWrite = [System.IO.Compression.ZipFile]::Open($Archive, [System.IO.Compression.ZipArchiveMode]::Create)
    try {
        foreach ($SourceFile in $SourceFiles) {
            $Relative = Get-ArchiveRelativePath -BasePath $RepoRoot -ChildPath $SourceFile.FullName
            $EntryName = "$ArchivePrefix$Relative"
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($ZipWrite, $SourceFile.FullName, $EntryName, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
        }
    }
    finally {
        $ZipWrite.Dispose()
    }
} else {
    $TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "DeepLiveCamSource-$([System.Guid]::NewGuid().ToString("N"))"
    $TempExtract = Join-Path $TempRoot "extract"
    $TempRawArchive = Join-Path $TempRoot "source-raw.zip"
    New-Item -ItemType Directory -Path $TempExtract -Force | Out-Null
    try {
        git archive --format zip --output $TempRawArchive --prefix $ArchivePrefix $ResolvedRef
        if ($LASTEXITCODE -ne 0) {
            throw "git archive failed with exit code $LASTEXITCODE."
        }

        [System.IO.Compression.ZipFile]::ExtractToDirectory($TempRawArchive, $TempExtract)

        $ForbiddenDirectories = @(
            Get-ChildItem -LiteralPath $TempExtract -Recurse -Directory -Force |
                Where-Object {
                    $Relative = Get-ArchiveRelativePath -BasePath $TempExtract -ChildPath $_.FullName
                    $Parts = @($Relative -split "/")
                    @($Parts | Where-Object { $ForbiddenSourceDirectoryNames -contains $_ }).Count -gt 0
                } |
                Sort-Object -Property FullName -Descending
        )
        foreach ($ForbiddenDirectory in $ForbiddenDirectories) {
            Remove-Item -LiteralPath $ForbiddenDirectory.FullName -Recurse -Force
        }

        $ForbiddenFiles = @(
            Get-ChildItem -LiteralPath $TempExtract -Recurse -File -Force |
                Where-Object { $ForbiddenSourceSuffixes -contains $_.Extension.ToLowerInvariant() }
        )
        foreach ($ForbiddenFile in $ForbiddenFiles) {
            Remove-Item -LiteralPath $ForbiddenFile.FullName -Force
        }

        if (Test-Path $Archive) {
            Remove-Item -LiteralPath $Archive -Force
        }
        $ZipWrite = [System.IO.Compression.ZipFile]::Open($Archive, [System.IO.Compression.ZipArchiveMode]::Create)
        try {
            foreach ($SourceFile in @(Get-ChildItem -LiteralPath $TempExtract -Recurse -File -Force)) {
                $Relative = Get-ArchiveRelativePath -BasePath $TempExtract -ChildPath $SourceFile.FullName
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($ZipWrite, $SourceFile.FullName, $Relative, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
            }
        }
        finally {
            $ZipWrite.Dispose()
        }
    }
    finally {
        if (Test-Path $TempRoot) {
            Remove-Item -LiteralPath $TempRoot -Recurse -Force
        }
    }
}

$Zip = [System.IO.Compression.ZipFile]::OpenRead($Archive)
try {
    $EntryNames = @($Zip.Entries | ForEach-Object { $_.FullName })
    foreach ($RequiredEntry in $RequiredEntries) {
        $Expected = "$ArchivePrefix$RequiredEntry"
        if ($EntryNames -notcontains $Expected) {
            throw "Source archive is missing required corresponding-source file: $RequiredEntry"
        }
    }

    $GeneratedManifest = Join-Path $RepoRoot "LICENSES\WINDOWS_BUNDLE_MANIFEST.md"
    if (-not (Test-Path $GeneratedManifest)) {
        throw "Generated Windows bundle manifest missing from workspace: $GeneratedManifest. Run build_windows.ps1 or run_release_checks.ps1 before packaging source."
    }
    $ManifestText = Get-Content -LiteralPath $GeneratedManifest -Raw
    if ($ManifestText -notmatch "Forbidden model/checkpoint files found: 0") {
        throw "Generated Windows bundle manifest does not record a clean forbidden model/checkpoint scan."
    }

    $ForbiddenEntries = @(
        $EntryNames |
            Where-Object {
                $_ -match '\.(onnx|pth|safetensors)$' -or
                $_ -match '(^|/)(models|checkpoints|model-cache|model_cache)/'
            }
    )
    if ($ForbiddenEntries) {
        $ForbiddenEntries | ForEach-Object { Write-Host "Forbidden source archive entry: $_" }
        throw "Source archive contains model/checkpoint entries."
    }

    $SourceFileEntries = @($Zip.Entries | Where-Object { -not $_.FullName.EndsWith("/") })
    $SourceEntryCount = $SourceFileEntries.Count
    $SourcePayloadBytes = ($SourceFileEntries | Measure-Object -Property Length -Sum).Sum
}
finally {
    $Zip.Dispose()
}

$HashPath = "$Archive.sha256"
$Hash = Get-FileHash $Archive -Algorithm SHA256
"$($Hash.Hash)  $(Split-Path $Archive -Leaf)" | Set-Content -LiteralPath $HashPath -Encoding ascii

$ManifestLines = @(
    "# Corresponding Source Archive Manifest",
    "",
    "Generated: $((Get-Date).ToUniversalTime().ToString("o"))",
    "App version: ``$AppVersion``",
    "Git ref requested: ``$GitRef``",
    "Git ref resolved: ``$ResolvedRef``",
    "Archive mode: ``$(if ($FromWorkingTree) { "draft-working-tree" } else { "git-ref" })``",
    "Archive: ``$Archive``",
    "Archive SHA-256: ``$($Hash.Hash)``",
    "Archive file entries: $SourceEntryCount",
    "Archive payload bytes: $SourcePayloadBytes",
    "",
    "## Required Corresponding-Source Entries",
    ""
)
foreach ($RequiredEntry in $RequiredEntries) {
    $ManifestLines += "- [x] ``$RequiredEntry``"
}
$ManifestLines += @(
    "",
    "## Forbidden Model/Checkpoint Scan",
    "",
    "- [x] No ``.onnx``, ``.pth``, ``.safetensors``, ``models/``, ``checkpoints/``, or model-cache entries were found.",
    "",
    "## Notes",
    "",
    "- This manifest is generated from the source archive after content validation.",
    "- The Windows bundle manifest remains separate release evidence generated from the PyInstaller payload.",
    "$(if ($FromWorkingTree) { "- This is a draft archive from the current worktree. For public GitHub Releases, create a clean release tag/commit and rerun without ``-FromWorkingTree``." } else { "- This archive was created with ``git archive`` from the resolved Git ref." })",
    ""
)
$ManifestLines | Set-Content -LiteralPath $SourceManifest -Encoding utf8

Write-Host "Source archive created at: $Archive"
Write-Host "Source archive SHA-256 written to: $HashPath"
Write-Host "Source archive manifest written to: $SourceManifest"
Write-Host "Source archive ref: $ResolvedRef"
Write-Host "Source archive SHA-256: $($Hash.Hash)"
Write-Host "Source archive content verification passed."
