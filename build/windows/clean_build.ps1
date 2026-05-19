$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

$Targets = @(
    (Join-Path $RepoRoot "build\windows\pyinstaller-work"),
    (Join-Path $RepoRoot "build\windows\installer"),
    (Join-Path $RepoRoot "dist\DeepLiveCamStudio")
)

foreach ($Target in $Targets) {
    $ResolvedParent = Resolve-Path (Split-Path $Target -Parent)
    if ((Test-Path $Target) -and $ResolvedParent.Path.StartsWith($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
}

Write-Host "Windows build outputs cleaned."
