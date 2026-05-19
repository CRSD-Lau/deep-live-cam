param(
    [string]$Python = "python",
    [switch]$Stage,
    [switch]$AllowUnknown
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$CutoverJson = Join-Path $env:TEMP "deep-live-cam-release-cutover-status.json"

Set-Location $RepoRoot

$PythonCandidates = @(
    (Join-Path $RepoRoot "venv\Scripts\python.exe"),
    (Join-Path $RepoRoot ".venv-build-windows\Scripts\python.exe"),
    $Python
)
$CutoverPython = ($PythonCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1)
if (-not $CutoverPython) {
    $CutoverPython = $Python
}

function Invoke-CutoverStatus {
    param(
        [switch]$WriteReport
    )

    $Args = @(
        "tools\check_windows_release_cutover.py",
        "--repo-root", $RepoRoot,
        "--json-output", $CutoverJson,
        "--limit", "500"
    )
    if ($WriteReport) {
        $Args += @("--output", "RELEASE_CUTOVER_STATUS.md")
    }
    & $CutoverPython @Args | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Cutover status generation failed with exit code $LASTEXITCODE."
    }
    return Get-Content -LiteralPath $CutoverJson -Raw | ConvertFrom-Json
}

$Status = Invoke-CutoverStatus -WriteReport
$ReleasePaths = @($Status.release_paths)
$MixedScopePaths = @($Status.mixed_scope_paths)
$UnknownPaths = @($Status.unknown_paths)

Write-Host ""
Write-Host "Release-owned paths: $($ReleasePaths.Count)"
Write-Host "Mixed-scope paths left unstaged: $($MixedScopePaths.Count)"
Write-Host "Unknown paths: $($UnknownPaths.Count)"

if ($UnknownPaths.Count -gt 0 -and -not $AllowUnknown) {
    $UnknownPaths | ForEach-Object { Write-Host "Unknown dirty path: $_" }
    throw "Unknown dirty paths remain. Classify them in tools/check_windows_release_cutover.py or rerun with -AllowUnknown for diagnostics only."
}

if (-not $ReleasePaths) {
    Write-Host "No release-owned paths to stage."
    exit 0
}

if (-not $Stage) {
    Write-Host ""
    Write-Host "Dry run only. Rerun with -Stage to stage the release-owned paths listed in RELEASE_CUTOVER_STATUS.md."
    exit 0
}

git add -- $ReleasePaths
if ($LASTEXITCODE -ne 0) {
    throw "git add failed with exit code $LASTEXITCODE."
}

$PostStageStatus = Invoke-CutoverStatus -WriteReport
git add -- RELEASE_CUTOVER_STATUS.md
if ($LASTEXITCODE -ne 0) {
    throw "git add RELEASE_CUTOVER_STATUS.md failed with exit code $LASTEXITCODE."
}

Write-Host ""
Write-Host "Post-stage release-owned paths: $(@($PostStageStatus.release_paths).Count)"
Write-Host "Post-stage staged release-owned paths: $(@($PostStageStatus.staged_release_paths).Count)"
Write-Host "Post-stage unstaged release-owned paths: $(@($PostStageStatus.unstaged_release_paths).Count)"
Write-Host "Staged release-owned paths. Review with: git diff --cached --stat"
