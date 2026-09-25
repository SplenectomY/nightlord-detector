; Inno Setup script. Built by scripts/build_windows.ps1 when ISCC.exe is on PATH.
;   winget install JRSoftware.InnoSetup
;
; The installer wraps the already-frozen one-file EXE. Players who do not want
; an installer can just copy dist\nightlord-detector.exe.

#define MyAppName "Nightlord Detector"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "SplenectomY"
#define MyAppURL "https://github.com/SplenectomY/nightlord-detector"
#define MyAppExeName "nightlord-detector.exe"

[Setup]
AppId={{B7C3E1A4-9F20-4D6B-8E11-A1B2C3D4E5F6}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Nightlord Detector
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=NightlordDetectorSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Extra shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\nightlord-detector.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
