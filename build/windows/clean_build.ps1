param(
    [string]$AppVersion = "2.2.3",
    [switch]$PruneStaleInstallerArtifacts
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

function Remove-IfInsideRepo {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $Resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not $Resolved.StartsWith($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside repository: $Resolved"
    }
    Remove-Item -LiteralPath $Resolved -Recurse -Force
}

function Get-ReleaseAssetName {
    param(
        [string]$ManifestText,
        [string]$Pattern
    )

    $Match = [regex]::Match($ManifestText, $Pattern)
    if (-not $Match.Success) {
        return $null
    }
    return $Match.Groups[1].Value
}

$Targets = @(
    (Join-Path $RepoRoot "build\windows\pyinstaller-work"),
    (Join-Path $RepoRoot "build\windows\pyinstaller-work-directml"),
    (Join-Path $RepoRoot "build\windows\installer"),
    (Join-Path $RepoRoot "build\windows\portable"),
    (Join-Path $RepoRoot ".venv-build-windows-cuda-runtime"),
    (Join-Path $RepoRoot "dist\DeepLiveCamStudio"),
    (Join-Path $RepoRoot "dist\DeepLiveCamStudio-DirectML")
)

if ($PruneStaleInstallerArtifacts) {
    $InstallerDir = Join-Path $RepoRoot "build\windows\installer"
    $ReleaseAssetsManifest = Join-Path $RepoRoot "build\windows\release-assets\$AppVersion\RELEASE_ASSETS.md"
    if (-not (Test-Path -LiteralPath $InstallerDir)) {
        Write-Host "No installer artifact directory found."
        exit 0
    }
    if (-not (Test-Path -LiteralPath $ReleaseAssetsManifest)) {
        throw "Release asset manifest missing: $ReleaseAssetsManifest"
    }

    $ManifestText = Get-Content -LiteralPath $ReleaseAssetsManifest -Raw
    $CurrentInstaller = "DeepLiveCamStudio-$AppVersion-x64-setup.exe"
    $CurrentSource = Get-ReleaseAssetName -ManifestText $ManifestText -Pattern "``(DeepLiveCamStudio-[^``]+-source-[^``]+\.zip)``"
    if (-not $CurrentSource) {
        throw "Could not determine current source archive from $ReleaseAssetsManifest"
    }

    $Keep = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    @(
        $CurrentInstaller,
        "$CurrentInstaller.sha256",
        $CurrentSource,
        "$CurrentSource.sha256",
        ([System.IO.Path]::ChangeExtension($CurrentSource, ".manifest.md"))
    ) | ForEach-Object { [void]$Keep.Add($_) }

    $Removed = 0
    Get-ChildItem -LiteralPath $InstallerDir -File |
        Where-Object {
            $_.Name -like "DeepLiveCamStudio-$AppVersion-source-*" -and -not $Keep.Contains($_.Name)
        } |
        ForEach-Object {
            Remove-IfInsideRepo -Path $_.FullName
            $Removed += 1
        }

    Write-Host "Pruned $Removed stale source artifact file(s) from $InstallerDir."
} else {
    foreach ($Target in $Targets) {
        Remove-IfInsideRepo -Path $Target
    }

    Write-Host "Windows build outputs cleaned."
}
