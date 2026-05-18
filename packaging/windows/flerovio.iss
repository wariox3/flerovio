; Script de Inno Setup para empaquetar Flerovio en Windows.
;
; Requisitos en la máquina de build:
;   - Inno Setup 6+ (https://jrsoftware.org/isdl.php)
;   - Haber corrido antes: pyinstaller packaging/windows/flerovio.spec
;     (genera dist/flerovio/ con flerovio.exe)
;
; Uso:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\windows\flerovio.iss
;
; Salida: packaging/windows/Output/flerovio-<versión>-setup.exe

#define AppName "Flerovio"
#define AppPublisher "Semantica"
#define AppExeName "flerovio.exe"
#define AppVersion "0.1.0"  ; mantener sincronizado con src/flerovio/__init__.py

[Setup]
AppId={{2B7A0F3D-6E12-4F5C-9D8A-8B7E4F2A9C10}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=flerovio-{#AppVersion}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
; Cierra Flerovio si está corriendo durante el update, y lo reabre al terminar.
CloseApplications=yes
RestartApplications=yes
; Idioma del instalador
ShowLanguageDialog=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Iconos adicionales:"; Flags: unchecked

[Files]
; Empaqueta toda la carpeta generada por PyInstaller.
Source: "..\..\dist\flerovio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Opción de lanzar Flerovio al terminar el instalador.
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName}"; Flags: nowait postinstall skipifsilent
