# Author: Neil Mitchell
# Creator: Neil Mitchell
# Last Modified By: Neil Mitchell
# Runs only in a disposable GitHub-hosted Windows job. Installs the exact
# downloaded release installers without building an application environment.
param(
    [Parameter(Mandatory = $true)][string]$PreviousInstaller,
    [Parameter(Mandatory = $true)][string]$CandidateInstaller,
    [Parameter(Mandatory = $true)][string]$OutputDir
)

$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') {
    throw 'This installer gate runs only on a disposable GitHub Actions Windows runner.'
}

$previousHash = 'D91080BEF32A6BB731830599BFDA90EECA4844D20AF6D34E67957C0BDA2B48BF'
$candidateHash = 'CB791D82188DB06E70DFC0A0229D2005AE43636A7D0CFCCCFAEAC802580702DF'
$candidateSource = '2d60d2e615a4eb09d48a9ddbad2572400d1cdd1d'
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\DeepLiveCamStudio'
$userDataDir = Join-Path $env:LOCALAPPDATA 'DeepLiveCamStudio'
$uninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{7B7D33BB-6B98-48D2-A8D5-31D6D6E53A08}_is1'
$machineUninstallKey = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{7B7D33BB-6B98-48D2-A8D5-31D6D6E53A08}_is1'

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$receipt = [ordered]@{
    author = 'Neil Mitchell'
    creator = 'Neil Mitchell'
    last_modified_by = 'Neil Mitchell'
    checked_utc = [DateTime]::UtcNow.ToString('o')
    runner = $env:RUNNER_NAME
    operating_system = (Get-CimInstance Win32_OperatingSystem).Caption
    os_build = (Get-CimInstance Win32_OperatingSystem).BuildNumber
    candidate_source_commit = $candidateSource
    status = 'FAIL'
    previous_installer = [ordered]@{}
    candidate_installer = [ordered]@{}
    checks = [ordered]@{}
    errors = @()
}

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Invoke-LoggedProcess([string]$FilePath, [string[]]$Arguments, [string]$Label, [int[]]$AcceptedExitCodes = @(0)) {
    $stdout = Join-Path $OutputDir "$Label.stdout.log"
    $stderr = Join-Path $OutputDir "$Label.stderr.log"
    $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if ($process.ExitCode -notin $AcceptedExitCodes) {
        throw "$Label exited $($process.ExitCode); expected $($AcceptedExitCodes -join ',')."
    }
    return [ordered]@{ exit_code = $process.ExitCode; stdout = (Split-Path -Leaf $stdout); stderr = (Split-Path -Leaf $stderr) }
}

