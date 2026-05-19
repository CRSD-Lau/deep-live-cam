param(
    [string]$Python = "python",
    [switch]$UseExistingVenv,
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ExistingVenv = Join-Path $RepoRoot "venv"
$Venv = if (($UseExistingVenv -or (Test-Path (Join-Path $ExistingVenv "Scripts\python.exe"))) -and (Test-Path (Join-Path $ExistingVenv "Scripts\python.exe"))) { $ExistingVenv } else { Join-Path $RepoRoot ".venv-build-windows" }
$PythonExe = Join-Path $Venv "Scripts\python.exe"
$DistDir = Join-Path $RepoRoot "dist\DeepLiveCamStudio"
$Spec = Join-Path $PSScriptRoot "deep_live_cam_studio.spec"

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

Set-Location $RepoRoot

if (-not (Test-Path $PythonExe)) {
    Invoke-Checked $Python @("-m", "venv", $Venv)
}

Invoke-Checked $PythonExe @("-m", "pip", "install", "--upgrade", "pip", "wheel")
if (-not $SkipDependencyInstall) {
    Invoke-Checked $PythonExe @("-m", "pip", "install", "-r", "requirements.txt")
}
Invoke-Checked $PythonExe @("-m", "pip", "install", "pyinstaller>=6.10,<7", "pyinstaller-hooks-contrib>=2024.8")

Invoke-Checked $PythonExe @("tools\generate_windows_logo_assets.py", "--source", "Logo.png", "--output-dir", "build\windows\assets")
Invoke-Checked $PythonExe @("-m", "PyInstaller", "--noconfirm", "--clean", $Spec, "--distpath", (Join-Path $RepoRoot "dist"), "--workpath", (Join-Path $RepoRoot "build\windows\pyinstaller-work"))
Invoke-Checked $PythonExe @("tools\prune_windows_dist.py", "--dist", $DistDir)

Invoke-Checked $PythonExe @("tools\collect_third_party_license_files.py", "--output", "LICENSES\THIRD_PARTY_LICENSES")

$RequiredDocs = @("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "COMPLIANCE.md", "RELEASE_CHECKLIST.md", "RELEASE_REPORT.md", "RELEASE_SOURCE_PREP.md", "MODEL_DOWNLOAD_VERIFICATION.md", "PROCESSING_VERIFICATION.md", "docs\OBS_VIRTUAL_CAMERA.md")
foreach ($Doc in $RequiredDocs) {
    $Source = Join-Path $RepoRoot $Doc
    if (-not (Test-Path $Source)) {
        throw "Required release document missing from repository root: $Source"
    }
    $Destination = Join-Path $DistDir $Doc
    New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

Copy-Item -LiteralPath (Join-Path $RepoRoot "Logo.png") -Destination (Join-Path $DistDir "Logo.png") -Force

$Licenses = Join-Path $RepoRoot "LICENSES"
if (Test-Path $Licenses) {
    Copy-Item -LiteralPath $Licenses -Destination (Join-Path $DistDir "LICENSES") -Recurse -Force
}

Invoke-Checked $PythonExe @("tools\generate_windows_bundle_manifest.py", "--dist", $DistDir, "--output", "LICENSES\WINDOWS_BUNDLE_MANIFEST.md")
New-Item -ItemType Directory -Path (Join-Path $DistDir "LICENSES") -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $RepoRoot "LICENSES\WINDOWS_BUNDLE_MANIFEST.md") -Destination (Join-Path $DistDir "LICENSES\WINDOWS_BUNDLE_MANIFEST.md") -Force

Write-Host "Executable bundle created at: $DistDir"
Write-Host "Run model setup with: $DistDir\DeepLiveCamStudioCLI.exe --download-models"
