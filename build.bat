@echo off
setlocal
cd /d "%~dp0"
py -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1
py -m PyInstaller --noconfirm --clean --onefile --windowed --name LumaTint --icon assets\lumatint.ico --add-data "assets;assets" --collect-all customtkinter main.py
if errorlevel 1 exit /b 1
echo.
echo Build complete: dist\LumaTint.exe
pause
