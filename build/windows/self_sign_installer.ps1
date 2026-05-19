param(
    [string]$AppVersion = "2.1.6",
    [string]$PublisherName = "Neil Mitchell",
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [switch]$TrustForCurrentUser
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Installer = Join-Path $PSScriptRoot "installer\DeepLiveCamStudio-$AppVersion-x64-setup.exe"
if (-not (Test-Path -LiteralPath $Installer)) {
    throw "Installer not found: $Installer"
}

$Subject = "CN=$PublisherName"
$Cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
    Where-Object { $_.Subject -eq $Subject } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if (-not $Cert) {
    $Cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $Subject `
        -CertStoreLocation Cert:\CurrentUser\My `
        -KeyUsage DigitalSignature `
        -KeyAlgorithm RSA `
        -KeyLength 3072 `
        -HashAlgorithm SHA256 `
        -NotAfter (Get-Date).AddYears(5)
}

$SigningDir = Join-Path $PSScriptRoot "signing"
New-Item -ItemType Directory -Path $SigningDir -Force | Out-Null
$CerPath = Join-Path $SigningDir "$($PublisherName.Replace(' ', ''))-self-signed-code-signing.cer"
Export-Certificate -Cert $Cert -FilePath $CerPath -Force | Out-Null

if ($TrustForCurrentUser) {
    $RootPath = "Cert:\CurrentUser\Root\$($Cert.Thumbprint)"
    $PublisherPath = "Cert:\CurrentUser\TrustedPublisher\$($Cert.Thumbprint)"
    if (-not (Test-Path -LiteralPath $RootPath)) {
        Import-Certificate -FilePath $CerPath -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
    }
    if (-not (Test-Path -LiteralPath $PublisherPath)) {
        Import-Certificate -FilePath $CerPath -CertStoreLocation Cert:\CurrentUser\TrustedPublisher | Out-Null
    }
}

$Signature = Set-AuthenticodeSignature `
    -FilePath $Installer `
    -Certificate $Cert `
    -HashAlgorithm SHA256 `
    -TimestampServer $TimestampUrl

if ($Signature.Status -ne "Valid") {
    throw "Signing failed: $($Signature.Status) $($Signature.StatusMessage)"
}

$Hash = Get-FileHash $Installer -Algorithm SHA256
"$($Hash.Hash)  $(Split-Path $Installer -Leaf)" |
    Set-Content -LiteralPath "$Installer.sha256" -Encoding ascii

Write-Host "Signed installer: $Installer"
Write-Host "Publisher: $PublisherName"
Write-Host "Certificate thumbprint: $($Cert.Thumbprint)"
Write-Host "Public certificate exported to: $CerPath"
Write-Host "SHA-256: $($Hash.Hash)"
