param(
    [string]$AppVersion = "2.2.1",
    [string]$Python = "python",
    [string]$GitRef = "HEAD",
    [string]$IsccPath = "",
    [switch]$UseExistingVenv,
    [switch]$SkipBuild,
    [switch]$SkipDependencyInstall,
    [switch]$SkipSourceArchive,
    [switch]$AllowDirtySource,
    [switch]$DraftWorkingTreeSource,
    [switch]$RequireFfmpeg,
    [switch]$RequireCuda,
    [switch]$RequireObsVirtualCam,
    [switch]$RequirePublishReady
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DistDir = Join-Path $RepoRoot "dist\DeepLiveCamStudio"
$Installer = Join-Path $PSScriptRoot "installer\DeepLiveCamStudio-$AppVersion-x64-setup.exe"
$InstallerHash = "$Installer.sha256"
$ReleaseAssetsDir = Join-Path $PSScriptRoot "release-assets\$AppVersion"
$ExpectGitRefSource = (-not $SkipSourceArchive) -and (-not $DraftWorkingTreeSource)

if ($RequirePublishReady) {
    if ($AllowDirtySource) {
        throw "-RequirePublishReady cannot be combined with -AllowDirtySource. Publish-ready releases must use a clean Git ref source archive."
    }
    if ($DraftWorkingTreeSource) {
        throw "-RequirePublishReady cannot be combined with -DraftWorkingTreeSource. Draft worktree archives are not publishable AGPL corresponding source."
    }
    if ($SkipSourceArchive) {
        throw "-RequirePublishReady cannot be combined with -SkipSourceArchive. Publish-ready releases must generate and validate corresponding source."
    }
}

function Invoke-ReleaseStep {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "Release step failed with exit code ${LASTEXITCODE}: $Name"
    }
}

Set-Location $RepoRoot

if (-not $SkipBuild) {
    Invoke-ReleaseStep "Build PyInstaller bundle" {
        $Args = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "build_windows.ps1"), "-Python", $Python)
        if ($UseExistingVenv) {
            $Args += "-UseExistingVenv"
        }
        if ($SkipDependencyInstall) {
            $Args += "-SkipDependencyInstall"
        }
        & powershell @Args
    }
} elseif (-not (Test-Path $DistDir)) {
    throw "Cannot skip build because packaged dist directory does not exist: $DistDir"
}

