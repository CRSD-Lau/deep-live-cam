param(
    [string]$DistDir = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $DistDir) {
    $DistDir = Join-Path $RepoRoot "dist\DeepLiveCamStudio"
}

if (-not (Test-Path $DistDir)) {
    throw "Packaged dist directory not found: $DistDir"
}

$Cli = Join-Path $DistDir "DeepLiveCamStudioCLI.exe"
$Gui = Join-Path $DistDir "DeepLiveCamStudio.exe"
if (-not (Test-Path $Cli)) {
    throw "Missing packaged CLI executable: $Cli"
}
if (-not (Test-Path $Gui)) {
    throw "Missing packaged GUI executable: $Gui"
}

$RequiredFiles = @(
    "README.md",
    "LICENSE",
    "Logo.png",
    "THIRD_PARTY_NOTICES.md",
    "COMPLIANCE.md",
    "RELEASE_CHECKLIST.md",
    "RELEASE_PUBLISH_HANDOFF.md",
    "RELEASE_REPORT.md",
    "RELEASE_SOURCE_PREP.md",
    "MODEL_DOWNLOAD_VERIFICATION.md",
    "PROCESSING_VERIFICATION.md",
    "docs\OBS_VIRTUAL_CAMERA.md",
    "LICENSES\BUNDLED_BINARY_OBLIGATIONS.md",
    "LICENSES\MODEL_LICENSE_AUDIT.md",
    "LICENSES\PYTHON_DEPENDENCIES.md",
    "LICENSES\THIRD_PARTY_LICENSES\README.md",
    "LICENSES\THIRD_PARTY_LICENSES\tensorflow-2.19.1\package\THIRD_PARTY_NOTICES.txt",
    "LICENSES\THIRD_PARTY_LICENSES\onnxruntime-gpu-1.23.2\package\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\opencv-python-4.10.0.84\package\LICENSE-3RD-PARTY.txt",
    "LICENSES\THIRD_PARTY_LICENSES\onnx-1.21.0\licenses\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\opennsfw2-0.10.2\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\PySide6-6.11.1\METADATA",
    "LICENSES\THIRD_PARTY_LICENSES\PySide6-6.11.1\licenses\LicenseRef-Qt-Commercial.txt",
    "LICENSES\THIRD_PARTY_LICENSES\shiboken6-6.11.1\METADATA",
    "LICENSES\THIRD_PARTY_LICENSES\pyvirtualcam-0.15.0\licenses\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\cv2_enumerate_cameras-1.1.15\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\easydict-1.13\LICENSE",
    "LICENSES\WINDOWS_BUNDLE_MANIFEST.md"
)

foreach ($RelativePath in $RequiredFiles) {
    $Path = Join-Path $DistDir $RelativePath
    if (-not (Test-Path $Path)) {
        throw "Packaged dist missing required release file: $RelativePath"
    }
}

$Forbidden = Get-ChildItem $DistDir -Recurse -File -Include *.onnx,*.pth,*.safetensors -ErrorAction SilentlyContinue
if ($Forbidden) {
    $Forbidden | Select-Object FullName, Length | Format-Table
    throw "Packaged dist contains model/checkpoint files."
}

if (Test-Path (Join-Path $DistDir "_internal\torch")) {
    throw "Packaged dist unexpectedly contains _internal\torch."
}

$DevOnlyPayloadPaths = @(
    "_internal\matplotlib\mpl-data\sample_data",
    "_internal\sklearn\datasets\data",
    "_internal\sklearn\datasets\images",
    "_internal\sklearn\datasets\tests"
)
foreach ($RelativePath in $DevOnlyPayloadPaths) {
    $Path = Join-Path $DistDir $RelativePath
    if (Test-Path $Path) {
        throw "Packaged dist unexpectedly contains dev-only payload path: $RelativePath"
    }
}

$DuplicatedReleaseDocs = @(
    "_internal\README.md",
    "_internal\LICENSE",
    "_internal\THIRD_PARTY_NOTICES.md",
    "_internal\COMPLIANCE.md",
    "_internal\RELEASE_CHECKLIST.md",
    "_internal\RELEASE_PUBLISH_HANDOFF.md",
    "_internal\RELEASE_REPORT.md",
    "_internal\RELEASE_SOURCE_PREP.md",
    "_internal\MODEL_DOWNLOAD_VERIFICATION.md",
    "_internal\PROCESSING_VERIFICATION.md",
    "_internal\LICENSES",
    "_internal\docs\OBS_VIRTUAL_CAMERA.md"
)

foreach ($RelativePath in $DuplicatedReleaseDocs) {
    if (Test-Path (Join-Path $DistDir $RelativePath)) {
        throw "Packaged dist contains duplicated release document under PyInstaller _internal: $RelativePath"
    }
}

$Manifest = Join-Path $DistDir "LICENSES\WINDOWS_BUNDLE_MANIFEST.md"
$ManifestText = Get-Content -LiteralPath $Manifest -Raw
if ($ManifestText -notmatch "Forbidden model/checkpoint files found: 0") {
    throw "Windows bundle manifest does not record a clean forbidden model/checkpoint scan."
}

$RequiredCodecFiles = @(
    "_internal\PIL\_webp.cp311-win_amd64.pyd",
    "_internal\PIL\_avif.cp311-win_amd64.pyd"
)

foreach ($RelativePath in $RequiredCodecFiles) {
    $Path = Join-Path $DistDir $RelativePath
    if (-not (Test-Path $Path)) {
        throw "Packaged dist missing image codec file: $RelativePath"
    }
}

& $Cli --version
if ($LASTEXITCODE -ne 0) {
    throw "Packaged CLI --version failed with exit code $LASTEXITCODE."
}

$SmokeAppData = Join-Path $env:TEMP ("DeepLiveCamStudio-runtime-preflight-" + [guid]::NewGuid().ToString("N"))
$previousAppData = $env:DLC_APP_DATA_DIR
try {
    $env:DLC_APP_DATA_DIR = $SmokeAppData
    & $Cli --download-models
    $downloadExit = $LASTEXITCODE
}
finally {
    $env:DLC_APP_DATA_DIR = $previousAppData
    if (Test-Path $SmokeAppData) {
        Remove-Item -LiteralPath $SmokeAppData -Recurse -Force
    }
}

if ($downloadExit -ne 2) {
    throw "Packaged CLI --download-models was expected to cancel with exit code 2 without consent, got $downloadExit."
}

Write-Host "Packaged runtime preflight passed."
