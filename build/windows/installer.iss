#define AppName "Deep Live Cam Studio"
#ifndef AppVersion
#define AppVersion "2.1.8"
#endif
#ifndef DistDir
#define DistDir "..\..\dist\DeepLiveCamStudio"
#endif
#ifndef OutputDir
#define OutputDir "installer"
#endif
#ifndef RepoRoot
#define RepoRoot "..\.."
#endif

[Setup]
AppId={{7B7D33BB-6B98-48D2-A8D5-31D6D6E53A08}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Deep-Live-Cam contributors
AppPublisherURL=https://github.com/hacksider/Deep-Live-Cam
AppSupportURL=https://github.com/hacksider/Deep-Live-Cam/issues
AppUpdatesURL=https://github.com/hacksider/Deep-Live-Cam/releases
DefaultDirName={localappdata}\Programs\DeepLiveCamStudio\{#AppVersion}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=DeepLiveCamStudio-{#AppVersion}-x64-setup
SetupIconFile={#RepoRoot}\build\windows\assets\Logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\DeepLiveCamStudio.exe
LicenseFile={#DistDir}\LICENSE
WizardImageFile={#RepoRoot}\build\windows\assets\WizardImage.bmp
WizardSmallImageFile={#RepoRoot}\build\windows\assets\WizardSmallImage.bmp
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\DeepLiveCamStudio.exe"; WorkingDir: "{app}"; IconFilename: "{app}\DeepLiveCamStudio.exe"
Name: "{group}\Download and Verify Models"; Filename: "{app}\DeepLiveCamStudioCLI.exe"; Parameters: "--download-models"; WorkingDir: "{app}"; IconFilename: "{app}\DeepLiveCamStudioCLI.exe"
Name: "{group}\Compliance Notes"; Filename: "{app}\COMPLIANCE.md"
Name: "{group}\Third Party Notices"; Filename: "{app}\THIRD_PARTY_NOTICES.md"
Name: "{group}\Bundled Binary Obligations"; Filename: "{app}\LICENSES\BUNDLED_BINARY_OBLIGATIONS.md"
Name: "{group}\OBS Virtual Camera Guide"; Filename: "{app}\docs\OBS_VIRTUAL_CAMERA.md"
Name: "{group}\Release Report"; Filename: "{app}\RELEASE_REPORT.md"
Name: "{group}\Release Source Preparation"; Filename: "{app}\RELEASE_SOURCE_PREP.md"
Name: "{group}\Model Download Verification"; Filename: "{app}\MODEL_DOWNLOAD_VERIFICATION.md"
Name: "{group}\Processing Verification"; Filename: "{app}\PROCESSING_VERIFICATION.md"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\DeepLiveCamStudio.exe"; WorkingDir: "{app}"; IconFilename: "{app}\DeepLiveCamStudio.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DeepLiveCamStudio.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ModelsDir: string;
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    ModelsDir := ExpandConstant('{localappdata}\DeepLiveCamStudio\models');
    if DirExists(ModelsDir) and not UninstallSilent then
    begin
      if MsgBox('Remove downloaded Deep Live Cam Studio model files from ' + ModelsDir + '?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        Exec(ExpandConstant('{cmd}'), '/C rmdir /S /Q "' + ModelsDir + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end;
    end;
  end;
end;
