param(
    [string]$AppVersion = "2.1.8",
    [string]$InstallerPath = "",
    [string]$SourceArchivePath = "",
    [string]$EvidenceDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $InstallerPath) {
    $InstallerPath = Join-Path $PSScriptRoot "installer\DeepLiveCamStudio-$AppVersion-x64-setup.exe"
}
if (-not $EvidenceDir) {
    $EvidenceDir = Join-Path $PSScriptRoot "manual-evidence\legal-review"
}
if (-not (Test-Path $InstallerPath)) {
    throw "Installer not found: $InstallerPath"
}
if (-not $SourceArchivePath) {
    $ReleaseAssetsManifest = Join-Path $PSScriptRoot "release-assets\$AppVersion\RELEASE_ASSETS.md"
    if (Test-Path $ReleaseAssetsManifest) {
        $ReleaseAssetsText = Get-Content -LiteralPath $ReleaseAssetsManifest -Raw
        $ReleaseAssetMatch = [regex]::Match($ReleaseAssetsText, "DeepLiveCamStudio-$([regex]::Escape($AppVersion))-source-[^``\s]+\.zip")
        if ($ReleaseAssetMatch.Success) {
            $ReleaseAssetSourcePath = Join-Path $PSScriptRoot "release-assets\$AppVersion\$($ReleaseAssetMatch.Value)"
            if (Test-Path $ReleaseAssetSourcePath) {
                $SourceArchivePath = $ReleaseAssetSourcePath
            }
        }
    }
}
if (-not $SourceArchivePath) {
    $SourceArchives = @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot "installer") -Filter "DeepLiveCamStudio-$AppVersion-source-*.zip" -File | Where-Object {
        $CandidateManifest = [System.IO.Path]::ChangeExtension($_.FullName, ".manifest.md")
        (Test-Path $CandidateManifest) -and ((Get-Content -LiteralPath $CandidateManifest -Raw) -match 'Archive mode: `git-ref`')
    } | Sort-Object LastWriteTime)
    if ($SourceArchives) {
        $SourceArchivePath = $SourceArchives[-1].FullName
    }
}
if (-not $SourceArchivePath -or -not (Test-Path $SourceArchivePath)) {
    throw "Corresponding source archive not found. Run build\windows\package_source.ps1 -AppVersion $AppVersion -GitRef <release-tag-or-commit> before legal review."
}

$SourceHashPath = "$SourceArchivePath.sha256"
$SourceManifestPath = [System.IO.Path]::ChangeExtension($SourceArchivePath, ".manifest.md")
if (-not (Test-Path $SourceHashPath)) {
    throw "Corresponding source hash sidecar not found: $SourceHashPath"
}
if (-not (Test-Path $SourceManifestPath)) {
    throw "Corresponding source manifest not found: $SourceManifestPath"
}

New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$SummaryPath = Join-Path $EvidenceDir "legal-review-$AppVersion-$Timestamp.md"

Set-Location $RepoRoot

$RequiredDocs = @(
    "LICENSE",
    "COMPLIANCE.md",
    "THIRD_PARTY_NOTICES.md",
    "LICENSES/BUNDLED_BINARY_OBLIGATIONS.md",
    "LICENSES/MODEL_LICENSE_AUDIT.md",
    "LICENSES/PYTHON_DEPENDENCIES.md",
    "LICENSES/WINDOWS_BUNDLE_MANIFEST.md",
    "RELEASE_REPORT.md",
    "RELEASE_CHECKLIST.md",
    "RELEASE_PUBLISH_HANDOFF.md",
    "RELEASE_VERIFICATION.md",
    "RELEASE_CUTOVER_STATUS.md",
    "RELEASE_NOTES_TEMPLATE.md"
)

$MissingDocs = @()
foreach ($Doc in $RequiredDocs) {
    if (-not (Test-Path (Join-Path $RepoRoot $Doc))) {
        $MissingDocs += $Doc
    }
}
if ($MissingDocs) {
    $MissingDocs | ForEach-Object { Write-Host "Missing legal review artifact: $_" }
    throw "Legal review evidence is incomplete."
}

$InstallerHash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash
$SourceHash = (Get-FileHash -LiteralPath $SourceArchivePath -Algorithm SHA256).Hash
$SourceSidecarHash = (Get-Content -LiteralPath $SourceHashPath -Raw).Trim().Split()[0].ToUpperInvariant()
if ($SourceSidecarHash -ne $SourceHash) {
    throw "Corresponding source hash sidecar mismatch: $SourceHashPath"
}

$SourceManifest = Get-Content -LiteralPath $SourceManifestPath -Raw
if ($SourceManifest -notmatch 'Archive mode: `git-ref`') {
    throw "Corresponding source manifest is not git-ref mode: $SourceManifestPath"
}
if ($SourceManifest -notmatch 'No `\.onnx`, `\.pth`, `\.safetensors`') {
    throw "Corresponding source manifest does not record forbidden model/checkpoint scan: $SourceManifestPath"
}

