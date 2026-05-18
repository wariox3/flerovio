@echo off
REM Build completo de Flerovio para Windows.
REM
REM Requisitos previos en la maquina:
REM   - Python 3.11+ con el venv en %USERPROFILE%\.venvs\flerovio
REM   - pip install -e ".[dev]"  (incluye pyinstaller)
REM   - Inno Setup 6+ instalado en su ruta por defecto
REM
REM Uso (desde la raiz del repo):
REM   packaging\windows\empaquetar.bat

setlocal enableextensions
cd /d "%~dp0\..\.."

set VENV=%USERPROFILE%\.venvs\flerovio
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

echo === Limpiando build anterior ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist packaging\windows\Output rmdir /s /q packaging\windows\Output

echo === PyInstaller ===
call "%VENV%\Scripts\activate.bat"
pyinstaller packaging\windows\flerovio.spec --noconfirm
if errorlevel 1 (
    echo PyInstaller fallo.
    exit /b 1
)

echo === Inno Setup ===
%ISCC% packaging\windows\flerovio.iss
if errorlevel 1 (
    echo Inno Setup fallo.
    exit /b 1
)

echo === Listo ===
echo Instalador en: packaging\windows\Output\
dir /b packaging\windows\Output
