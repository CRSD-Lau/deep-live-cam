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
$CudaRuntimeVenv = Join-Path $RepoRoot ".venv-build-windows-cuda-runtime"
$Venv = if ($UseExistingVenv) { $ExistingVenv } else { $BuildVenv }
$PythonExe = Join-Path $Venv "Scripts\python.exe"
$CudaRuntimePython = Join-Path $CudaRuntimeVenv "Scripts\python.exe"
$CudaRuntimeSitePackages = Join-Path $CudaRuntimeVenv "Lib\site-packages"
$CudaRuntimeTorchLib = Join-Path $CudaRuntimeSitePackages "torch\lib"
$BundleName = if ($IsDirectML) { "DeepLiveCamStudio-DirectML" } else { "DeepLiveCamStudio" }
$DistDir = Join-Path $RepoRoot "dist\$BundleName"
$RequirementsFile = if ($IsDirectML) {
    "requirements-locks\windows-directml-py311.lock"
} else {
    "requirements-locks\windows-cuda-py311.lock"
}
$CudaRuntimeRequirementsFile = "requirements-locks\windows-cuda-runtime-py311.lock"
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

if ($UseExistingVenv -and -not (Test-Path -LiteralPath $PythonExe)) {
    throw "-UseExistingVenv was requested, but the expected environment does not exist: $PythonExe"
}

if (-not (Test-Path $PythonExe)) {
    Invoke-Checked $Python @("-m", "venv", $Venv)
}

$BuildPythonVersion = & $PythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0 -or $BuildPythonVersion.Trim() -ne "3.11.9") {
    throw "Windows release locks require CPython 3.11.9; found $BuildPythonVersion at $PythonExe"
}

if (-not $SkipDependencyInstall) {
    Invoke-Checked $PythonExe @("-m", "pip", "install", "--require-hashes", "-r", $RequirementsFile)
    if (-not $IsDirectML) {
        # The packaged application excludes Torch Python modules. Its isolated
        # wheel is only the reviewed source for CUDA 12/cuDNN 9 DLLs copied by
        # the PyInstaller spec.
        if (-not (Test-Path -LiteralPath $CudaRuntimePython)) {
            Invoke-Checked $Python @("-m", "venv", $CudaRuntimeVenv)
        }
        $CudaRuntimePythonVersion = & $CudaRuntimePython -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
        if ($LASTEXITCODE -ne 0 -or $CudaRuntimePythonVersion.Trim() -ne "3.11.9") {
            throw "The CUDA runtime wheel lock requires CPython 3.11.9; found $CudaRuntimePythonVersion at $CudaRuntimePython"
        }
        Invoke-Checked $CudaRuntimePython @(
            "-m", "pip", "install", "--require-hashes", "--no-cache-dir", "--no-deps",
            "-r", $CudaRuntimeRequirementsFile
        )
    }
}

$EffectiveCudaRuntimeTorchLib = $CudaRuntimeTorchLib
$EffectiveCudaRuntimeSitePackages = $CudaRuntimeSitePackages
if (-not $IsDirectML -and -not (Test-Path -LiteralPath $EffectiveCudaRuntimeTorchLib)) {
    $ExistingRuntimeSitePackages = Join-Path $Venv "Lib\site-packages"
    $ExistingRuntimeTorchLib = Join-Path $ExistingRuntimeSitePackages "torch\lib"
    if (-not $SkipDependencyInstall -or -not (Test-Path -LiteralPath $ExistingRuntimeTorchLib)) {
        throw "CUDA runtime DLL source is missing: $EffectiveCudaRuntimeTorchLib"
    }
    $EffectiveCudaRuntimeTorchLib = $ExistingRuntimeTorchLib
    $EffectiveCudaRuntimeSitePackages = $ExistingRuntimeSitePackages
}

Invoke-Checked $PythonExe @("tools\generate_windows_logo_assets.py", "--source", "Logo.png", "--output-dir", "build\windows\assets")
$PreviousBuildAccelerator = $env:DLC_BUILD_ACCELERATOR
$PreviousBundleName = $env:DLC_BUNDLE_NAME
$PreviousCudaRuntimeTorchLib = $env:DLC_CUDA_RUNTIME_TORCH_LIB
try {
    $env:DLC_BUILD_ACCELERATOR = $Accelerator.ToLowerInvariant()
    $env:DLC_BUNDLE_NAME = $BundleName
    if (-not $IsDirectML) {
        $env:DLC_CUDA_RUNTIME_TORCH_LIB = $EffectiveCudaRuntimeTorchLib
    }
    Invoke-Checked $PythonExe @("-m", "PyInstaller", "--noconfirm", "--clean", $Spec, "--distpath", (Join-Path $RepoRoot "dist"), "--workpath", $PyInstallerWork)
}
finally {
    $env:DLC_BUILD_ACCELERATOR = $PreviousBuildAccelerator
    $env:DLC_BUNDLE_NAME = $PreviousBundleName
    $env:DLC_CUDA_RUNTIME_TORCH_LIB = $PreviousCudaRuntimeTorchLib
}

Invoke-Checked $PythonExe @("tools\prune_windows_dist.py", "--dist", $DistDir)

$OnnxRuntimePackage = if ($IsDirectML) { "onnxruntime-directml" } else { "onnxruntime-gpu" }
$DependencyLicenseSnapshot = if ($IsDirectML) {
    "LICENSES\PYTHON_DEPENDENCIES_DIRECTML.md"
} else {
    "LICENSES\PYTHON_DEPENDENCIES.md"
}
$PreviousPythonPath = $env:PYTHONPATH
try {
    if (-not $IsDirectML) {
        $env:PYTHONPATH = if ($PreviousPythonPath) {
            "$EffectiveCudaRuntimeSitePackages;$PreviousPythonPath"
        } else {
            $EffectiveCudaRuntimeSitePackages
        }
    }
    Invoke-Checked $PythonExe @("tools\collect_third_party_license_files.py", "--output", "LICENSES\THIRD_PARTY_LICENSES", "--onnxruntime-package", $OnnxRuntimePackage)
    Invoke-Checked $PythonExe @("tools\generate_python_dependency_licenses.py", "--output", $DependencyLicenseSnapshot)
}
finally {
    $env:PYTHONPATH = $PreviousPythonPath
}

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
