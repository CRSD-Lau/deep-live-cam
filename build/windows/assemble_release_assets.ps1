param(
    [string]$AppVersion = "2.1.5",
    [string]$InstallerDir = "",
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
    (Join-Path $RepoRoot "RELEASE_NOTES_TEMPLATE.md"),
    (Join-Path $RepoRoot "RELEASE_VERIFICATION.md"),
    (Join-Path $RepoRoot "RELEASE_CHECKLIST.md"),
    (Join-Path $RepoRoot "RELEASE_REPORT.md"),
    (Join-Path $RepoRoot "COMPLIANCE.md"),
    (Join-Path $RepoRoot "THIRD_PARTY_NOTICES.md")
)
foreach ($Path in $FilesToCopy) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required release asset input missing: $Path"
    }
    Copy-Item -LiteralPath $Path -Destination (Join-Path $StagingDir (Split-Path $Path -Leaf)) -Force
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

$AssetManifest = Join-Path $StagingDir "RELEASE_ASSETS.md"
$UploadNames = @(
    Get-ChildItem -LiteralPath $StagingDir -File |
        Where-Object { $_.Name -ne "RELEASE_ASSETS.md" } |
        Sort-Object Name |
        ForEach-Object { "- ``$($_.Name)``" }
)
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
    "",
    "## Notes",
    "",
    "- Do not upload model/checkpoint files unless separate redistribution approval exists.",
    "- Replace placeholders in ``RELEASE_NOTES_TEMPLATE.md`` before publishing.",
    "- Attach or link the exact corresponding source archive listed above for AGPL-3.0 compliance.",
    "- This asset set is not publish-approved until clean VM, OBS workflow, and legal review gates are complete.",
    ""
)
$Lines | Set-Content -LiteralPath $AssetManifest -Encoding utf8

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
