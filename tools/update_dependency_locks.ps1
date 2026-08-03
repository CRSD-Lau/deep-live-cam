param(
    [string]$Python = "",
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LockVenv = Join-Path $RepoRoot ".venv-locks"
$LockPython = Join-Path $LockVenv "Scripts\python.exe"
$LockDir = Join-Path $RepoRoot "requirements-locks"

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

function Assert-PythonVersion {
    param([string]$PythonExe)

    $Version = & $PythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    if ($LASTEXITCODE -ne 0 -or $Version.Trim() -ne "3.11.9") {
        throw "Dependency locks must be generated with CPython 3.11.9; found $Version at $PythonExe"
    }
}

function Compile-Lock {
    param(
        [string]$Output,
        [string[]]$Inputs,
        [string[]]$AdditionalArguments = @()
    )

    $Arguments = @(
        "-m", "piptools", "compile",
        "--allow-unsafe",
        "--generate-hashes",
        "--no-header",
        "--quiet",
        "--resolver=backtracking",
        "--strip-extras",
        "--output-file", $Output
    )
    $Arguments += $AdditionalArguments
    $Arguments += $Inputs
    Invoke-Checked $LockPython $Arguments
}

function Write-CudaRuntimeLock {
    param(
        [string]$Output,
        [string]$AuditOutput
    )

    $Requirements = @(
        Get-Content -LiteralPath "requirements-build-windows-cuda.txt" |
            Where-Object { $_ -match '^torch==' }
    )
    if ($Requirements.Count -ne 1 -or $Requirements[0] -notmatch '^torch==([^+]+)\+cu128$') {
        throw "Expected one torch==<version>+cu128 requirement in requirements-build-windows-cuda.txt"
    }
    $TorchVersion = $Matches[1]
    $WheelName = "torch-$TorchVersion%2Bcu128-cp311-cp311-win_amd64.whl"
    $IndexUrl = "https://download.pytorch.org/whl/cu128/torch/"
    $Index = (Invoke-WebRequest -UseBasicParsing $IndexUrl).Content
    $Pattern = 'href="[^"]*/' + [regex]::Escape($WheelName) + '#sha256=([0-9a-f]{64})"'
    $WheelMatch = [regex]::Match($Index, $Pattern)
    if (-not $WheelMatch.Success) {
        throw "Could not find the CPython 3.11 Windows x64 wheel hash for torch==$TorchVersion+cu128"
    }

    $Contents = @(
        "--extra-index-url https://download.pytorch.org/whl/cu128",
        ("torch==$TorchVersion+cu128 " + [char]92),
        "    --hash=sha256:$($WheelMatch.Groups[1].Value)",
        ""
    ) -join [Environment]::NewLine
    [System.IO.File]::WriteAllText($Output, $Contents, [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText(
        $AuditOutput,
        "torch==$TorchVersion" + [Environment]::NewLine,
        [System.Text.UTF8Encoding]::new($false)
    )
}

Set-Location $RepoRoot

if (-not $Python) {
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $PyLauncher) {
        throw "The Python launcher is required. Install CPython 3.11.9 or pass -Python explicitly."
    }
    $Python = $PyLauncher.Source
    $BootstrapArguments = @("-3.11")
} else {
    $BootstrapArguments = @()
}

if (-not (Test-Path -LiteralPath $LockPython)) {
    Invoke-Checked $Python ($BootstrapArguments + @("-m", "venv", $LockVenv))
}
Assert-PythonVersion $LockPython
Invoke-Checked $LockPython @("-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements-lock-tools.txt")

if ($Check) {
    $OutputRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("deep-live-cam-lock-check-" + [guid]::NewGuid().ToString("N"))
} else {
    $OutputRoot = $LockDir
}
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

try {
    Compile-Lock `
        -Output (Join-Path $OutputRoot "windows-cuda-py311.lock") `
        -Inputs @("requirements.txt", "requirements-build-windows.txt")
    Write-CudaRuntimeLock -Output (Join-Path $OutputRoot "windows-cuda-runtime-py311.lock") -AuditOutput (Join-Path $OutputRoot "windows-cuda-runtime-audit-py311.txt")
    Compile-Lock `
        -Output (Join-Path $OutputRoot "windows-directml-py311.lock") `
        -Inputs @("requirements-directml.txt", "requirements-build-windows.txt")

    if ($Check) {
        $Mismatches = @()
        foreach ($Name in @("windows-cuda-py311.lock", "windows-cuda-runtime-py311.lock", "windows-cuda-runtime-audit-py311.txt", "windows-directml-py311.lock")) {
            $Expected = Join-Path $LockDir $Name
            $Generated = Join-Path $OutputRoot $Name
            if (-not (Test-Path -LiteralPath $Expected) -or
                (Get-FileHash -LiteralPath $Expected -Algorithm SHA256).Hash -ne
                (Get-FileHash -LiteralPath $Generated -Algorithm SHA256).Hash) {
                $Mismatches += $Name
            }
        }
        if ($Mismatches) {
            throw "Dependency locks are stale: $($Mismatches -join ', '). Run tools\update_dependency_locks.ps1 and review the diff."
        }
        Write-Host "Dependency locks are current."
    } else {
        Write-Host "Updated deterministic dependency locks in: $LockDir"
    }
}
finally {
    if ($Check -and (Test-Path -LiteralPath $OutputRoot)) {
        Remove-Item -LiteralPath $OutputRoot -Recurse -Force
    }
}
