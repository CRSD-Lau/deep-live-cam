param(
    [string]$Python = "",
    [switch]$RequireFfmpeg,
    [switch]$RequireCuda,
    [switch]$RequireObsVirtualCam
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if (-not $Python) {
    $VenvPython = Join-Path $RepoRoot "venv\Scripts\python.exe"
    if (Test-Path $VenvPython) {
        $Python = $VenvPython
    } else {
        $Python = "python"
    }
}

function Test-CommandAvailable {
    param(
        [string]$Name,
        [switch]$Required
    )

    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($Command) {
        Write-Host "[environment] $Name found: $($Command.Source)"
        & $Command.Source -version 2>$null | Select-Object -First 1
        return $true
    }

    $Message = "[environment] $Name not found on PATH."
    if ($Required) {
        throw $Message
    }
    Write-Host $Message
    return $false
}

Set-Location $RepoRoot

Write-Host "[environment] Python: $Python"
& $Python --version
if ($LASTEXITCODE -ne 0) {
    throw "Python version check failed."
}

Test-CommandAvailable -Name "ffmpeg" -Required:$RequireFfmpeg | Out-Null
Test-CommandAvailable -Name "ffprobe" -Required:$RequireFfmpeg | Out-Null

$cudaArgs = @("tools\check_cuda_provider.py", "--execution-provider", "cuda")
if ($RequireCuda) {
    $cudaArgs += "--strict"
}
& $Python @cudaArgs
$cudaExit = $LASTEXITCODE
if ($RequireCuda -and $cudaExit -ne 0) {
    throw "CUDA provider preflight failed with exit code $cudaExit."
}
if (-not $RequireCuda -and $cudaExit -ne 0) {
    Write-Host "[environment] CUDA provider check reported exit code $cudaExit; continuing because -RequireCuda was not set."
}

if ($RequireObsVirtualCam) {
    & $Python tools\check_obs_virtualcam.py --seconds 1
    if ($LASTEXITCODE -ne 0) {
        throw "OBS/virtual camera preflight failed with exit code $LASTEXITCODE."
    }
} else {
    Write-Host "[environment] OBS virtual camera active-output test skipped. Re-run with -RequireObsVirtualCam on an OBS test machine."
    if ($IsWindows) {
        try {
            & $Python -c "from pygrabber.dshow_graph import FilterGraph; print('[environment] DirectShow devices:'); [print('  ' + str(device)) for device in FilterGraph().get_input_devices()]"
        } catch {
            Write-Host "[environment] DirectShow device listing skipped: $_"
        }
    }
}

Write-Host "[environment] Windows environment preflight complete."
