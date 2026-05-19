param(
    [string]$AppVersion = "2.1.6",
    [string]$InstallerPath = "",
    [string]$EvidenceDir = "",
    [switch]$KeepInstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $InstallerPath) {
    $InstallerPath = Join-Path $PSScriptRoot "installer\DeepLiveCamStudio-$AppVersion-x64-setup.exe"
}
if (-not $EvidenceDir) {
    $EvidenceDir = Join-Path $PSScriptRoot "manual-evidence\clean-vm"
}
if (-not (Test-Path $InstallerPath)) {
    throw "Installer not found: $InstallerPath"
}

New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$TranscriptPath = Join-Path $EvidenceDir "clean-vm-$AppVersion-$Timestamp.log"
$SummaryPath = Join-Path $EvidenceDir "clean-vm-$AppVersion-$Timestamp.md"
$InstallDir = Join-Path $env:TEMP "DeepLiveCamStudio-clean-vm-gate-$AppVersion"

Start-Transcript -LiteralPath $TranscriptPath -Force | Out-Null
try {
    Write-Host "Deep Live Cam clean VM gate evidence"
    Write-Host "Timestamp: $((Get-Date).ToUniversalTime().ToString("o"))"
    Write-Host "Computer: $env:COMPUTERNAME"
    Write-Host "User: $env:USERNAME"
    Write-Host "Installer: $InstallerPath"
    Write-Host "Installer SHA-256: $((Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash)"
    Write-Host "Admin identity: $([Security.Principal.WindowsIdentity]::GetCurrent().Name)"
    $Os = Get-CimInstance Win32_OperatingSystem
    Write-Host "Windows: $($Os.Caption) $($Os.Version) build $($Os.BuildNumber)"
    Write-Host "Install dir: $InstallDir"

    $Args = @(
        "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $PSScriptRoot "test_installer.ps1"),
        "-AppVersion", $AppVersion,
        "-InstallerPath", $InstallerPath,
        "-InstallDir", $InstallDir
    )
    if ($KeepInstall) {
        $Args += "-KeepInstall"
    }
    & powershell @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Installer verification failed with exit code $LASTEXITCODE."
    }

    $SummaryTimestamp = (Get-Date).ToUniversalTime().ToString("o")
    $SummaryHash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash
    $SummaryWindows = "$($Os.Caption) $($Os.Version) build $($Os.BuildNumber)"
    $Summary = @(
        "# Clean VM Gate Evidence",
        "",
        "Status: AUTOMATED-SUBSET-PASS",
        "",
        "- Timestamp UTC: ``$SummaryTimestamp``",
        "- Installer: ``$InstallerPath``",
        "- Installer SHA-256: ``$SummaryHash``",
        "- Windows: ``$SummaryWindows``",
        "- Transcript: ``$TranscriptPath``",
        "",
        "This script verifies the automated subset of `CLEAN_VM_VERIFICATION.md`:",
        "silent per-user install, required installed files, forbidden model/checkpoint",
        "scan, CLI `--version`, silent uninstall, and user-model sentinel preservation.",
        "",
        "Manual checks still need tester confirmation before changing",
        "`CLEAN_VM_VERIFICATION.md` to `Status: PASS`: Start menu shortcut, optional",
        "desktop shortcut, model download consent text, missing-model messaging, and",
        "interactive uninstall prompt."
    )
    $Summary | Set-Content -LiteralPath $SummaryPath -Encoding utf8
    Write-Host "Clean VM automated gate evidence written to: $SummaryPath"
}
finally {
    Stop-Transcript | Out-Null
}
