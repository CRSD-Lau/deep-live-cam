param(
    [string]$AppVersion = "2.1.5",
    [string]$InstallerPath = "",
    [string]$InstallDir = "",
    [switch]$KeepInstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $InstallerPath) {
    $InstallerPath = Join-Path $PSScriptRoot "installer\DeepLiveCamStudio-$AppVersion-x64-setup.exe"
}

if (-not (Test-Path $InstallerPath)) {
    throw "Installer not found: $InstallerPath"
}

if (-not $InstallDir) {
    $InstallDir = Join-Path $env:TEMP "DeepLiveCamStudio-installer-smoke-$AppVersion"
}

if (Test-Path $InstallDir) {
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
}

$InstallerFullPath = (Resolve-Path $InstallerPath).Path
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

Write-Host "Installing $InstallerFullPath to $InstallDir"
$installArgs = @(
    "/VERYSILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART",
    "/DIR=$InstallDir"
)
$process = Start-Process -FilePath $InstallerFullPath -ArgumentList $installArgs -Wait -PassThru
if ($process.ExitCode -ne 0) {
    throw "Installer exited with code $($process.ExitCode)."
}

$RequiredFiles = @(
    "DeepLiveCamStudio.exe",
    "DeepLiveCamStudioCLI.exe",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "COMPLIANCE.md",
    "RELEASE_CHECKLIST.md",
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
    "LICENSES\THIRD_PARTY_LICENSES\onnx-1.18.0\licenses\LICENSE",
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
    $Path = Join-Path $InstallDir $RelativePath
    if (-not (Test-Path $Path)) {
        throw "Installed payload missing required file: $RelativePath"
    }
}

$Forbidden = Get-ChildItem $InstallDir -Recurse -File -Include *.onnx,*.pth,*.safetensors -ErrorAction SilentlyContinue
if ($Forbidden) {
    $Forbidden | Select-Object FullName, Length | Format-Table
    throw "Installed payload contains model/checkpoint files."
}

if (Test-Path (Join-Path $InstallDir "_internal\torch")) {
    throw "Installed payload unexpectedly contains _internal\torch."
}

$DevOnlyPayloadPaths = @(
    "_internal\matplotlib\mpl-data\sample_data",
    "_internal\sklearn\datasets\data",
    "_internal\sklearn\datasets\images",
    "_internal\sklearn\datasets\tests"
)
foreach ($RelativePath in $DevOnlyPayloadPaths) {
    $Path = Join-Path $InstallDir $RelativePath
    if (Test-Path $Path) {
        throw "Installed payload unexpectedly contains dev-only payload path: $RelativePath"
    }
}

$Cli = Join-Path $InstallDir "DeepLiveCamStudioCLI.exe"
& $Cli --version
if ($LASTEXITCODE -ne 0) {
    throw "Installed CLI --version failed with exit code $LASTEXITCODE."
}

$ModelsDir = Join-Path $env:LOCALAPPDATA "DeepLiveCamStudio\models"
$SentinelPath = Join-Path $ModelsDir "installer-smoke-preserve-$AppVersion.txt"
New-Item -ItemType Directory -Path $ModelsDir -Force | Out-Null
"Created by build/windows/test_installer.ps1; safe to delete." | Set-Content -LiteralPath $SentinelPath -Encoding ascii

Write-Host "Installer smoke test passed."

if (-not $KeepInstall) {
    $Uninstaller = Join-Path $InstallDir "unins000.exe"
    if (Test-Path $Uninstaller) {
        Write-Host "Uninstalling smoke-test install."
        $uninstall = Start-Process -FilePath $Uninstaller -ArgumentList @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART") -PassThru
        if (-not $uninstall.WaitForExit(120000)) {
            Stop-Process -Id $uninstall.Id -Force -ErrorAction SilentlyContinue
            throw "Uninstaller did not exit within 120 seconds."
        }
        if ($uninstall.ExitCode -ne 0) {
            throw "Uninstaller exited with code $($uninstall.ExitCode)."
        }
    }
    if (-not (Test-Path $SentinelPath)) {
        throw "Uninstall removed user model data sentinel: $SentinelPath"
    }
    Remove-Item -LiteralPath $SentinelPath -Force
    if (Test-Path $InstallDir) {
        Remove-Item -LiteralPath $InstallDir -Recurse -Force
    }
}
