#define AppName "Deep Live Cam Studio"
#ifndef AppVersion
#define AppVersion "2.2.3"
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
#ifndef AppId
#define AppId "{{7B7D33BB-6B98-48D2-A8D5-31D6D6E53A08}"
#endif
#ifndef AppIdRegistryValue
#define AppIdRegistryValue "{7B7D33BB-6B98-48D2-A8D5-31D6D6E53A08}"
#endif
#ifndef OutputBaseFilename
#define OutputBaseFilename "DeepLiveCamStudio-" + AppVersion + "-x64-setup"
#endif

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=CRSD-Lau and Deep-Live-Cam contributors
AppPublisherURL=https://github.com/CRSD-Lau/deep-live-cam
AppSupportURL=https://github.com/CRSD-Lau/deep-live-cam/issues
AppUpdatesURL=https://github.com/CRSD-Lau/deep-live-cam/releases
DefaultDirName={localappdata}\Programs\DeepLiveCamStudio
UsePreviousAppDir=no
DisableDirPage=yes
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile={#RepoRoot}\build\windows\assets\Logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no
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

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\docs"
Type: filesandordirs; Name: "{app}\LICENSES"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
const
  ActiveAppId = '{#AppIdRegistryValue}';
  UninstallRegistryRoot =
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\';

var
  PreviousInstallDir: string;
  PreviousUninstaller: string;
  PreviousInstallationLoaded: Boolean;
  MigrationCompleted: Boolean;

function NormalizeDirectory(Path: string): string;
begin
  if Path = '' then
    Result := ''
  else
    Result := RemoveBackslashUnlessRoot(ExpandFileName(Path));
end;

function ExtractCommandExecutable(CommandLine: string): string;
var
  I: Integer;
begin
  Result := '';
  CommandLine := Trim(CommandLine);
  if CommandLine = '' then
    Exit;

  if CommandLine[1] = '"' then
  begin
    I := 2;
    while (I <= Length(CommandLine)) and (CommandLine[I] <> '"') do
      I := I + 1;
    if I <= Length(CommandLine) then
      Result := Copy(CommandLine, 2, I - 2);
  end
  else
  begin
    I := Pos(' ', CommandLine);
    if I = 0 then
      Result := CommandLine
    else
      Result := Copy(CommandLine, 1, I - 1);
  end;
end;

function FindUninstaller(InstallDir: string): string;
var
  FindRec: TFindRec;
begin
  Result := '';
  if (InstallDir = '') or not DirExists(InstallDir) then
    Exit;

  if FindFirst(AddBackslash(InstallDir) + 'unins*.exe', FindRec) then
  begin
    try
      repeat
        if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY = 0 then
        begin
          Result := AddBackslash(InstallDir) + FindRec.Name;
          Exit;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

procedure LoadPreviousInstallation;
var
  RegistryKey: string;
  Value: string;
begin
  if PreviousInstallationLoaded then
    Exit;

  PreviousInstallationLoaded := True;
  RegistryKey := UninstallRegistryRoot + ActiveAppId + '_is1';

  if RegQueryStringValue(HKCU, RegistryKey, 'InstallLocation', Value) then
    PreviousInstallDir := NormalizeDirectory(Value);

  if RegQueryStringValue(HKCU, RegistryKey, 'UninstallString', Value) then
    PreviousUninstaller := ExtractCommandExecutable(Value);

  if (PreviousInstallDir = '') and (PreviousUninstaller <> '') then
    PreviousInstallDir := NormalizeDirectory(ExtractFileDir(PreviousUninstaller));

  if (PreviousUninstaller = '') and (PreviousInstallDir <> '') then
    PreviousUninstaller := FindUninstaller(PreviousInstallDir);

  if (PreviousUninstaller <> '') and
     (LowerCase(NormalizeDirectory(ExtractFileDir(PreviousUninstaller))) <>
      LowerCase(PreviousInstallDir)) then
  begin
    Log('Ignoring an uninstaller outside the registered installation directory.');
    PreviousUninstaller := '';
  end;
end;

function InitializeSetup: Boolean;
begin
  LoadPreviousInstallation;
  Result := True;
end;

procedure RegisterExtraCloseApplicationsResources;
begin
  LoadPreviousInstallation;
  if (PreviousInstallDir <> '') and
     FileExists(AddBackslash(PreviousInstallDir) + 'DeepLiveCamStudio.exe') then
  begin
    RegisterExtraCloseApplicationsResource(
      False, AddBackslash(PreviousInstallDir) + 'DeepLiveCamStudio.exe');
  end;
end;

function IsVersionDirectoryName(Name: string): Boolean;
var
  I: Integer;
  DotCount: Integer;
  LastWasDot: Boolean;
begin
  Result := False;
  DotCount := 0;
  LastWasDot := True;

  for I := 1 to Length(Name) do
  begin
    if Name[I] = '.' then
    begin
      if LastWasDot then
        Exit;
      DotCount := DotCount + 1;
      LastWasDot := True;
    end
    else if (Name[I] >= '0') and (Name[I] <= '9') then
      LastWasDot := False
    else
      Exit;
  end;

  Result := (DotCount = 2) and not LastWasDot;
end;

function HasLegacyInstallationMarker(Directory: string): Boolean;
var
  FindRec: TFindRec;
begin
  Result := FileExists(AddBackslash(Directory) + 'DeepLiveCamStudio.exe');
  if Result then
    Exit;

  if FindFirst(AddBackslash(Directory) + 'unins*.exe', FindRec) then
  begin
    try
      Result := FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY = 0;
    finally
      FindClose(FindRec);
    end;
  end;
end;

procedure RemoveLegacyVersionDirectories;
var
  InstallRoot: string;
  LegacyDir: string;
  FindRec: TFindRec;
begin
  InstallRoot := NormalizeDirectory(ExpandConstant('{app}'));
  if not DirExists(InstallRoot) then
    Exit;

  if FindFirst(AddBackslash(InstallRoot) + '*', FindRec) then
  begin
    try
      repeat
        if (FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0) and
           (FindRec.Attributes and FILE_ATTRIBUTE_REPARSE_POINT = 0) and
           IsVersionDirectoryName(FindRec.Name) then
        begin
          LegacyDir := AddBackslash(InstallRoot) + FindRec.Name;
          if HasLegacyInstallationMarker(LegacyDir) then
          begin
            Log('Removing orphaned legacy installation directory: ' + LegacyDir);
            if not DelTree(LegacyDir, True, True, True) then
              RaiseException(
                'Could not remove an older Deep Live Cam Studio installation at ' +
                LegacyDir + '. Close the app and run Setup again.');
          end;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

procedure MigratePreviousInstallation;
var
  ResultCode: Integer;
  CurrentInstallDir: string;
begin
  if MigrationCompleted then
    Exit;
  MigrationCompleted := True;

  LoadPreviousInstallation;
  CurrentInstallDir := NormalizeDirectory(ExpandConstant('{app}'));

  if (PreviousInstallDir <> '') and
     (LowerCase(PreviousInstallDir) <> LowerCase(CurrentInstallDir)) then
  begin
    if (PreviousUninstaller = '') or not FileExists(PreviousUninstaller) then
      RaiseException(
        'The previous Deep Live Cam Studio installation could not be migrated ' +
        'because its uninstaller is missing. Reinstall the previous version or ' +
        'remove it from Windows Installed apps, then run Setup again.');

    Log('Migrating previous installation from ' + PreviousInstallDir +
      ' to ' + CurrentInstallDir + '.');
    if not Exec(
      PreviousUninstaller,
      '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART',
      PreviousInstallDir,
      SW_HIDE,
      ewWaitUntilTerminated,
      ResultCode) or (ResultCode <> 0) then
    begin
      RaiseException(
        'Could not remove the previous Deep Live Cam Studio installation. ' +
        'Close the app and run Setup again.');
    end;

    if DirExists(PreviousInstallDir) and
       not DelTree(PreviousInstallDir, True, True, True) then
    begin
      RaiseException(
        'The previous installation directory is still in use: ' +
        PreviousInstallDir + '. Close the app and run Setup again.');
    end;
  end;

  RemoveLegacyVersionDirectories;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    MigratePreviousInstallation;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ModelsDir: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    ModelsDir := ExpandConstant('{localappdata}\DeepLiveCamStudio\models');
    if DirExists(ModelsDir) and not UninstallSilent then
    begin
      if MsgBox('Remove downloaded Deep Live Cam Studio model files from ' + ModelsDir + '?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(ModelsDir, True, True, True);
      end;
    end;
  end;
end;