Invoke-ReleaseStep "Refresh Python dependency license snapshot" {
    $LicensePythonCandidates = @(
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
        $Python
    )
    $LicensePython = ($LicensePythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
    if (-not $LicensePython) {
        $LicensePython = $Python
    }
    $CudaRuntimeSitePackages = Join-Path $RepoRoot ".venv-build-windows-cuda-runtime\Lib\site-packages"
    $PreviousPythonPath = $env:PYTHONPATH
    try {
        if (Test-Path -LiteralPath $CudaRuntimeSitePackages) {
            $env:PYTHONPATH = if ($PreviousPythonPath) {
                "$CudaRuntimeSitePackages;$PreviousPythonPath"
            } else {
                $CudaRuntimeSitePackages
            }
        }
        & $LicensePython tools\generate_python_dependency_licenses.py --output LICENSES\PYTHON_DEPENDENCIES.md
        if ($LASTEXITCODE -ne 0) {
            throw "Python dependency license snapshot generation failed with exit code $LASTEXITCODE."
        }
        & $LicensePython tools\collect_third_party_license_files.py --output LICENSES\THIRD_PARTY_LICENSES
        if ($LASTEXITCODE -ne 0) {
            throw "Third-party license file collection failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        $env:PYTHONPATH = $PreviousPythonPath
    }
    & $LicensePython tools\prune_windows_dist.py --dist $DistDir
    if ($LASTEXITCODE -ne 0) {
        throw "Windows dist pruning failed with exit code $LASTEXITCODE."
    }

    $LicenseDestination = Join-Path $DistDir "LICENSES"
    New-Item -ItemType Directory -Path $LicenseDestination -Force | Out-Null
    $CuratedLicenseFiles = @(
        "README.md",
        "BUNDLED_BINARY_OBLIGATIONS.md",
        "MODEL_LICENSE_AUDIT.md",
        "PYTHON_DEPENDENCIES.md",
        "PYTHON_DEPENDENCIES_DIRECTML.md"
    )
    foreach ($LicenseFile in $CuratedLicenseFiles) {
        $Source = Join-Path $RepoRoot "LICENSES\$LicenseFile"
        if (-not (Test-Path $Source)) {
            throw "Required license/audit file missing from repository root: $Source"
        }
        Copy-Item -LiteralPath $Source -Destination (Join-Path $LicenseDestination $LicenseFile) -Force
    }
    $ThirdPartyLicensesSource = Join-Path $RepoRoot "LICENSES\THIRD_PARTY_LICENSES"
    if (-not (Test-Path $ThirdPartyLicensesSource)) {
        throw "Collected third-party license folder missing from repository root: $ThirdPartyLicensesSource"
    }
    Copy-Item -LiteralPath $ThirdPartyLicensesSource -Destination $LicenseDestination -Recurse -Force

    & $LicensePython tools\generate_windows_bundle_manifest.py --dist $DistDir --output LICENSES\WINDOWS_BUNDLE_MANIFEST.md
    if ($LASTEXITCODE -ne 0) {
        throw "Windows bundle manifest generation failed with exit code $LASTEXITCODE."
    }
    Copy-Item -LiteralPath (Join-Path $RepoRoot "LICENSES\WINDOWS_BUNDLE_MANIFEST.md") -Destination (Join-Path $LicenseDestination "WINDOWS_BUNDLE_MANIFEST.md") -Force

    $RequiredDocs = @("README.md", "CHANGELOG.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "COMPLIANCE.md", "RELEASE_CHECKLIST.md", "RELEASE_PUBLISH_HANDOFF.md", "RELEASE_REPORT.md", "RELEASE_SOURCE_PREP.md", "MODEL_DOWNLOAD_VERIFICATION.md", "PROCESSING_VERIFICATION.md", "docs\OBS_VIRTUAL_CAMERA.md")
    foreach ($Doc in $RequiredDocs) {
        $Source = Join-Path $RepoRoot $Doc
        if (-not (Test-Path $Source)) {
            throw "Required release document missing from repository root: $Source"
        }
        $Destination = Join-Path $DistDir $Doc
        New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
    }
}

Invoke-ReleaseStep "Packaged runtime preflight" {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "test_packaged_runtime.ps1") -DistDir $DistDir
}

Invoke-ReleaseStep "Windows environment preflight" {
    $Args = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "test_environment.ps1"))
    if ($RequireFfmpeg) {
        $Args += "-RequireFfmpeg"
    }
    if ($RequireCuda) {
        $Args += "-RequireCuda"
    }
    if ($RequireObsVirtualCam) {
        $Args += "-RequireObsVirtualCam"
    }
    & powershell @Args
}

Invoke-ReleaseStep "Package Inno Setup installer" {
    $Args = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "package_installer.ps1"), "-AppVersion", $AppVersion)
    if ($IsccPath) {
        $Args += @("-IsccPath", $IsccPath)
    }
    & powershell @Args
}

Invoke-ReleaseStep "Installer smoke test" {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "test_installer.ps1") -AppVersion $AppVersion
}

Invoke-ReleaseStep "Verify installer SHA-256 sidecar" {
    if (-not (Test-Path $Installer)) {
        throw "Installer missing: $Installer"
    }
    if (-not (Test-Path $InstallerHash)) {
        throw "Installer hash sidecar missing: $InstallerHash"
    }

    $Actual = (Get-FileHash $Installer -Algorithm SHA256).Hash
    $Sidecar = ((Get-Content -LiteralPath $InstallerHash -Raw).Trim() -split "\s+")[0]
    if ($Actual -ne $Sidecar) {
        throw "Installer SHA-256 sidecar mismatch. Actual: $Actual Sidecar: $Sidecar"
    }
    Write-Host "Installer SHA-256 verified: $Actual"
}