try {
    Assert-True (Test-Path -LiteralPath $PreviousInstaller) 'Previous installer is missing.'
    Assert-True (Test-Path -LiteralPath $CandidateInstaller) 'Candidate installer is missing.'
    Assert-True (-not (Test-Path -LiteralPath $installDir)) 'Runner is not clean: app install directory already exists.'
    Assert-True (-not (Test-Path -LiteralPath $userDataDir)) 'Runner is not clean: app user data already exists.'
    Assert-True (-not (Test-Path -LiteralPath $uninstallKey)) 'Runner is not clean: app HKCU uninstall key already exists.'

    $oldActual = (Get-FileHash -LiteralPath $PreviousInstaller -Algorithm SHA256).Hash
    $newActual = (Get-FileHash -LiteralPath $CandidateInstaller -Algorithm SHA256).Hash
    $receipt.previous_installer = [ordered]@{ name = (Split-Path -Leaf $PreviousInstaller); bytes = (Get-Item -LiteralPath $PreviousInstaller).Length; sha256 = $oldActual }
    $receipt.candidate_installer = [ordered]@{ name = (Split-Path -Leaf $CandidateInstaller); bytes = (Get-Item -LiteralPath $CandidateInstaller).Length; sha256 = $newActual }
    Assert-True ($oldActual -eq $previousHash) 'Published 2.2.4 installer SHA-256 mismatch.'
    Assert-True ($newActual -eq $candidateHash) 'Exact 2.2.5 candidate installer SHA-256 mismatch.'
    $receipt.checks.exact_downloaded_bytes = 'PASS'

    # The hosted image may contain development tools. The application process
    # receives only the base Windows search path, so no host Python/Node can
    # satisfy missing packaged dependencies during runtime checks.
    $env:PATH = @(
        "$env:WINDIR\System32",
        "$env:WINDIR",
        "$env:WINDIR\System32\Wbem",
        "$env:WINDIR\System32\WindowsPowerShell\v1.0"
    ) -join ';'
    Assert-True (-not (Get-Command python,node -ErrorAction SilentlyContinue)) 'Python or Node remains on sanitized PATH.'
    $receipt.checks.sanitized_path = 'PASS'

    $cli = Join-Path $installDir 'DeepLiveCamStudioCLI.exe'
    $uninstaller = Join-Path $installDir 'unins000.exe'

    $receipt.checks.clean_install_225 = Invoke-LoggedProcess $CandidateInstaller @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOICONS') 'clean-install-225'
    Assert-True (Test-Path -LiteralPath $cli) '2.2.5 clean install has no CLI executable.'
    Assert-True (Test-Path -LiteralPath $uninstallKey) '2.2.5 clean install has no HKCU uninstall registration.'
    Assert-True (-not (Test-Path -LiteralPath $machineUninstallKey)) '2.2.5 clean installer unexpectedly registered machine-wide.'
    Assert-True ((Get-ItemProperty -LiteralPath $uninstallKey).DisplayVersion -eq '2.2.5') 'Clean 2.2.5 install registered the wrong version.'
    $receipt.checks.clean_version_225 = Invoke-LoggedProcess $cli @('--version') 'clean-version-225'
    Assert-True ((Get-Content -LiteralPath (Join-Path $OutputDir 'clean-version-225.stdout.log') -Raw) -match '2\.2\.5') 'Clean 2.2.5 CLI returned the wrong version.'
    Assert-True (Test-Path -LiteralPath $uninstaller) 'Clean 2.2.5 install has no uninstaller.'
    $receipt.checks.clean_uninstall_225 = Invoke-LoggedProcess $uninstaller @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') 'clean-uninstall-225'
    Assert-True (-not (Test-Path -LiteralPath $cli)) 'Clean uninstall left the CLI executable.'
    Assert-True (-not (Test-Path -LiteralPath $uninstallKey)) 'Clean uninstall left the HKCU registration.'
    Assert-True (-not (Test-Path -LiteralPath $userDataDir)) 'Clean version check unexpectedly created user data.'

    $receipt.checks.install_224 = Invoke-LoggedProcess $PreviousInstaller @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOICONS') 'install-224'
    Assert-True (Test-Path -LiteralPath $cli) '2.2.4 clean install has no CLI executable.'
    Assert-True (Test-Path -LiteralPath $uninstallKey) '2.2.4 install has no HKCU uninstall registration.'
    Assert-True (-not (Test-Path -LiteralPath $machineUninstallKey)) '2.2.4 installer unexpectedly registered machine-wide.'
    $oldRegistration = Get-ItemProperty -LiteralPath $uninstallKey
    Assert-True ($oldRegistration.DisplayVersion -eq '2.2.4') '2.2.4 registered the wrong version.'
    Assert-True ([IO.Path]::GetFullPath($oldRegistration.InstallLocation).TrimEnd('\') -eq [IO.Path]::GetFullPath($installDir).TrimEnd('\')) '2.2.4 registered an unexpected install path.'
    $receipt.checks.version_224 = Invoke-LoggedProcess $cli @('--version') 'version-224'
    Assert-True ((Get-Content -LiteralPath (Join-Path $OutputDir 'version-224.stdout.log') -Raw) -match '2\.2\.4') 'Installed 2.2.4 CLI returned the wrong version.'

    New-Item -ItemType Directory -Path (Join-Path $userDataDir 'models') -Force | Out-Null
    $modelSentinel = Join-Path $userDataDir 'models\validation-preserve.txt'
    $settingsSentinel = Join-Path $userDataDir 'validation-settings.json'
    Set-Content -LiteralPath $modelSentinel -Value 'Deep Live Cam 2.2.5 upgrade preservation model sentinel' -Encoding UTF8
    Set-Content -LiteralPath $settingsSentinel -Value '{"source":"clean-hosted-validation","preserve":true}' -Encoding UTF8
    $modelSentinelHash = (Get-FileHash -LiteralPath $modelSentinel -Algorithm SHA256).Hash
    $settingsSentinelHash = (Get-FileHash -LiteralPath $settingsSentinel -Algorithm SHA256).Hash

    $receipt.checks.upgrade_225 = Invoke-LoggedProcess $CandidateInstaller @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOICONS') 'upgrade-225'
    Assert-True (Test-Path -LiteralPath $cli) '2.2.5 upgrade has no CLI executable.'
    $registration = Get-ItemProperty -LiteralPath $uninstallKey
    Assert-True ($registration.DisplayVersion -eq '2.2.5') '2.2.5 registered the wrong version.'
    Assert-True ([IO.Path]::GetFullPath($registration.InstallLocation).TrimEnd('\') -eq [IO.Path]::GetFullPath($installDir).TrimEnd('\')) '2.2.5 registered an unexpected install path.'
    Assert-True (-not (Test-Path -LiteralPath $machineUninstallKey)) '2.2.5 installer unexpectedly registered machine-wide.'
    Assert-True ((Get-FileHash -LiteralPath $modelSentinel -Algorithm SHA256).Hash -eq $modelSentinelHash) 'Upgrade changed the model sentinel.'
    Assert-True ((Get-FileHash -LiteralPath $settingsSentinel -Algorithm SHA256).Hash -eq $settingsSentinelHash) 'Upgrade changed the settings sentinel.'
    $receipt.checks.user_data_preserved_on_upgrade = 'PASS'
    $receipt.checks.version_225 = Invoke-LoggedProcess $cli @('--version') 'version-225'
    Assert-True ((Get-Content -LiteralPath (Join-Path $OutputDir 'version-225.stdout.log') -Raw) -match '2\.2\.5') 'Installed 2.2.5 CLI returned the wrong version.'
    $receipt.checks.cpu_provider = Invoke-LoggedProcess $cli @('--execution-provider', 'cpu', '--check-execution-provider') 'cpu-provider'
    $receipt.checks.model_notice_cancel = Invoke-LoggedProcess $cli @('--download-models') 'model-notice-cancel' @(2)
    $notice = Get-Content -LiteralPath (Join-Path $OutputDir 'model-notice-cancel.stdout.log') -Raw
    Assert-True ($notice.Contains('Download cancelled. No model files were installed.')) 'Model notice did not cancel safely.'
    Assert-True ($notice.Contains('inswapper_128.onnx') -and $notice.Contains('SHA256:')) 'Model source/checksum notice is incomplete.'
    Assert-True (@(Get-ChildItem -LiteralPath (Join-Path $userDataDir 'models') -File | Where-Object { $_.Extension -in @('.onnx', '.pth', '.safetensors') }).Count -eq 0) 'Model notice downloaded a model without consent.'
    $receipt.checks.model_consent_cancel = 'PASS'
    Assert-True (@(Get-ChildItem -LiteralPath $installDir -Recurse -File | Where-Object { $_.Extension -in @('.onnx', '.pth', '.safetensors') }).Count -eq 0) 'Installer payload contains model/checkpoint files.'
    $receipt.checks.model_payload_exclusion = 'PASS'

    $uninstaller = Join-Path $installDir 'unins000.exe'
    Assert-True (Test-Path -LiteralPath $uninstaller) 'Uninstaller is missing.'
    $receipt.checks.uninstall_225 = Invoke-LoggedProcess $uninstaller @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') 'uninstall-225'
    Assert-True (-not (Test-Path -LiteralPath $cli)) 'Uninstall left the application executable.'
    Assert-True (-not (Test-Path -LiteralPath $uninstallKey)) 'Uninstall left the HKCU registration.'
    Assert-True ((Get-FileHash -LiteralPath $modelSentinel -Algorithm SHA256).Hash -eq $modelSentinelHash) 'Uninstall changed the model sentinel.'
    Assert-True ((Get-FileHash -LiteralPath $settingsSentinel -Algorithm SHA256).Hash -eq $settingsSentinelHash) 'Uninstall changed the settings sentinel.'
    $receipt.checks.user_data_preserved_on_uninstall = 'PASS'
    $receipt.status = 'PASS'
} catch {
    $receipt.errors += $_.Exception.Message
    Write-Warning $_.Exception.Message
} finally {
    $receipt.finished_utc = [DateTime]::UtcNow.ToString('o')
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputDir 'clean-hosted-validation.json') -Encoding UTF8
}

if ($receipt.status -ne 'PASS') { exit 1 }
