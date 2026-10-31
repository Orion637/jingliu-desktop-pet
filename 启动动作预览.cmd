@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0.venv\Scripts\pythonw.exe" goto missing
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py" --preview
exit /b 0
:missing
echo Local Python environment is missing. See README.md for setup.
pause
exit /b 1
