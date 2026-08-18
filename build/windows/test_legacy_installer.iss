#ifndef TestAppId
#error TestAppId must be provided by the installer smoke test.
#endif
#ifndef PayloadDir
#error PayloadDir must be provided by the installer smoke test.
#endif
#ifndef OutputDir
#error OutputDir must be provided by the installer smoke test.
#endif

[Setup]
AppId={#TestAppId}
AppName=Deep Live Cam Studio Upgrade Fixture
AppVersion=2.2.1
DefaultDirName={localappdata}\Programs\DeepLiveCamStudioInstallerFixture\2.2.1
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=DeepLiveCamStudio-2.2.1-upgrade-fixture
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
