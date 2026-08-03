param(
    [string]$AppVersion = "2.2.1",
    [ValidateSet("Cuda", "DirectML")]
    [string]$Accelerator = "DirectML",
    [string]$DistDir = "",
    [string]$OutputDir = "",
    [switch]$SkipAcceleratorProbe
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$BundleName = if ($Accelerator -eq "DirectML") { "DeepLiveCamStudio-DirectML" } else { "DeepLiveCamStudio" }
$ProfileName = if ($Accelerator -eq "DirectML") { "DirectML" } else { "CUDA" }

if (-not $DistDir) {
    $DistDir = Join-Path $RepoRoot "dist\$BundleName"
}
if (-not $OutputDir) {
    $OutputDir = Join-Path $PSScriptRoot "portable"
}

$DistDir = [System.IO.Path]::GetFullPath($DistDir)
$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)

foreach ($RequiredFile in @("DeepLiveCamStudio.exe", "DeepLiveCamStudioCLI.exe", "README.md", "CHANGELOG.md", "LICENSE")) {
    $RequiredPath = Join-Path $DistDir $RequiredFile
    if (-not (Test-Path -LiteralPath $RequiredPath -PathType Leaf)) {
        throw "Portable bundle input is missing required file: $RequiredPath"
    }
}

$RuntimeTestArgs = @{
    DistDir = $DistDir
    Accelerator = $Accelerator
}
if (-not $SkipAcceleratorProbe) {
    $RuntimeTestArgs.RequireAccelerator = $true
}
& (Join-Path $PSScriptRoot "test_packaged_runtime.ps1") @RuntimeTestArgs
if ($LASTEXITCODE -ne 0) {
    throw "Packaged runtime validation failed with exit code $LASTEXITCODE."
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$ArchiveName = "DeepLiveCamStudio-$AppVersion-$ProfileName-x64-portable.zip"
$ArchivePath = Join-Path $OutputDir $ArchiveName
$HashPath = "$ArchivePath.sha256"

foreach ($StalePath in @($ArchivePath, $HashPath)) {
    if (Test-Path -LiteralPath $StalePath) {
        [System.IO.File]::Delete($StalePath)
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $DistDir,
    $ArchivePath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

$Archive = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
try {
    $EntryNames = @($Archive.Entries | ForEach-Object { $_.FullName.Replace("\", "/") })
    $RequiredEntries = @(
        "DeepLiveCamStudio.exe",
        "DeepLiveCamStudioCLI.exe",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "_internal/sklearn/.libs/vcomp140.dll"
    )
    foreach ($RequiredEntry in $RequiredEntries) {
        if ($EntryNames -notcontains $RequiredEntry) {
            throw "Portable archive is missing required entry: $RequiredEntry"
        }
    }

    $ForbiddenModelEntries = @(
        $EntryNames | Where-Object { $_ -match "(?i)(^|/)(models?|checkpoints?)/|\.(onnx|pth|safetensors)$" }
    )
    if ($ForbiddenModelEntries) {
        throw "Portable archive contains forbidden model/checkpoint entries: $($ForbiddenModelEntries -join ', ')"
    }
}
finally {
    $Archive.Dispose()
}

$Hash = Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256
"$($Hash.Hash)  $ArchiveName" | Set-Content -LiteralPath $HashPath -Encoding ascii

Write-Host "Portable $ProfileName archive created at: $ArchivePath"
Write-Host "SHA-256 written to: $HashPath"
Write-Host "SHA-256: $($Hash.Hash)"
