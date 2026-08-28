param(
    [string]$AppVersion = "2.2.3",
    [string]$InstallerPath = "",
    [string]$InstallDir = "",
    [string]$DistDir = "",
    [string]$IsccPath = "",
    [switch]$KeepInstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $DistDir) {
    $DistDir = Join-Path $RepoRoot "dist\DeepLiveCamStudio"
}
if (-not (Test-Path -LiteralPath (Join-Path $DistDir "DeepLiveCamStudio.exe"))) {
    throw "Executable bundle not found: $DistDir"
}
$DistDir = (Resolve-Path -LiteralPath $DistDir).Path

if (-not $InstallerPath) {
    $InstallerPath = Join-Path $PSScriptRoot "installer\DeepLiveCamStudio-$AppVersion-x64-setup.exe"
}

if (-not (Test-Path $InstallerPath)) {
    throw "Installer not found: $InstallerPath"
}

if (-not $InstallDir) {
    $InstallDir = Join-Path $env:TEMP "DeepLiveCamStudio-installer-smoke-$AppVersion-$PID"
}

$InstallDir = [IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
$TempRoot = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')
if (-not $InstallDir.StartsWith("$TempRoot\", [StringComparison]::OrdinalIgnoreCase)) {
    throw "Installer smoke-test directory must be inside the current TEMP directory: $InstallDir"
}

$InstallerFullPath = (Resolve-Path $InstallerPath).Path
$TestRunId = [Guid]::NewGuid().ToString("N")
$TestAppGuid = [Guid]::NewGuid().ToString().ToUpperInvariant()
$TestAppId = "{$TestAppGuid}"
$TestDirectiveAppId = '{' + $TestAppId
$TestUninstallRegistryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$($TestAppId)_is1"
$FixtureWorkDir = Join-Path $env:TEMP "DeepLiveCamStudio-upgrade-fixture-$TestRunId"
$FixturePayloadDir = Join-Path $FixtureWorkDir "payload"
$FixtureOutputDir = Join-Path $FixtureWorkDir "output"
$LegacyInstallDir = Join-Path $InstallDir "2.2.1"
$OrphanInstallDir = Join-Path $InstallDir "2.1.9"
$ModelsDir = Join-Path $env:LOCALAPPDATA "DeepLiveCamStudio\models"
$SentinelPath = Join-Path $ModelsDir "installer-smoke-preserve-$TestRunId.txt"

if (-not $IsccPath) {
    $Command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($Command) {
        $IsccPath = $Command.Source
    } else {
        $Candidates = @(
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
        )
        $IsccPath = ($Candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1)
    }
}

if (-not $IsccPath -or -not (Test-Path -LiteralPath $IsccPath)) {
    throw "Inno Setup 6 compiler (ISCC.exe) is required for the upgrade fixture."
}

function Invoke-InstallerProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$Description = "Installer"
    )

    $Process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -Wait -PassThru
    if ($Process.ExitCode -ne 0) {
        throw "$Description exited with code $($Process.ExitCode)."
    }
}