$BundleManifest = Get-Content -LiteralPath (Join-Path $RepoRoot "LICENSES/WINDOWS_BUNDLE_MANIFEST.md") -Raw
$PythonLicenses = Get-Content -LiteralPath (Join-Path $RepoRoot "LICENSES/PYTHON_DEPENDENCIES.md") -Raw
$ModelAudit = Get-Content -LiteralPath (Join-Path $RepoRoot "LICENSES/MODEL_LICENSE_AUDIT.md") -Raw
$Obligations = Get-Content -LiteralPath (Join-Path $RepoRoot "LICENSES/BUNDLED_BINARY_OBLIGATIONS.md") -Raw
$Verification = Get-Content -LiteralPath (Join-Path $RepoRoot "RELEASE_VERIFICATION.md") -Raw

$UnknownLicenseLines = @($PythonLicenses -split "`r?`n" | Where-Object { $_ -match "UNKNOWN|Unknown|LicenseRef|GPL|LGPL" } | Select-Object -First 80)
$ModelRiskLines = @($ModelAudit -split "`r?`n" | Where-Object { $_ -match "Exclude|non-commercial|GPL|redistribution|provenance|risk" } | Select-Object -First 80)
$ObligationLines = @($Obligations -split "`r?`n" | Where-Object { $_ -match "PySide6|shiboken6|pyvirtualcam|cv2_enumerate_cameras|LGPL|GPL|Inno|ffmpeg" } | Select-Object -First 80)
$ForbiddenModelStatus = if ($BundleManifest -match "Forbidden model/checkpoint files found:\s*0") { "PASS" } else { "REVIEW-REQUIRED" }
$PublishReadyStatus = if ($Verification -match "Ready to publish without remaining manual gates:\s+\*\*YES\*\*") { "YES" } else { "NO" }
$SourceArchiveModeStatus = if ($SourceManifest -match 'Archive mode: `git-ref`') { "git-ref" } else { "review-required" }
$SourceForbiddenScanStatus = if ($SourceManifest -match 'No `\.onnx`, `\.pth`, `\.safetensors`') { "PASS" } else { "REVIEW-REQUIRED" }

$SummaryTimestamp = (Get-Date).ToUniversalTime().ToString("o")

$Lines = @(
    "# Legal Review Evidence Packet",
    "",
    "Status: REVIEW-REQUIRED",
    "",
    "This packet is generated by ``build/windows/verify_legal_review_gate.ps1``.",
    "It is not legal advice and does not approve the release. It collects the",
    "engineering evidence an authorized reviewer needs before changing",
    "``LEGAL_REVIEW.md`` to ``Status: PASS``.",
    "",
    "## Artifacts",
    "",
    "- Timestamp UTC: ``$SummaryTimestamp``",
    "- Installer: ``$InstallerPath``",
    "- Installer SHA-256: ``$InstallerHash``",
    "- Source archive: ``$SourceArchivePath``",
    "- Source archive SHA-256: ``$SourceHash``",
    "- Source archive mode: ``$SourceArchiveModeStatus``",
    "- Source forbidden model/checkpoint scan: ``$SourceForbiddenScanStatus``",
    "- Source manifest: ``$SourceManifestPath``",
    "- Publish-ready according to ``RELEASE_VERIFICATION.md``: ``$PublishReadyStatus``",
    "- Forbidden model/checkpoint scan: ``$ForbiddenModelStatus``",
    "",
    "## Required Review Documents Present",
    ""
)
foreach ($Doc in $RequiredDocs) {
    $Lines += "- [x] ``$Doc``"
}

$Lines += @(
    "",
    "## High-Attention Dependency Metadata Lines",
    ""
)
if ($UnknownLicenseLines) {
    foreach ($Line in $UnknownLicenseLines) {
        $Lines += "- $Line"
    }
} else {
    $Lines += "- No matching high-attention dependency metadata lines found by this helper."
}

$Lines += @(
    "",
    "## Model Redistribution Review Lines",
    ""
)
foreach ($Line in $ModelRiskLines) {
    $Lines += "- $Line"
}

$Lines += @(
    "",
    "## Bundled Binary Obligation Lines",
    ""
)
foreach ($Line in $ObligationLines) {
    $Lines += "- $Line"
}

$Lines += @(
    "",
    "## Reviewer Decisions Still Required",
    "",
    "- Confirm AGPL-3.0 corresponding-source handling for the exact binary release.",
    "- Confirm model downloader URLs/license notes/checksums are acceptable for the intended distribution context.",
    "- Confirm PySide6/shiboken6 LGPL/GPL/commercial-license posture.",
    "- Confirm pyvirtualcam GPLv2 metadata and cv2_enumerate_cameras GPL-3.0 metadata are acceptable in the binary distribution.",
    "- Confirm Inno Setup commercial-use position for the publisher.",
    "- Confirm any UNKNOWN or unusual dependency metadata in ``LICENSES/PYTHON_DEPENDENCIES.md``.",
    "- Confirm ffmpeg remains unbundled or has separate redistribution approval.",
    "",
    "After review, summarize conclusions in ``LEGAL_REVIEW.md`` and check off every",
    "required item before changing that file to ``Status: PASS``."
)

$Lines | Set-Content -LiteralPath $SummaryPath -Encoding utf8
Write-Host "Legal review evidence packet written to: $SummaryPath"
