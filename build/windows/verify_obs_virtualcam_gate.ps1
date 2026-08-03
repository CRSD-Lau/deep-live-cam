param(
    [string]$Python = "python",
    [string]$CameraName = "",
    [string]$EvidenceDir = "",
    [int]$Seconds = 5
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $EvidenceDir) {
    $EvidenceDir = Join-Path $PSScriptRoot "manual-evidence\obs-virtualcam"
}

New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$TranscriptPath = Join-Path $EvidenceDir "obs-virtualcam-$Timestamp.log"
$SummaryPath = Join-Path $EvidenceDir "obs-virtualcam-$Timestamp.md"

$PythonCandidates = @(
    (Join-Path $RepoRoot "venv\Scripts\python.exe"),
    (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
    $Python
)
$CheckPython = ($PythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
if (-not $CheckPython) {
    $CheckPython = $Python
}

Set-Location $RepoRoot
Start-Transcript -LiteralPath $TranscriptPath -Force | Out-Null
try {
    Write-Host "Deep Live Cam OBS virtual camera gate evidence"
    Write-Host "Timestamp: $((Get-Date).ToUniversalTime().ToString("o"))"
    Write-Host "Computer: $env:COMPUTERNAME"
    Write-Host "User: $env:USERNAME"
    $Os = Get-CimInstance Win32_OperatingSystem
    Write-Host "Windows: $($Os.Caption) $($Os.Version) build $($Os.BuildNumber)"

    & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "test_environment.ps1") -Python $CheckPython -RequireObsVirtualCam
    if ($LASTEXITCODE -ne 0) {
        throw "OBS virtual camera environment preflight failed with exit code $LASTEXITCODE."
    }

    $Args = @("tools\check_obs_virtualcam.py", "--seconds", "$Seconds")
    if ($CameraName) {
        $Args += @("--name", $CameraName)
    }
    & $CheckPython @Args
    if ($LASTEXITCODE -ne 0) {
        throw "OBS virtual camera frame-sending check failed with exit code $LASTEXITCODE."
    }

    $SummaryTimestamp = (Get-Date).ToUniversalTime().ToString("o")
    $SummaryWindows = "$($Os.Caption) $($Os.Version) build $($Os.BuildNumber)"
    $SummaryCameraName = if ($CameraName) { $CameraName } else { "default pyvirtualcam device" }
    $Summary = @(
        "# OBS Virtual Camera Gate Evidence",
        "",
        "Status: AUTOMATED-SUBSET-PASS",
        "",
        "- Timestamp UTC: ``$SummaryTimestamp``",
        "- Windows: ``$SummaryWindows``",
        "- Camera name: ``$SummaryCameraName``",
        "- Transcript: ``$TranscriptPath``",
        "",
        "This script verifies the automated subset of",
        "`OBS_VIRTUAL_CAMERA_VERIFICATION.md`: OBS/virtual-camera environment",
        "preflight and pyvirtualcam frame sending.",
        "",
        "Manual checks still need tester confirmation before changing",
        "`OBS_VIRTUAL_CAMERA_VERIFICATION.md` to `Status: PASS`: Deep-Live-Cam",
        "live preview opens/stops cleanly, receiving app or OBS rebroadcast shows",
        "the output, the workflow matches `docs/OBS_VIRTUAL_CAMERA.md`, and no",
        "bundled model/checkpoint files are required for the OBS smoke path."
    )
    $Summary | Set-Content -LiteralPath $SummaryPath -Encoding utf8
    Write-Host "OBS virtual camera automated gate evidence written to: $SummaryPath"
}
finally {
    Stop-Transcript | Out-Null
}
