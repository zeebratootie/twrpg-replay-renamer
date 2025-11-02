@echo off
REM Install Dependencies and Build Executable
REM Run this file to automatically set up everything

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo Replay Batch Processor - Setup and Build
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Step 1: Checking Python version...
python --version

echo.
echo Step 2: Installing/Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing anyway...
)

echo.
echo Step 3: Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    echo.
    echo Trying alternative installation method...
    python -m pip install requests pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo.
echo Step 4: Building Windows executable...
python build.py
if errorlevel 1 (
    echo ERROR: Build failed!
    echo.
    echo Trying to run directly without executable...
)

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo You can now run the application using:
echo   Option 1: python replay_batch_gui.py
echo   Option 2: Double-click run.bat
echo.
if exist "dist\ReplayBatchProcessor.exe" (
    echo.exe file created successfully!
    echo   Option 3: dist\ReplayBatchProcessor.exe
)
echo.
pause
