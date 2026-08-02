param(
    [string]$AppVersion = "2.2.0",
    [string]$InstallerDir = "",
    [string]$PortableDir = "",
    [string]$OutputDir = "",
    [string]$Python = "python",
    [switch]$RequireGitRefSource
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if (-not $InstallerDir) {
    $InstallerDir = Join-Path $PSScriptRoot "installer"
}
if (-not $OutputDir) {
    $OutputDir = Join-Path $PSScriptRoot "release-assets\$AppVersion"
}

Set-Location $RepoRoot

$PythonCandidates = @(
    (Join-Path $RepoRoot "venv\Scripts\python.exe"),
    (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
    $Python
)
$CheckPython = ($PythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
if (-not $CheckPython) {
    $CheckPython = $Python
}

$ValidatorArgs = @(
    "tools\validate_windows_release_artifacts.py",
    "--repo-root", $RepoRoot,
    "--output-dir", $InstallerDir,
    "--app-version", $AppVersion
)
if ($RequireGitRefSource) {
    $ValidatorArgs += "--require-git-ref-source"
}
& $CheckPython @ValidatorArgs
if ($LASTEXITCODE -ne 0) {
    throw "Release artifact validation failed with exit code $LASTEXITCODE."
}

function Read-SourceManifestText {
    param([System.IO.FileInfo]$Archive)

    $Manifest = [System.IO.Path]::ChangeExtension($Archive.FullName, ".manifest.md")
    if (-not (Test-Path -LiteralPath $Manifest)) {
        return ""
    }
    return Get-Content -LiteralPath $Manifest -Raw
}

$Installer = Join-Path $InstallerDir "DeepLiveCamStudio-$AppVersion-x64-setup.exe"
$InstallerHash = "$Installer.sha256"
if (-not (Test-Path -LiteralPath $Installer)) {
    throw "Installer missing: $Installer"
}
if (-not (Test-Path -LiteralPath $InstallerHash)) {
    throw "Installer SHA-256 sidecar missing: $InstallerHash"
}

$PortableArchive = $null
$PortableHash = $null
$PortableDigest = ""
if ($PortableDir) {
    $PortableDir = [System.IO.Path]::GetFullPath($PortableDir)
    $PortableArchive = Join-Path $PortableDir "DeepLiveCamStudio-$AppVersion-DirectML-x64-portable.zip"
    $PortableHash = "$PortableArchive.sha256"
    if (-not (Test-Path -LiteralPath $PortableArchive -PathType Leaf)) {
        throw "DirectML portable archive missing: $PortableArchive"
    }
    if (-not (Test-Path -LiteralPath $PortableHash -PathType Leaf)) {
        throw "DirectML portable SHA-256 sidecar missing: $PortableHash"
    }
    $PortableDigest = (Get-FileHash -LiteralPath $PortableArchive -Algorithm SHA256).Hash
    $SidecarDigest = ((Get-Content -LiteralPath $PortableHash -Raw).Trim() -split "\s+")[0].ToUpperInvariant()
    if ($SidecarDigest -ne $PortableDigest) {
        throw "DirectML portable SHA-256 sidecar does not match: $PortableHash"
    }
}

$SourceArchives = @(
    Get-ChildItem -LiteralPath $InstallerDir -Filter "DeepLiveCamStudio-$AppVersion-source-*.zip" -File |
        Where-Object {
            $ManifestText = Read-SourceManifestText -Archive $_
            if ($RequireGitRefSource) {
                $ManifestText -match "Archive mode:\s*``git-ref``"
            } else {
                $ManifestText
            }
        } |
        Sort-Object LastWriteTime, Name
)
if (-not $SourceArchives) {
    throw "No matching source archive found in $InstallerDir."
}
$SourceArchive = $SourceArchives[-1]
$SourceHash = "$($SourceArchive.FullName).sha256"
$SourceManifest = [System.IO.Path]::ChangeExtension($SourceArchive.FullName, ".manifest.md")
if (-not (Test-Path -LiteralPath $SourceHash)) {
    throw "Source SHA-256 sidecar missing: $SourceHash"
}
if (-not (Test-Path -LiteralPath $SourceManifest)) {
    throw "Source manifest missing: $SourceManifest"
}

$OutputParent = Split-Path -Parent ([System.IO.Path]::GetFullPath($OutputDir))
if (-not (Test-Path -LiteralPath $OutputParent)) {
    New-Item -ItemType Directory -Path $OutputParent -Force | Out-Null
}
$StagingDir = Join-Path $OutputParent ("." + (Split-Path -Leaf $OutputDir) + ".staging-" + [System.Guid]::NewGuid().ToString("N"))
$BackupDir = Join-Path $OutputParent ("." + (Split-Path -Leaf $OutputDir) + ".old-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

$FilesToCopy = @(
    $Installer,
    $InstallerHash,
    $SourceArchive.FullName,
    $SourceHash,
    $SourceManifest,
    (Join-Path $RepoRoot "README.md"),
    (Join-Path $RepoRoot "CHANGELOG.md"),
    (Join-Path $RepoRoot "LICENSE"),
    (Join-Path $RepoRoot "RELEASE_NOTES_TEMPLATE.md"),
    (Join-Path $RepoRoot "RELEASE_PUBLISH_HANDOFF.md"),
    (Join-Path $RepoRoot "RELEASE_SOURCE_PREP.md"),
    (Join-Path $RepoRoot "RELEASE_VERIFICATION.md"),
    (Join-Path $RepoRoot "RELEASE_CHECKLIST.md"),
    (Join-Path $RepoRoot "RELEASE_COMPLETION_AUDIT.md"),
    (Join-Path $RepoRoot "RELEASE_CUTOVER_PLAN.md"),
    (Join-Path $RepoRoot "RELEASE_CUTOVER_STATUS.md"),
    (Join-Path $RepoRoot "CLEAN_RELEASE_WORKTREE_VERIFICATION.md"),
    (Join-Path $RepoRoot "RELEASE_REPORT.md"),
    (Join-Path $RepoRoot "CLEAN_VM_VERIFICATION.md"),
    (Join-Path $RepoRoot "OBS_VIRTUAL_CAMERA_VERIFICATION.md"),
    (Join-Path $RepoRoot "LEGAL_REVIEW.md"),
    (Join-Path $RepoRoot "MODEL_DOWNLOAD_VERIFICATION.md"),
    (Join-Path $RepoRoot "PROCESSING_VERIFICATION.md"),
    (Join-Path $RepoRoot "COMPLIANCE.md"),
    (Join-Path $RepoRoot "THIRD_PARTY_NOTICES.md"),
    (Join-Path $RepoRoot "LICENSES\BUNDLED_BINARY_OBLIGATIONS.md"),
    (Join-Path $RepoRoot "LICENSES\MODEL_LICENSE_AUDIT.md"),
    (Join-Path $RepoRoot "LICENSES\PYTHON_DEPENDENCIES.md"),
    (Join-Path $RepoRoot "LICENSES\WINDOWS_BUNDLE_MANIFEST.md")
)
if ($PortableArchive) {
    $FilesToCopy += $PortableArchive
    $FilesToCopy += $PortableHash
}
foreach ($Path in $FilesToCopy) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required release asset input missing: $Path"
    }
    Copy-Item -LiteralPath $Path -Destination (Join-Path $StagingDir (Split-Path $Path -Leaf)) -Force
}

function Copy-LatestManualEvidence {
    param(
        [string]$Subdirectory,
        [string]$Pattern,
        [string]$DestinationName
    )

    $EvidenceDirectory = Join-Path $PSScriptRoot "manual-evidence\$Subdirectory"
    if (-not (Test-Path -LiteralPath $EvidenceDirectory)) {
        Write-Warning "Manual evidence directory not found, skipping optional release evidence packet: $EvidenceDirectory"
        return
    }

    $EvidenceFiles = @(
        Get-ChildItem -LiteralPath $EvidenceDirectory -Filter $Pattern -File |
            Sort-Object LastWriteTime, Name
    )
    if (-not $EvidenceFiles) {
        Write-Warning "Manual evidence packet not found, skipping optional release evidence packet: $Pattern"
        return
    }

    $LatestEvidence = $EvidenceFiles[-1]
    Copy-Item -LiteralPath $LatestEvidence.FullName -Destination (Join-Path $StagingDir $DestinationName) -Force
}

Copy-LatestManualEvidence -Subdirectory "clean-vm" -Pattern "clean-vm-$AppVersion-*.md" -DestinationName "CLEAN_VM_AUTOMATED_EVIDENCE.md"
Copy-LatestManualEvidence -Subdirectory "obs-virtualcam" -Pattern "obs-virtualcam-*.md" -DestinationName "OBS_VIRTUAL_CAMERA_AUTOMATED_EVIDENCE.md"
Copy-LatestManualEvidence -Subdirectory "legal-review" -Pattern "legal-review-$AppVersion-*.md" -DestinationName "LEGAL_REVIEW_EVIDENCE_PACKET.md"

$ManualGateSummary = Join-Path $StagingDir "MANUAL_RELEASE_GATES.md"
& $CheckPython tools\summarize_manual_release_gates.py --repo-root $RepoRoot --output $ManualGateSummary
if ($LASTEXITCODE -ne 0) {
    throw "Manual release gate summary generation failed with exit code $LASTEXITCODE."
}

$InstallerDigest = (Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash
$SourceDigest = (Get-FileHash -LiteralPath $SourceArchive.FullName -Algorithm SHA256).Hash
$SourceManifestText = Get-Content -LiteralPath $SourceManifest -Raw
$ResolvedRef = "UNKNOWN"
if ($SourceManifestText -match "Git ref resolved:\s*``([^``]+)``") {
    $ResolvedRef = $Matches[1]
}
$SourceMode = "UNKNOWN"
if ($SourceManifestText -match "Archive mode:\s*``([^``]+)``") {
    $SourceMode = $Matches[1]
}

$ReleaseNotesTemplate = Join-Path $StagingDir "RELEASE_NOTES_TEMPLATE.md"
$ReleaseNotes = Join-Path $StagingDir "RELEASE_NOTES.md"
$ReleaseNotesText = Get-Content -LiteralPath $ReleaseNotesTemplate -Raw
$ReleaseNotesText = $ReleaseNotesText.Replace(
    "Installer SHA-256: listed in the uploaded ``RELEASE_ASSETS.md`` and ``DeepLiveCamStudio-$AppVersion-x64-setup.exe.sha256``",
    "Installer SHA-256: ``$InstallerDigest``"
)
$ReleaseNotesText = $ReleaseNotesText.Replace(
    "Corresponding source archive: listed in the uploaded ``RELEASE_ASSETS.md``",
    "Corresponding source archive: ``$($SourceArchive.Name)``"
)
$ReleaseNotesText = $ReleaseNotesText.Replace(
    "Source archive SHA-256: listed in the uploaded ``RELEASE_ASSETS.md`` and source ``.zip.sha256`` sidecar",
    "Source archive SHA-256: ``$SourceDigest``"
)
$ReleaseNotesText = $ReleaseNotesText.Replace(
    "Source ref: listed in the uploaded ``RELEASE_ASSETS.md`` and source ``.manifest.md``",
    "Source ref: ``$ResolvedRef``"
)
$ReleaseNotesText = $ReleaseNotesText.Replace(
    "powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion $AppVersion -GitRef HEAD",
    "powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion $AppVersion -GitRef $ResolvedRef"
)
if ($PortableArchive) {
    $ReleaseNotesText = $ReleaseNotesText.Replace("{{DIRECTML_PORTABLE_NAME}}", "``$(Split-Path $PortableArchive -Leaf)``")
    $ReleaseNotesText = $ReleaseNotesText.Replace("{{DIRECTML_PORTABLE_SHA256}}", "``$PortableDigest``")
} else {
    $ReleaseNotesText = $ReleaseNotesText.Replace("{{DIRECTML_PORTABLE_NAME}}", "not included in this CUDA-only candidate")
    $ReleaseNotesText = $ReleaseNotesText.Replace("{{DIRECTML_PORTABLE_SHA256}}", "not available")
}
$ReleaseNotesText | Set-Content -LiteralPath $ReleaseNotes -Encoding utf8

$AssetManifest = Join-Path $StagingDir "RELEASE_ASSETS.md"
$UploadNames = @(
    Get-ChildItem -LiteralPath $StagingDir -File |
        Where-Object { $_.Name -ne "RELEASE_ASSETS.md" } |
        Sort-Object Name |
        ForEach-Object { "- ``$($_.Name)``" }
)
$UploadNames += "- ``SHA256SUMS.txt``"
$UploadNames += "- ``RELEASE_ASSETS.md``"
$Lines = @(
    "# Windows GitHub Release Assets",
    "",
    "Generated: $((Get-Date).ToUniversalTime().ToString("o"))",
    "App version: ``$AppVersion``",
    "Source ref: ``$ResolvedRef``",
    "Source archive mode: ``$SourceMode``",
    "",
    "## Upload These Files",
    "",
    $UploadNames,
    "",
    "## Hashes",
    "",
    "- Installer SHA-256: ``$InstallerDigest``",
    "- Source SHA-256: ``$SourceDigest``",
    $(if ($PortableArchive) { "- DirectML portable SHA-256: ``$PortableDigest``" }),
    "",
    "## Notes",
    "",
    "- Do not upload model/checkpoint files unless separate redistribution approval exists.",
    "- Use ``RELEASE_NOTES.md`` for the GitHub Release body; it is generated from the template with the exact installer, source archive, source ref, and hashes.",
    "- Attach or link the exact corresponding source archive listed above for AGPL-3.0 compliance.",
    "- Manual gate and publish-readiness status is recorded in ``MANUAL_RELEASE_GATES.md`` and ``RELEASE_VERIFICATION.md``.",
    ""
)
$Lines | Set-Content -LiteralPath $AssetManifest -Encoding utf8

$Sha256Sums = Join-Path $StagingDir "SHA256SUMS.txt"
$ShaLines = @(
    Get-ChildItem -LiteralPath $StagingDir -File |
        Where-Object { $_.Name -ne "SHA256SUMS.txt" } |
        Sort-Object Name |
        ForEach-Object {
            $Digest = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            "$Digest  $($_.Name)"
        }
)
$ShaLines | Set-Content -LiteralPath $Sha256Sums -Encoding ascii

if (Test-Path -LiteralPath $OutputDir) {
    Move-Item -LiteralPath $OutputDir -Destination $BackupDir
}
Move-Item -LiteralPath $StagingDir -Destination $OutputDir
if (Test-Path -LiteralPath $BackupDir) {
    try {
        Remove-Item -LiteralPath $BackupDir -Recurse -Force
    } catch {
        Write-Warning "Could not remove previous release asset folder: $BackupDir. It is no longer the active output folder."
    }
}

Write-Host "Release assets assembled at: $OutputDir"
Write-Host "Release asset manifest: $(Join-Path $OutputDir "RELEASE_ASSETS.md")"
Write-Host "Installer SHA-256: $InstallerDigest"
Write-Host "Source archive: $($SourceArchive.FullName)"
Write-Host "Source SHA-256: $SourceDigest"
