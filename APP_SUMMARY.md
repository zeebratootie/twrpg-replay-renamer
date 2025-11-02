# Replay Batch Processor - Application Summary

## What Was Created

A complete Windows GUI application for batch processing Warcraft 3 replay files with the following features:

### Features
✓ **Easy GUI Interface** - No command line needed
✓ **Player Name Input** - Filter replays by player name
✓ **Folder Selection** - Browse and select source/output folders
✓ **Batch Processing** - Process files in configurable batches
✓ **Dry Run Mode** - Preview changes before executing
✓ **Real-time Logging** - Watch progress as files are processed
✓ **Settings Persistence** - Your settings are saved automatically
✓ **Parser Integration** - Configurable parser URL
✓ **Windows Executable** - Can be packaged as a standalone .exe

## File Structure

```
replay-batch-app/
├── replay_batch_gui.py      - Main GUI application (Python)
├── build.py                 - Script to create Windows .exe
├── run.py                   - Python launcher
├── run.bat                  - Windows batch launcher (double-click)
├── requirements.txt         - Python dependencies
├── README.md                - Full documentation
├── SETUP.md                 - Quick setup guide
├── settings.json            - Saved settings (auto-created)
└── dist/                    - Output folder for built .exe
    └── ReplayBatchProcessor.exe  (created after running build.py)
```

## Quick Start Options

### Option 1: Easy - Use the .bat Launcher (Recommended)
```
1. Double-click: replay-batch-app\run.bat
2. Enter your settings
3. Click "Start Processing"
```

### Option 2: Build a Standalone .exe
```
1. Open Command Prompt
2. cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
3. pip install -r requirements.txt
4. python build.py
5. Double-click: dist\ReplayBatchProcessor.exe
```

### Option 3: Run Python Directly
```
1. Open Command Prompt
2. cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
3. pip install -r requirements.txt
4. python replay_batch_gui.py
```

## How to Use the App

1. **Start the Application**
   - Double-click `run.bat` or the .exe

2. **Enter Player Name**
   - Type the player/character name (e.g., "crucibles")

3. **Set Folder Paths**
   - Source Folder: Where your replay files are located
   - Output Folder: Where processed files will be saved

4. **Configure Parser**
   - Default: http://localhost:3000
   - Change if your parser runs elsewhere

5. **Set Batch Size** (optional)
   - Default: 50 files per batch
   - Increase for faster processing

6. **Preview with Dry Run**
   - Check "Dry Run (preview without creating files)"
   - Click "Start Processing"
   - Review the log to see what would happen

7. **Execute for Real**
   - Uncheck "Dry Run"
   - Click "Start Processing"
   - Files will be created in the output folder

## Key GUI Features

- **Real-time Progress Log** - Watch processing in real-time
- **Error Handling** - Graceful error messages if something goes wrong
- **Input Validation** - Prevents invalid folder paths or batch sizes
- **Non-blocking UI** - App stays responsive during processing
- **Threading** - Long operations run in background
- **Settings Saved** - Your preferences persist between sessions

## Building the Executable

The application can be converted to a standalone Windows .exe file using PyInstaller:

```
python build.py
```

This creates: `dist/ReplayBatchProcessor.exe`

The .exe:
- Runs without Python installed
- Contains all dependencies
- Can be run from anywhere
- Can be put on a USB drive
- Can have a desktop shortcut

## System Requirements

- **For .exe**: Windows 7 or higher (no Python needed)
- **For Python**: Python 3.8+ installed
- **General**: Replay parser running at configured URL
- **Storage**: 100MB+ free space

## Default Settings

- Player Name: (empty - you set it)
- Source Folder: (empty - you choose)
- Output Folder: (empty - you choose)
- Parser URL: http://localhost:3000
- Batch Size: 50
- Dry Run: Enabled (for safety)

## Troubleshooting

### GUI Won't Open
- Ensure Python 3.8+ is installed
- Try running from command line to see error messages
- Install dependencies: `pip install -r requirements.txt`

### Build Fails
- Update pip: `python -m pip install --upgrade pip`
- Reinstall PyInstaller: `pip install --force-reinstall pyinstaller`

### Parser Not Connecting
- Verify parser is running at http://localhost:3000
- Check the URL in the GUI settings
- Make sure port 3000 is accessible

### Folder Not Found
- Verify the folder path is correct
- Ensure you have read/write permissions
- Check that the folder exists

## Next Steps

1. Choose your preferred method to launch (bat, exe, or python)
2. Install dependencies if needed: `pip install -r requirements.txt`
3. Run the application
4. Test with a Dry Run first
5. Process your replays!

## Support Files

- **README.md** - Comprehensive documentation
- **SETUP.md** - Detailed setup instructions
- **requirements.txt** - Python packages needed
- **build.py** - Executable builder

For detailed information, see `README.md` in the replay-batch-app folder.
