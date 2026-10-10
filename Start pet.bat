@echo off
rem starts the claude usage pet without a console window.
rem it looks for python first, and says what to do if there isn't one.
rem (no ( ) blocks below on purpose: a folder name with brackets in it would break them)
set "PET=%~dp0claude_pet.py"

rem the py launcher comes with python from python.org and picks the newest python.
rem <nul so it can't sit waiting for an answer if it wants to ask something
py -c "import sys" <nul >nul 2>nul
if errorlevel 1 goto no_launcher
start "" pyw "%PET%"
exit /b 0

:no_launcher
rem a python on the path. windows has a fake "python" that only points you to the
rem microsoft store, so check this one really runs
python -c "import sys" <nul >nul 2>nul
if errorlevel 1 goto no_python
where pythonw >nul 2>nul
if errorlevel 1 goto with_console
start "" pythonw "%PET%"
exit /b 0

:with_console
start "" /min python "%PET%"
exit /b 0

:no_python
echo.
echo   The Claude usage pet needs Python, and it isn't installed on this computer.
echo.
echo   1. Your browser is opening the Python download page.
echo   2. Download Python from there and run the installer.
echo   3. Then double-click "Start pet.bat" again.
echo.
start "" "https://www.python.org/downloads/windows/"
echo   Press any key to close this window.
pause >nul
exit /b 1
