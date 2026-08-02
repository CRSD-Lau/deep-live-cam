param(
    [string]$Python = "python",
    [switch]$UseExistingVenv,
    [switch]$SkipDependencyInstall,
    [ValidateSet("Cuda", "DirectML")]
    [string]$Accelerator = "Cuda"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$IsDirectML = $Accelerator -eq "DirectML"
$ExistingVenv = Join-Path $RepoRoot $(if ($IsDirectML) { ".venv-directml" } else { "venv" })
$BuildVenv = Join-Path $RepoRoot $(if ($IsDirectML) { ".venv-build-windows-directml" } else { ".venv-build-windows" })
$Venv = if (($UseExistingVenv -or (Test-Path (Join-Path $ExistingVenv "Scripts\python.exe"))) -and (Test-Path (Join-Path $ExistingVenv "Scripts\python.exe"))) { $ExistingVenv } else { $BuildVenv }
$PythonExe = Join-Path $Venv "Scripts\python.exe"
$BundleName = if ($IsDirectML) { "DeepLiveCamStudio-DirectML" } else { "DeepLiveCamStudio" }
$DistDir = Join-Path $RepoRoot "dist\$BundleName"
$RequirementsFile = if ($IsDirectML) { "requirements-directml.txt" } else { "requirements.txt" }
$CudaRuntimeRequirementsFile = "requirements-build-windows-cuda.txt"
$PyInstallerWork = Join-Path $RepoRoot $(if ($IsDirectML) { "build\windows\pyinstaller-work-directml" } else { "build\windows\pyinstaller-work" })
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
    Invoke-Checked $PythonExe @("-m", "pip", "install", "-r", $RequirementsFile)
    if (-not $IsDirectML) {
        # The application does not import torch, but its CUDA wheel is the
        # reviewed source for the CUDA 12/cuDNN 9 redistributable DLLs copied
        # by the PyInstaller spec.
        Invoke-Checked $PythonExe @(
            "-m", "pip", "install", "--no-cache-dir", "--no-deps",
            "-r", $CudaRuntimeRequirementsFile
        )
    }
}
Invoke-Checked $PythonExe @("-m", "pip", "install", "pyinstaller>=6.10,<7", "pyinstaller-hooks-contrib>=2024.8")

Invoke-Checked $PythonExe @("tools\generate_windows_logo_assets.py", "--source", "Logo.png", "--output-dir", "build\windows\assets")
$PreviousBuildAccelerator = $env:DLC_BUILD_ACCELERATOR
$PreviousBundleName = $env:DLC_BUNDLE_NAME
try {
    $env:DLC_BUILD_ACCELERATOR = $Accelerator.ToLowerInvariant()
    $env:DLC_BUNDLE_NAME = $BundleName
    Invoke-Checked $PythonExe @("-m", "PyInstaller", "--noconfirm", "--clean", $Spec, "--distpath", (Join-Path $RepoRoot "dist"), "--workpath", $PyInstallerWork)
}
finally {
    $env:DLC_BUILD_ACCELERATOR = $PreviousBuildAccelerator
    $env:DLC_BUNDLE_NAME = $PreviousBundleName
}

# A clean release venv only needs torch long enough for PyInstaller to copy the
# selected runtime DLLs. Keep dist-info for licence generation, but release the
# four-gigabyte Python package before installer compression. Never modify an
# explicitly reused developer venv.
if (-not $IsDirectML -and $Venv -eq $BuildVenv) {
    $TorchPackageDir = Join-Path $Venv "Lib\site-packages\torch"
    if (Test-Path -LiteralPath $TorchPackageDir) {
        $ResolvedTorchPackageDir = (Resolve-Path -LiteralPath $TorchPackageDir).Path
        $ResolvedBuildVenv = (Resolve-Path -LiteralPath $BuildVenv).Path
        if (-not $ResolvedTorchPackageDir.StartsWith("$ResolvedBuildVenv\")) {
            throw "Refusing to remove torch package outside the isolated build venv: $ResolvedTorchPackageDir"
        }
        Remove-Item -LiteralPath $ResolvedTorchPackageDir -Recurse -Force
        Write-Host "Removed build-only torch package after CUDA runtime DLL collection."
    }
}
Invoke-Checked $PythonExe @("tools\prune_windows_dist.py", "--dist", $DistDir)

$OnnxRuntimePackage = if ($IsDirectML) { "onnxruntime-directml" } else { "onnxruntime-gpu" }
Invoke-Checked $PythonExe @("tools\collect_third_party_license_files.py", "--output", "LICENSES\THIRD_PARTY_LICENSES", "--onnxruntime-package", $OnnxRuntimePackage)

$RequiredDocs = @("README.md", "CHANGELOG.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "COMPLIANCE.md", "RELEASE_CHECKLIST.md", "RELEASE_PUBLISH_HANDOFF.md", "RELEASE_REPORT.md", "RELEASE_SOURCE_PREP.md", "MODEL_DOWNLOAD_VERIFICATION.md", "PROCESSING_VERIFICATION.md", "docs\OBS_VIRTUAL_CAMERA.md")
if ($IsDirectML) {
    $RequiredDocs += "docs\DIRECTML_TESTING.md"
}
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
Write-Host "Accelerator profile: $Accelerator"
Write-Host "Run model setup with: $DistDir\DeepLiveCamStudioCLI.exe --download-models"