Invoke-ReleaseStep "Generate release cutover status" {
    $CutoverPythonCandidates = @(
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
        $Python
    )
    $CutoverPython = ($CutoverPythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
    if (-not $CutoverPython) {
        $CutoverPython = $Python
    }
    $Args = @(
        "tools\check_windows_release_cutover.py",
        "--repo-root", $RepoRoot,
        "--output", "RELEASE_CUTOVER_STATUS.md",
        "--limit", "500"
    )
    if ($RequirePublishReady) {
        $Args += "--strict"
        $Args += "--allow-mixed-scope-dirty"
    }
    & $CutoverPython @Args
}

if (-not $SkipSourceArchive) {
    Invoke-ReleaseStep "Package corresponding source archive" {
        $Args = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "package_source.ps1"), "-AppVersion", $AppVersion, "-GitRef", $GitRef)
        if ($AllowDirtySource -or $DraftWorkingTreeSource) {
            $Args += "-AllowDirty"
        }
        if ($DraftWorkingTreeSource) {
            $Args += "-FromWorkingTree"
        }
        & powershell @Args
    }
} else {
    Write-Host ""
    Write-Host "==> Package corresponding source archive"
    Write-Host "Skipped by -SkipSourceArchive. Do not publish until package_source.ps1 has been run against the exact release tag or commit."
}

Invoke-ReleaseStep "Generate release verification summary" {
    $VerificationPythonCandidates = @(
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
        $Python
    )
    $VerificationPython = ($VerificationPythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
    if (-not $VerificationPython) {
        $VerificationPython = $Python
    }
    $Args = @(
        "tools\generate_windows_release_verification.py",
        "--repo-root", $RepoRoot,
        "--dist", $DistDir,
        "--output-dir", (Join-Path $PSScriptRoot "installer"),
        "--app-version", $AppVersion,
        "--output", "RELEASE_VERIFICATION.md"
    )
    if ($RequirePublishReady) {
        $Args += "--require-publish-ready"
    }
    & $VerificationPython @Args
}

Invoke-ReleaseStep "Validate release artifact set" {
    $ArtifactPythonCandidates = @(
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
        $Python
    )
    $ArtifactPython = ($ArtifactPythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
    if (-not $ArtifactPython) {
        $ArtifactPython = $Python
    }
    $Args = @(
        "tools\validate_windows_release_artifacts.py",
        "--repo-root", $RepoRoot,
        "--output-dir", (Join-Path $PSScriptRoot "installer"),
        "--app-version", $AppVersion
    )
    if ($ExpectGitRefSource) {
        $Args += "--require-git-ref-source"
    }
    & $ArtifactPython @Args
}

Invoke-ReleaseStep "Assemble GitHub Release asset set" {
    $Args = @(
        "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $PSScriptRoot "assemble_release_assets.ps1"),
        "-AppVersion", $AppVersion
    )
    if ($ExpectGitRefSource) {
        $Args += "-RequireGitRefSource"
    }
    & powershell @Args
}

Invoke-ReleaseStep "Validate GitHub Release asset set" {
    $ArtifactPythonCandidates = @(
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
        $Python
    )
    $ArtifactPython = ($ArtifactPythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
    if (-not $ArtifactPython) {
        $ArtifactPython = $Python
    }
    $Args = @(
        "tools\validate_windows_release_artifacts.py",
        "--repo-root", $RepoRoot,
        "--output-dir", (Join-Path $PSScriptRoot "installer"),
        "--release-assets-dir", $ReleaseAssetsDir,
        "--app-version", $AppVersion
    )
    if ($ExpectGitRefSource) {
        $Args += "--require-git-ref-source"
    }
    & $ArtifactPython @Args
}

Write-Host ""
Write-Host "Windows release checks completed."
Write-Host "Installer: $Installer"
Write-Host "Installer SHA-256 sidecar: $InstallerHash"
Write-Host "GitHub Release assets: $ReleaseAssetsDir"
Write-Host "Release verification summary: $(Join-Path $RepoRoot "RELEASE_VERIFICATION.md")"
