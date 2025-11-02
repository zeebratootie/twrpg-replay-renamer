@echo off
REM Replay Batch Processor - Windows Launcher
REM This file launches the GUI application

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Try executable first if it exists
if exist "dist\ReplayBatchProcessor.exe" (
    start "" "dist\ReplayBatchProcessor.exe"
    exit /b 0
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Install dependencies if needed (silent)
echo Checking dependencies...
python -m pip install -q requests 2>nul

REM Run the application
echo Starting Replay Batch Processor...
python replay_batch_gui.py

if errorlevel 1 (
    echo.
    echo The application encountered an error.
    echo Please try the following:
    echo   1. Make sure Python 3.8+ is installed
    echo   2. Run INSTALL.bat to install dependencies
    echo   3. Check rename_replays.py is in the parent folder
    echo.
    pause
)
