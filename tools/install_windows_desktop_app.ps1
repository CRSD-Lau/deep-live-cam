[CmdletBinding()]
param(
    [string]$ShortcutName = "Deep Live Cam Studio"
)

$ErrorActionPreference = "Stop"

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ToolsDir "..")).Path
$LauncherPath = Join-Path $ProjectRoot "DeepLiveCamStudio.pyw"
$VenvPythonw = Join-Path $ProjectRoot "venv\Scripts\pythonw.exe"

if (-not (Test-Path -LiteralPath $LauncherPath)) {
    throw "Desktop launcher not found: $LauncherPath"
}

if (Test-Path -LiteralPath $VenvPythonw) {
    $PythonwPath = $VenvPythonw
} else {
    $PythonwCommand = Get-Command "pythonw.exe" -ErrorAction SilentlyContinue
    if ($null -eq $PythonwCommand) {
        throw "pythonw.exe was not found. Create the venv first or install Python with the py launcher."
    }
    $PythonwPath = $PythonwCommand.Source
}

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "$ShortcutName.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonwPath
$Shortcut.Arguments = '"' + $LauncherPath + '"'
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.IconLocation = "$PythonwPath,0"
$Shortcut.Description = "Launch Deep Live Cam Studio without a console window."
$Shortcut.Save()

Write-Host "Created desktop shortcut: $ShortcutPath"
Write-Host "Launcher: $LauncherPath"
Write-Host "Python windowed runtime: $PythonwPath"
