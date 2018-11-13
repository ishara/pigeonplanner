; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Pigeon Planner"
#define MyAppURL "http://www.pigeonplanner.com"
#define MyAppVersion GetFileVersion("..\dist\pigeonplanner.exe")
#define MyVersion() ParseVersion("..\dist\pigeonplanner.exe", Local[0], Local[1], Local[2], Local[3]), Str(Local[0]) + "." + Str(Local[1]) + "." + Str(Local[2]);

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{3F372268-0B73-46A8-9824-47849B983480}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
VersionInfoTextVersion={#MyAppVersion}
AppPublisher=Timo Vanwynsberghe
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=..\COPYING
OutputDir=.
OutputBaseFilename=Pigeon_Planner-{#MyVersion()}
SetupIconFile=pigeonplanner.ico
Compression=lzma
SolidCompression=yes

[Languages]
Name: english; MessagesFile: compiler:Default.isl
Name: czech; MessagesFile: compiler:Languages\Czech.isl
Name: dutch; MessagesFile: compiler:Languages\Dutch.isl
Name: french; MessagesFile: compiler:Languages\French.isl
Name: german; MessagesFile: compiler:Languages\German.isl
Name: hebrew; MessagesFile: compiler:Languages\Hebrew.isl
Name: hungarian; MessagesFile: compiler:Languages\Hungarian.isl
Name: portuguese; MessagesFile: compiler:Languages\Portuguese.isl
Name: russian; MessagesFile: compiler:Languages\Russian.isl
Name: spanish; MessagesFile: compiler:Languages\Spanish.isl
Name: ukrainian; MessagesFile: compiler:Languages\Ukrainian.isl

[Tasks]
Name: desktopicon; Description: {cm:CreateDesktopIcon}; GroupDescription: {cm:AdditionalIcons}
Name: quicklaunchicon; Description: {cm:CreateQuickLaunchIcon}; GroupDescription: {cm:AdditionalIcons}; Flags: unchecked

[Files]
Source: ..\dist\pigeonplanner.exe; DestDir: {app}; Flags: ignoreversion
Source: ..\dist\*; DestDir: {app}; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Code]
var
  Version: TWindowsVersion;
  uninstaller: String;
  ErrorCode: Integer;

function InitializeSetup(): Boolean;

begin

  Result := true;
  GetWindowsVersionEx(Version);

  if RegKeyExists(HKEY_LOCAL_MACHINE,  'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{3F372268-0B73-46A8-9824-47849B983480}_is1') then
  begin
   MsgBox('Setup needs to uninstall the previous version of Pigeon Planner. All your data will be saved automatically.',
           mbInformation, MB_OK);

      RegQueryStringValue(HKEY_LOCAL_MACHINE,
            'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{3F372268-0B73-46A8-9824-47849B983480}_is1',
            'UninstallString', uninstaller);

      //ShellExec('runas', uninstaller, '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
      //use above statement if extra level security is required usually it is not req
      ShellExec('open', uninstaller, '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);

      if RegKeyExists(HKEY_LOCAL_MACHINE,  'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{3F372268-0B73-46A8-9824-47849B983480}_is1') then
        begin
          Result := false;
        end
      else
        begin
          Result := true;
        end
  end
end;

[Icons]
Name: {group}\Pigeon Planner; Filename: {app}\pigeonplanner.exe; WorkingDir: {app}
Name: {group}\Pigeon Planner Database Tool; Filename: {app}\pigeonplanner-db.exe; WorkingDir: {app}
Name: {group}\{cm:ProgramOnTheWeb,Pigeon Planner}; Filename: http://www.pigeonplanner.com
Name: {group}\{cm:UninstallProgram,Pigeon Planner}; Filename: {uninstallexe}
Name: {commondesktop}\Pigeon Planner; Filename: {app}\pigeonplanner.exe; WorkingDir: {app}; Tasks: desktopicon

[Run]
Filename: {app}\pigeonplanner.exe; Description: {cm:LaunchProgram,Pigeon Planner}; Flags: nowait postinstall skipifsilent
