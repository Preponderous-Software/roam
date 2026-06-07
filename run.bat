@echo off
REM Usage: double-click this file, or run "run.bat" from a command prompt.
REM Launches Roam using the Python interpreter on your PATH.
REM Run install.ps1 first if you have not installed the dependencies yet.

REM Move to the directory this script lives in so relative paths resolve.
cd /d "%~dp0"

REM Prefer the "python" command; fall back to the "py" launcher.
REM Use && after each "where" so the set runs only on success — this avoids
REM the %errorlevel%-inside-a-block parse-time expansion pitfall.
set "ROAM_PYTHON="
where python >nul 2>nul && set "ROAM_PYTHON=python"
if not defined ROAM_PYTHON where py >nul 2>nul && set "ROAM_PYTHON=py"

if not defined ROAM_PYTHON (
    echo Python could not be found on your PATH.
    echo Run install.ps1 first, or install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

"%ROAM_PYTHON%" src\roam.py
if errorlevel 1 (
    echo.
    echo Roam exited with an error. See the messages above for details.
    pause
)
