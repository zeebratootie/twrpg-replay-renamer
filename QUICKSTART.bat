@echo off
REM Quick Setup - Simpler alternative to INSTALL.bat
REM Just installs dependencies and runs the app, no build

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo Replay Batch Processor - Quick Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install from: https://www.python.org/downloads/
    echo Check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Checking Python installation...
python --version

echo.
echo Installing required package (requests)...
python -m pip install --quiet requests

if errorlevel 1 (
    echo Failed with pip, trying alternative...
    python -m pip install requests
)

echo.
echo ============================================================
echo Setup Complete! Starting application...
echo ============================================================
echo.

python replay_batch_gui.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start.
    echo.
    echo Try:
    echo   1. Close this window
    echo   2. Run: python replay_batch_gui.py (from command prompt)
    echo.
    pause
)
