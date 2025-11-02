# Quick Setup Guide

## For Easiest Use: Build the Executable

### Step 1: Install Dependencies
Open Command Prompt or PowerShell and run:
```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
pip install -r requirements.txt
```

### Step 2: Build Executable
```
python build.py
```

This will create `dist\ReplayBatchProcessor.exe` - a standalone executable that doesn't require Python!

### Step 3: Run the App
Either:
- **Option A**: Double-click `dist\ReplayBatchProcessor.exe`
- **Option B**: Double-click `run.bat` in the replay-batch-app folder
- **Option C**: From command line: `python replay_batch_gui.py`

## First Time Running

1. **Start the application** using one of the methods above
2. **Enter player name**: e.g., "crucibles"
3. **Browse source folder**: Select your replay folder (e.g., `C:\Users\Admin\Desktop\Git\replay-project\Replay`)
4. **Browse output folder**: Select where to save processed replays (e.g., `C:\Users\Admin\Desktop\Git\replay-project\Replay\crucibles`)
5. **Check "Dry Run"** to preview first
6. **Click "Start Processing"**
7. **Review the log** to see what would happen
8. **Uncheck "Dry Run"** to execute for real
9. **Click "Start Processing"** again

## Troubleshooting

### Python Not Found
Install Python from https://www.python.org/downloads/
Make sure to check "Add Python to PATH"

### Build Fails
```
pip install --upgrade pip
pip install --force-reinstall pyinstaller
python build.py
```

### Parser Not Responding
Make sure your replay parser is running at http://localhost:3000

### GUI Won't Open
From command line, run:
```
python replay_batch_gui.py
```
This will show error messages that help diagnose the issue.

## Creating a Desktop Shortcut

### For the Executable (.exe)
1. Find `ReplayBatchProcessor.exe` in the `dist` folder
2. Right-click it → Send to → Desktop (create shortcut)
3. Double-click the shortcut to run

### For the Python Script
1. Find `run.bat` in the `replay-batch-app` folder
2. Right-click it → Send to → Desktop (create shortcut)
3. Double-click the shortcut to run

## Files Created

```
replay-batch-app/
├── replay_batch_gui.py      ← Main GUI application (Python)
├── run.py                   ← Python launcher
├── run.bat                  ← Windows launcher (double-click to run)
├── build.py                 ← Script to build executable
├── requirements.txt         ← Python dependencies
├── settings.json            ← Your saved settings (auto-created)
├── README.md                ← Full documentation
├── SETUP.md                 ← This file
└── dist/
    └── ReplayBatchProcessor.exe  ← Built executable (created by build.py)
```

## Next Steps

1. Run the app using `run.bat` or the executable
2. Configure your player name and folders
3. Start with a "Dry Run" to test
4. Process your replays!

For more details, see `README.md`
