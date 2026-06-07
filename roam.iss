; Inno Setup script for Roam — wraps the PyInstaller build into a setup wizard.
;
; Build (after `pyinstaller roam.spec` has produced dist\Roam\):
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" roam.iss
; Produces installer-output\RoamSetup.exe.
;
; The version can be overridden:  ISCC.exe /DMyAppVersion=1.2.3 roam.iss

#ifndef MyAppVersion
  #define MyAppVersion "0.8.0"
#endif
#define MyAppName "Roam"
#define MyAppExeName "Roam.exe"
#define MyAppPublisher "Preponderous Software"
#define MyAppURL "https://github.com/Preponderous-Software/roam"

[Setup]
; A stable, unique identifier so upgrades and uninstall work across versions.
AppId={{A3F1C2E4-5B6D-4E7F-8A90-1234567890AB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=installer-output
OutputBaseFilename=RoamSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Install into the real Program Files (64-bit) so the standalone build lives
; with other applications. User data is stored under %APPDATA%\Roam, so the
; install directory can be read-only.
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
#if FileExists("src\media\icon.ico")
SetupIconFile=src\media\icon.ico
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; The entire one-folder PyInstaller output.
Source: "dist\Roam\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
