# Replay Batch Processor GUI Application

A Windows desktop application for batch processing Warcraft 3 replay files (.w3g) with a user-friendly graphical interface.

## Features

- **GUI Interface**: Easy-to-use graphical interface for batch processing
- **Player Filtering**: Process replays for a specific player
- **Flexible Paths**: Configure source and output folders
- **Batch Processing**: Process files in batches to avoid timeout issues
- **Dry Run Mode**: Preview changes before executing
- **Progress Logging**: Real-time progress updates in the application
- **Settings Persistence**: Saves your settings between sessions
- **Parser Integration**: Connects to your replay parser at localhost:3000

## Installation

### Option 1: Use Pre-built Executable (Easiest)

If you have the pre-built executable (`ReplayBatchProcessor.exe`), simply:
1. Double-click the .exe file
2. No Python installation required!

### Option 2: Build from Source

1. **Install Python 3.8+** (if not already installed)
   - Download from https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Install dependencies**:
   ```bash
   cd replay-batch-app
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python replay_batch_gui.py
   ```

4. **Build executable** (optional):
   ```bash
   python build.py
   ```
   This creates `dist/ReplayBatchProcessor.exe` which can be run without Python.

## Usage

### Quick Start

1. **Enter Player Name**: Type the character/player name you want to filter by (e.g., "crucibles")

2. **Select Source Folder**: Click "Browse..." next to "Source Replay Folder" and select the folder containing your replay files (e.g., `C:\path\to\Replay`)

3. **Select Output Folder**: Click "Browse..." next to "Output Folder" and select where processed files should be saved (e.g., `C:\path\to\Replay\crucibles`)

4. **Configure Options**:
   - **Parser URL**: Default is `http://localhost:3000` (change if your parser runs elsewhere)
   - **Batch Size**: How many files to process per batch (default: 50)
   - **Dry Run**: Check to preview changes without creating files
   - **Skip Existing Files**: Skip files that already exist in output folder
   - **No Prompting**: Process all batches without pausing between them

5. **Click "Start Processing"**: The application will begin processing your replays

6. **Review the Log**: Watch the progress in the "Processing Log" section

### Dry Run Workflow

For safety, it's recommended to:
1. Check the "Dry Run" option
2. Click "Start Processing"
3. Review the log to see what would be created
4. Uncheck "Dry Run" to execute for real
5. Click "Start Processing" again

## Configuration

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

## Files

- `replay_batch_gui.py` - Main GUI application
- `build.py` - Script to build Windows executable
- `requirements.txt` - Python dependencies
- `settings.json` - Automatically created, stores your preferences
- `dist/ReplayBatchProcessor.exe` - Built executable (created by build.py)

## Advanced Usage

### Command Line Building

To build with custom options:
```bash
python -m PyInstaller --onefile --windowed --name ReplayBatchProcessor replay_batch_gui.py
```

### Creating a Desktop Shortcut

After building the executable:
1. Right-click on `ReplayBatchProcessor.exe`
2. Send to → Desktop (create shortcut)
3. Double-click the shortcut to launch the app

## Performance Tips

- **Batch Size**: Increase to 100+ if you have a fast parser
- **No Prompting**: Enable "Process all batches without prompting" for faster processing
- **Multiple Runs**: Process different players sequentially rather than simultaneously

## Requirements

- Windows 7 or higher
- Replay parser running at configured URL
- Python 3.8+ (only if running from source)
- 100MB free disk space (for executable build)

## License

Same as parent project

## Support

If you encounter issues:
1. Check the "Processing Log" for error messages
2. Verify settings are correct (saved in settings.json)
3. Ensure parser is running
4. Check folder permissions
# twrpg-replay-renamer
# twrpg-replay-renamer
