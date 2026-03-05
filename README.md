# Replay Batch Processor GUI Application

A Windows desktop application for batch processing Warcraft 3 replay files (.w3g) with a user-friendly graphical interface.

## ✨ Features

- **GUI Interface**: Easy-to-use graphical interface for batch processing
- **Player Filtering**: Process replays for a specific player
- **Flexible Paths**: Configure source and output folders
- **Batch Processing**: Process files in batches to avoid timeout issues
- **Dry Run Mode**: Preview changes before executing
- **Progress Logging**: Real-time progress updates in the application
- **Settings Persistence**: Saves your settings between sessions
- **Parser Integration**: Connects to your replay parser at localhost:3000

## � Installation

**Just want to use the app?** → Download `ReplayBatchProcessor.exe` from the [Releases](https://github.com/zeebratootie/twrpg-replay-renamer/releases) page and double-click it. No installation needed!

**Want to modify the code?** → See the Quick Start options below for building from source.

## �🚀 Quick Start (Choose One)

### Option 1: Download Release Executable ⭐ (EASIEST)
**No installation required - just download and run:**
```
1. Download: ReplayBatchProcessor.exe from Releases
2. Double-click the .exe file
3. Application launches instantly
4. Done! ✅
```

**Why this is best:**
- ✓ No Python installation needed
- ✓ No dependencies to install
- ✓ Works immediately out of the box
- ✓ Standalone executable - just download and use

---

### Option 2: Run from Source (For Developers)
**If you cloned the repository:**
```
1. Install Python 3.8+ from https://www.python.org/downloads/
2. Open terminal in replay-batch-app folder
3. pip install -r requirements.txt
4. python replay_batch_gui.py
```

### Option 3: Build Your Own Executable
**Create a standalone .exe:**
```
1. Install Python 3.8+ and dependencies (see Option 2)
2. python build.py
3. Find executable in: dist\ReplayBatchProcessor.exe
4. Double-click to run
```

## 📖 Usage Guide

### First-Time Setup

1. **Enter Player Name**: Type the character/player name you want to filter by (e.g., "crucibles")

2. **Select Source Folder**: Click "Browse..." next to "Source Replay Folder" and select the folder containing your replay files  
   Example: `C:\Users\Admin\Desktop\Git\replay-project\Replay`

3. **Select Output Folder**: Click "Browse..." next to "Output Folder" and select where processed files should be saved  
   Example: `C:\Users\Admin\Desktop\Git\replay-project\Replay\crucibles`

4. **Configure Options**:
   - **Parser URL**: Default is `http://localhost:3000` (change if your parser runs elsewhere)
   - **Batch Size**: How many files to process per batch (default: 50)
   - **Dry Run**: Check to preview changes without creating files
   - **Skip Existing Files**: Skip files that already exist in output folder
   - **No Prompting**: Process all batches without pausing between them

5. **Click "Start Processing"**: The application will begin processing your replays

6. **Review the Log**: Watch the progress in the "Processing Log" section

### ✅ Recommended Dry Run Workflow

For safety, it's recommended to:
1. ✓ Check the "Dry Run" option
2. ✓ Click "Start Processing"
3. ✓ Review the log to see what would be created
4. ✓ Uncheck "Dry Run" to execute for real
5. ✓ Click "Start Processing" again

## ⚙️ Configuration

### Parser Setup

Make sure your replay parser is running and accessible at the URL configured in the app (default: http://localhost:3000).

The parser should have an endpoint: `POST /parse-w3g`

### Output Folder Structure

Files are organized by player class abbreviation:
```
output_folder/
├── am/              (Assassin/Master)
├── merch/           (Merchant)
├── th/              (Ther/Thunder Hero)
├── cpal/            (Crusader/Paladin)
└── ...
```

### Settings

Settings are automatically saved to `settings.json` in the application folder:
- Player name
- Source folder path
- Output folder path
- Parser URL
- Batch size

## 📁 Repository Files

### Python Source Files
- **replay_batch_gui.py** - Main GUI application source code
- **rename_replays.py** - Replay renaming logic module
- **build.py** - Script to build Windows executable using PyInstaller

### Configuration Files
- **requirements.txt** - Python dependencies (requests, pyinstaller)
- **settings.json** - User settings (auto-created on first run, gitignored)
- **.gitignore** - Excludes build artifacts, cache, and user settings

### Documentation
- **README.md** - This file - complete documentation

### Build Output (gitignored)
- **build/** - Build artifacts and temporary files (created by build.py)
- **dist/** - Distribution folder containing:
  - **ReplayBatchProcessor.exe** - Standalone Windows executable (created by build.py)

## Troubleshooting

### "Parser not responding" Error
- Make sure your replay parser is running at the URL configured
- Check that http://localhost:3000 is accessible
- Verify the parser endpoint is `/parse-w3g`

### "No .w3g files found"
- Verify your source folder path is correct
- Make sure the folder contains `.w3g` replay files
- Check folder permissions

### Application Won't Start
- Ensure Python 3.8 or higher is installed
- Try running from command line to see error messages:
  ```bash
  python replay_batch_gui.py
  ```

### Build Fails
- Update pip: `python -m pip install --upgrade pip`
- Reinstall PyInstaller: `pip install --force-reinstall pyinstaller`
- Make sure you have write permissions in the app folder

### Where to Get the Release Executable
- Download from the [Releases](../../releases) page on GitHub
- No need to build it yourself unless you want to modify the code

## Advanced Usage

### Command Line Building

To build with custom options:
```bash
python -m PyInstaller --onefile --windowed --name ReplayBatchProcessor replay_batch_gui.py
```

### Creating a Desktop Shortcut

**For the Release Executable (downloaded .exe):**
1. Right-click on `ReplayBatchProcessor.exe` wherever you saved it
2. Send to → Desktop (create shortcut)
3. Double-click the shortcut to launch

**For the Built Executable (.exe in dist/ folder):**
1. Navigate to the `dist` folder in the repository
2. Right-click on `ReplayBatchProcessor.exe`
3. Send to → Desktop (create shortcut)
4. Double-click the shortcut to launch

## Performance Tips

- **Batch Size**: Increase to 100+ if you have a fast parser
- **No Prompting**: Enable "Process all batches without prompting" for faster processing
- **Multiple Runs**: Process different players sequentially rather than simultaneously

## Requirements

### For Release Executable (Option 1)
- Windows 7 or higher
- Replay parser running at configured URL
- **No Python required!** ✅

### For Building from Source (Options 2-3)
- Windows 7 or higher
- Python 3.8+
- Replay parser running at configured URL
- 100MB free disk space (for executable build)

## License

Same as parent project

## Support

**Quick Start Issues:**
- Using the release executable? Just download it again if it doesn't work
- Check the [Releases](../../releases) page for the latest version

If you encounter issues:
1. Check the "Processing Log" for error messages
2. Verify settings are correct (saved in settings.json)
3. Ensure parser is running
4. Check folder permissions

**For Developers:**
- If building from source, ensure Python 3.8+ is installed
- Run `python replay_batch_gui.py` from command line to see detailed error messages
