param(
    [string]$Python = "",
    [string]$VenvPath = ".venv-directml"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ResolvedVenv = if ([System.IO.Path]::IsPathRooted($VenvPath)) {
    $VenvPath
} else {
    Join-Path $RepoRoot $VenvPath
}

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

$BootstrapArgs = @()
if (-not $Python) {
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        $Python = $PyLauncher.Source
        $BootstrapArgs = @("-3.11")
    } else {
        $PythonCommand = Get-Command python -ErrorAction Stop
        $Python = $PythonCommand.Source
    }
}

$PythonExe = Join-Path $ResolvedVenv "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonExe)) {
    Invoke-Checked $Python ($BootstrapArgs + @("-m", "venv", $ResolvedVenv))
}

$DirectMLPythonVersion = & $PythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0 -or $DirectMLPythonVersion.Trim() -ne "3.11.9") {
    throw "The DirectML lock requires CPython 3.11.9; found $DirectMLPythonVersion at $PythonExe"
}

Invoke-Checked $PythonExe @("-m", "pip", "uninstall", "-y", "onnxruntime", "onnxruntime-gpu")
Invoke-Checked $PythonExe @(
    "-m", "pip", "install", "--require-hashes",
    "-r", "requirements-locks\windows-directml-py311.lock"
)
Invoke-Checked $PythonExe @(
    "tools\check_cuda_provider.py",
    "--execution-provider", "directml",
    "--strict"
)

Write-Host "DirectML environment is ready: $ResolvedVenv"
Write-Host "Launch with: run-directml.bat"
