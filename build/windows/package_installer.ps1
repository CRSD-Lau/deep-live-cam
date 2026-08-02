param(
    [string]$AppVersion = "2.2.0",
    [string]$IsccPath = "",
    [string]$SignCertPath = "",
    [string]$SignCertPassword = "",
    [string]$SignToolPath = "",
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DistDir = Join-Path $RepoRoot "dist\DeepLiveCamStudio"
$Script = Join-Path $PSScriptRoot "installer.iss"
$OutputDir = Join-Path $PSScriptRoot "installer"

if (-not (Test-Path (Join-Path $DistDir "DeepLiveCamStudio.exe"))) {
    throw "Executable bundle not found at $DistDir. Run build\windows\build_windows.ps1 first."
}

$RequiredDocs = @(
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "COMPLIANCE.md",
    "RELEASE_CHECKLIST.md",
    "RELEASE_PUBLISH_HANDOFF.md",
    "RELEASE_REPORT.md",
    "RELEASE_SOURCE_PREP.md",
    "MODEL_DOWNLOAD_VERIFICATION.md",
    "PROCESSING_VERIFICATION.md",
    "docs\OBS_VIRTUAL_CAMERA.md"
)

foreach ($Doc in $RequiredDocs) {
    $Source = Join-Path $RepoRoot $Doc
    $Destination = Join-Path $DistDir $Doc
    if (-not (Test-Path $Source)) {
        throw "Required release document missing from repository root: $Source"
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

Copy-Item -LiteralPath (Join-Path $RepoRoot "Logo.png") -Destination (Join-Path $DistDir "Logo.png") -Force

$LicensePythonCandidates = @(
    (Join-Path $RepoRoot "venv\Scripts\python.exe"),
    (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
    "python"
)
$LicensePython = ($LicensePythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
if (-not $LicensePython) {
    $LicensePython = "python"
}
& $LicensePython tools\collect_third_party_license_files.py --output LICENSES\THIRD_PARTY_LICENSES
if ($LASTEXITCODE -ne 0) {
    throw "Third-party license file collection failed with exit code $LASTEXITCODE."
}
& $LicensePython tools\generate_windows_logo_assets.py --source Logo.png --output-dir build\windows\assets
if ($LASTEXITCODE -ne 0) {
    throw "Windows logo asset generation failed with exit code $LASTEXITCODE."
}
& $LicensePython tools\prune_windows_dist.py --dist $DistDir
if ($LASTEXITCODE -ne 0) {
    throw "Windows dist pruning failed with exit code $LASTEXITCODE."
}

$LicensesSource = Join-Path $RepoRoot "LICENSES"
if (Test-Path $LicensesSource) {
    Copy-Item -LiteralPath $LicensesSource -Destination $DistDir -Recurse -Force
}

& $LicensePython tools\generate_windows_bundle_manifest.py --dist $DistDir --output LICENSES\WINDOWS_BUNDLE_MANIFEST.md
if ($LASTEXITCODE -ne 0) {
    throw "Windows bundle manifest generation failed with exit code $LASTEXITCODE."
}
New-Item -ItemType Directory -Path (Join-Path $DistDir "LICENSES") -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $RepoRoot "LICENSES\WINDOWS_BUNDLE_MANIFEST.md") -Destination (Join-Path $DistDir "LICENSES\WINDOWS_BUNDLE_MANIFEST.md") -Force

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
        $IsccPath = ($Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1)
    }
}

if (-not $IsccPath -or -not (Test-Path $IsccPath)) {
    throw "Inno Setup 6 compiler (ISCC.exe) was not found. Install Inno Setup 6 or pass -IsccPath."
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
& $IsccPath "/DAppVersion=$AppVersion" "/DRepoRoot=$RepoRoot" "/DDistDir=$DistDir" "/DOutputDir=$OutputDir" $Script
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE."
}

$Installer = Join-Path $OutputDir "DeepLiveCamStudio-$AppVersion-x64-setup.exe"

if ($SignCertPath) {
    $ResolvedSignCertPath = (Resolve-Path -LiteralPath $SignCertPath).Path
    if (-not $SignCertPassword) {
        $SignCertPassword = $env:DLC_SIGN_CERT_PASSWORD
    }
    if (-not $SignCertPassword) {
        throw "Signing certificate password missing. Pass -SignCertPassword or set DLC_SIGN_CERT_PASSWORD."
    }

    if (-not $SignToolPath) {
        $Command = Get-Command signtool.exe -ErrorAction SilentlyContinue
        if ($Command) {
            $SignToolPath = $Command.Source
        } else {
            $WindowsKitsRoot = "${env:ProgramFiles(x86)}\Windows Kits\10\bin"
            if (Test-Path -LiteralPath $WindowsKitsRoot) {
                $SignToolPath = Get-ChildItem -LiteralPath $WindowsKitsRoot -Recurse -Filter signtool.exe -File |
                    Where-Object { $_.FullName -match "\\x64\\signtool\.exe$" } |
                    Sort-Object FullName -Descending |
                    Select-Object -First 1 -ExpandProperty FullName
            }
        }
    }

    if (-not $SignToolPath -or -not (Test-Path -LiteralPath $SignToolPath)) {
        throw "signtool.exe was not found. Install the Windows SDK or pass -SignToolPath."
    }

    & $SignToolPath sign /fd SHA256 /tr $TimestampUrl /td SHA256 /f $ResolvedSignCertPath /p $SignCertPassword $Installer
    if ($LASTEXITCODE -ne 0) {
        throw "signtool signing failed with exit code $LASTEXITCODE."
    }

    & $SignToolPath verify /pa /v $Installer
    if ($LASTEXITCODE -ne 0) {
        throw "signtool verification failed with exit code $LASTEXITCODE."
    }

    Write-Host "Installer signed with certificate: $ResolvedSignCertPath"
}

$HashPath = "$Installer.sha256"
$Hash = Get-FileHash $Installer -Algorithm SHA256
"$($Hash.Hash)  $(Split-Path $Installer -Leaf)" | Set-Content -LiteralPath $HashPath -Encoding ascii
Write-Host "Installer created at: $Installer"
Write-Host "SHA-256 written to: $HashPath"
Write-Host "SHA-256: $($Hash.Hash)"
