@echo off
setlocal
cd /d "%~dp0"
if not exist "%LOCALAPPDATA%\RockBlockWireless\python-env\Scripts\python.exe" (
  py -3 -m venv "%LOCALAPPDATA%\RockBlockWireless\python-env"
  if errorlevel 1 goto failed
)
"%LOCALAPPDATA%\RockBlockWireless\python-env\Scripts\python.exe" -m pip install -r "%~dp0wireless-requirements.txt"
if errorlevel 1 goto failed
"%LOCALAPPDATA%\RockBlockWireless\python-env\Scripts\python.exe" "%~dp0wireless_setup.py"
if errorlevel 1 goto failed
exit /b 0
:failed
echo Setup failed. Install Python 3.11 or newer with the Windows Python launcher, then check the error above.
pause
exit /b 1