try {
    if (Test-Path -LiteralPath $InstallDir) {
        Remove-Item -LiteralPath $InstallDir -Recurse -Force
    }
    if (Test-Path -LiteralPath $FixtureWorkDir) {
        Remove-Item -LiteralPath $FixtureWorkDir -Recurse -Force
    }

    New-Item -ItemType Directory -Path $FixturePayloadDir -Force | Out-Null
    New-Item -ItemType Directory -Path $FixtureOutputDir -Force | Out-Null
    "Legacy executable marker" | Set-Content -LiteralPath (Join-Path $FixturePayloadDir "DeepLiveCamStudio.exe") -Encoding ascii
    "This file must not survive migration." | Set-Content -LiteralPath (Join-Path $FixturePayloadDir "legacy-payload.txt") -Encoding ascii

    $FixtureScript = Join-Path $PSScriptRoot "test_legacy_installer.iss"
    & $IsccPath "/DTestAppId=$TestDirectiveAppId" "/DPayloadDir=$FixturePayloadDir" "/DOutputDir=$FixtureOutputDir" $FixtureScript
    if ($LASTEXITCODE -ne 0) {
        throw "Legacy upgrade fixture compilation failed with exit code $LASTEXITCODE."
    }

    $FixtureInstaller = Join-Path $FixtureOutputDir "DeepLiveCamStudio-2.2.1-upgrade-fixture.exe"
    $TestInstallerBaseName = "DeepLiveCamStudio-$AppVersion-isolated-test-setup"
    $InstallerScript = Join-Path $PSScriptRoot "installer.iss"
    & $IsccPath "/DAppVersion=$AppVersion" "/DRepoRoot=$RepoRoot" "/DDistDir=$DistDir" "/DOutputDir=$FixtureOutputDir" "/DAppId=$TestDirectiveAppId" "/DAppIdRegistryValue=$TestAppId" "/DOutputBaseFilename=$TestInstallerBaseName" $InstallerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Isolated candidate installer compilation failed with exit code $LASTEXITCODE."
    }
    $TestInstaller = Join-Path $FixtureOutputDir "$TestInstallerBaseName.exe"

    Write-Host "Installing legacy-layout fixture to $LegacyInstallDir"
    Invoke-InstallerProcess -FilePath $FixtureInstaller -Description "Legacy upgrade fixture" -Arguments @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/NOICONS",
        "/DIR=$LegacyInstallDir"
    )

    $FixtureRegistration = Get-ItemProperty -LiteralPath $TestUninstallRegistryPath
    $RegisteredFixtureDir = [IO.Path]::GetFullPath($FixtureRegistration.InstallLocation).TrimEnd('\')
    if (-not $RegisteredFixtureDir.Equals($LegacyInstallDir, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Legacy fixture registered an unexpected installation directory: $RegisteredFixtureDir"
    }

    New-Item -ItemType Directory -Path $OrphanInstallDir -Force | Out-Null
    "Orphaned executable marker" | Set-Content -LiteralPath (Join-Path $OrphanInstallDir "DeepLiveCamStudio.exe") -Encoding ascii
    New-Item -ItemType Directory -Path $ModelsDir -Force | Out-Null
    "Created by build/windows/test_installer.ps1; safe to delete." | Set-Content -LiteralPath $SentinelPath -Encoding ascii

    Write-Host "Upgrading legacy-layout fixture with isolated build of $InstallerFullPath"
    Invoke-InstallerProcess -FilePath $TestInstaller -Description "Candidate installer" -Arguments @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/NOICONS",
        "/DIR=$InstallDir"
    )

    if (Test-Path -LiteralPath $LegacyInstallDir) {
        throw "Registered legacy installation directory survived migration: $LegacyInstallDir"
    }
    if (Test-Path -LiteralPath $OrphanInstallDir) {
        throw "Orphaned version installation directory survived migration: $OrphanInstallDir"
    }
    if (-not (Test-Path -LiteralPath $SentinelPath)) {
        throw "Upgrade removed user model data sentinel: $SentinelPath"
    }

    $CandidateRegistration = Get-ItemProperty -LiteralPath $TestUninstallRegistryPath
    $RegisteredCandidateDir = [IO.Path]::GetFullPath($CandidateRegistration.InstallLocation).TrimEnd('\')
    if (-not $RegisteredCandidateDir.Equals($InstallDir, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Candidate registered an unexpected installation directory: $RegisteredCandidateDir"
    }
    if ($CandidateRegistration.DisplayVersion -ne $AppVersion) {
        throw "Candidate registered version $($CandidateRegistration.DisplayVersion), expected $AppVersion."
    }

$RequiredFiles = @(
    "DeepLiveCamStudio.exe",
    "DeepLiveCamStudioCLI.exe",
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
    "LICENSES\PYTHON_DEPENDENCIES_DIRECTML.md",
    "LICENSES\THIRD_PARTY_LICENSES\README.md",
    "LICENSES\THIRD_PARTY_LICENSES\tensorflow-2.19.1\package\THIRD_PARTY_NOTICES.txt",
    "LICENSES\THIRD_PARTY_LICENSES\onnxruntime-gpu-1.24.4\package\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\opencv-python-4.10.0.84\package\LICENSE-3RD-PARTY.txt",
    "LICENSES\THIRD_PARTY_LICENSES\onnx-1.22.0\licenses\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\opennsfw2-0.18.0\licenses\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\PySide6-6.11.1\METADATA",
    "LICENSES\THIRD_PARTY_LICENSES\PySide6-6.11.1\licenses\LicenseRef-Qt-Commercial.txt",
    "LICENSES\THIRD_PARTY_LICENSES\shiboken6-6.11.1\METADATA",
    "LICENSES\THIRD_PARTY_LICENSES\pyvirtualcam-0.15.0\licenses\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\cv2_enumerate_cameras-1.1.15\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\easydict-1.13\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\torch-2.11.0_cu128\LICENSE",
    "LICENSES\THIRD_PARTY_LICENSES\torch-2.11.0_cu128\METADATA",
    "LICENSES\THIRD_PARTY_LICENSES\torch-2.11.0_cu128\NOTICE",
    "LICENSES\WINDOWS_BUNDLE_MANIFEST.md"
)

$RequiredFiles += @(
    "_internal\cublas64_12.dll",
    "_internal\cublasLt64_12.dll",
    "_internal\cudart64_12.dll",
    "_internal\cudnn64_9.dll",
    "_internal\cudnn_adv64_9.dll",
    "_internal\cudnn_cnn64_9.dll",
    "_internal\cudnn_engines_precompiled64_9.dll",
    "_internal\cudnn_engines_runtime_compiled64_9.dll",
    "_internal\cudnn_graph64_9.dll",
    "_internal\cudnn_heuristic64_9.dll",
    "_internal\cudnn_ops64_9.dll",
    "_internal\cufft64_11.dll",
    "_internal\cufftw64_11.dll",
    "_internal\curand64_10.dll",
    "_internal\cusolver64_11.dll",
    "_internal\cusolverMg64_11.dll",
    "_internal\cusparse64_12.dll",
    "_internal\nvrtc-builtins64_128.dll",
    "_internal\nvrtc64_120_0.dll",
    "_internal\nvToolsExt64_1.dll",
    "_internal\zlibwapi.dll"
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

    Write-Host "Installer upgrade smoke test passed."

    if (-not $KeepInstall) {
        $Uninstaller = Join-Path $InstallDir "unins000.exe"
        if (-not (Test-Path -LiteralPath $Uninstaller)) {
            throw "Candidate uninstaller is missing: $Uninstaller"
        }

        Write-Host "Uninstalling smoke-test install."
        $Uninstall = Start-Process -FilePath $Uninstaller -ArgumentList @(
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART"
        ) -PassThru
        if (-not $Uninstall.WaitForExit(120000)) {
            Stop-Process -Id $Uninstall.Id -Force -ErrorAction SilentlyContinue
            throw "Uninstaller did not exit within 120 seconds."
        }
        if ($Uninstall.ExitCode -ne 0) {
            throw "Uninstaller exited with code $($Uninstall.ExitCode)."
        }
        if (-not (Test-Path -LiteralPath $SentinelPath)) {
            throw "Uninstall removed user model data sentinel: $SentinelPath"
        }
        if (Test-Path -LiteralPath $TestUninstallRegistryPath) {
            throw "Test uninstall registration survived uninstall: $TestUninstallRegistryPath"
        }
        $UninstallCleanupDeadline = [DateTime]::UtcNow.AddSeconds(5)
        while ((Test-Path -LiteralPath $InstallDir) -and
               ([DateTime]::UtcNow -lt $UninstallCleanupDeadline)) {
            Start-Sleep -Milliseconds 100
        }
        if (Test-Path -LiteralPath $InstallDir) {
            throw "Stable installation directory survived uninstall: $InstallDir"
        }
    }
}
finally {
    if (-not $KeepInstall) {
        if (Test-Path -LiteralPath $TestUninstallRegistryPath) {
            $CleanupRegistration = Get-ItemProperty -LiteralPath $TestUninstallRegistryPath -ErrorAction SilentlyContinue
            if ($CleanupRegistration -and $CleanupRegistration.UninstallString -match '^"([^"]+)"') {
                $CleanupUninstaller = [IO.Path]::GetFullPath($Matches[1])
                if ($CleanupUninstaller.StartsWith("$InstallDir\", [StringComparison]::OrdinalIgnoreCase) -and
                    (Test-Path -LiteralPath $CleanupUninstaller)) {
                    $CleanupProcess = Start-Process -FilePath $CleanupUninstaller -ArgumentList @(
                        "/VERYSILENT",
                        "/SUPPRESSMSGBOXES",
                        "/NORESTART"
                    ) -PassThru
                    if (-not $CleanupProcess.WaitForExit(120000)) {
                        Stop-Process -Id $CleanupProcess.Id -Force -ErrorAction SilentlyContinue
                    }
                }
            }
            Remove-Item -LiteralPath $TestUninstallRegistryPath -Recurse -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path -LiteralPath $SentinelPath) {
            Remove-Item -LiteralPath $SentinelPath -Force
        }
        if (Test-Path -LiteralPath $InstallDir) {
            Remove-Item -LiteralPath $InstallDir -Recurse -Force
        }
    }

    if (Test-Path -LiteralPath $FixtureWorkDir) {
        Remove-Item -LiteralPath $FixtureWorkDir -Recurse -Force
    }
}
