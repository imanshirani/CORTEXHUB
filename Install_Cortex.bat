@echo off
cd /d "%~dp0"
title Cortex Hub - Install requirements

where python >nul 2>&1
if errorlevel 1 (
    echo Python was not found on PATH.
    echo Install Python 3.10 or newer and enable "Add python.exe to PATH".
    pause
    exit /b 1
)

echo Using:
python --version
echo.

echo Installing packages from requirements.txt ...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo pip upgrade failed.
    pause
    exit /b 1
)

python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo Install failed.
    pause
    exit /b 1
)

echo.
echo Done. Run Start_Cortex.bat to open Cortex Hub.
pause
