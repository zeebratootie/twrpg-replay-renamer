# Configuration Guide - Replay Batch Processor

## Overview

The Replay Batch Processor now supports persistent configuration through `config.ini` and date-based file filtering. This allows you to:

1. **Save settings** between sessions without retyping parameters
2. **Filter files** by date range to process only replays from specific time periods
3. **Automate** the setup with pre-configured values
4. **Log processing** details for troubleshooting

## Configuration File (config.ini)

The application automatically creates a `config.ini` file on first run with default values. You can modify this file to customize your settings.

### File Location
```
replay-batch-app/config.ini
```

### Configuration Sections

#### [SETTINGS]

All configuration options are under the `[SETTINGS]` section:

```ini
[SETTINGS]
# Input and Output Folders
input_folder = ./input
output_folder = ./output

# Parser Configuration
parser_url = http://localhost:3000

# Processing Options
batch_size = 500
parallel_threads = 8

# Date Filtering
date_from = 
date_to = 

# Logging
log_level = INFO

# GUI/Processing Options
dry_run = true
skip_existing = true
```

### Configuration Options

| Option | Type | Description | Example |
|--------|------|-------------|---------|
| `input_folder` | Path | Source folder with replay files | `./input` or `C:\Replays` |
| `output_folder` | Path | Destination folder for processed files | `./output` |
| `parser_url` | URL | URL where replay parser is running | `http://localhost:3000` |
| `batch_size` | Integer | Files to process per batch (higher = faster) | `500` |
| `parallel_threads` | Integer | Concurrent threads for processing (4-16) | `8` |
| `date_from` | Date | Process files from this date (YYYY-MM-DD) | `2024-01-01` (optional) |
| `date_to` | Date | Process files until this date (YYYY-MM-DD) | `2024-12-31` (optional) |
| `log_level` | String | Logging verbosity: DEBUG, INFO, WARNING, ERROR | `INFO` |
| `dry_run` | Boolean | Start in preview mode (true/false) | `true` |
| `skip_existing` | Boolean | Skip files that exist in output (true/false) | `true` |

## Date Filtering

The application can filter files by date range. Files are checked against the date filter BEFORE processing, saving time and resources.

### How Date Filtering Works

1. **Date Detection Priority**:
   - First: Tries to extract date from filename (patterns like YYYY-MM-DD, MM-DD-YYYY, YYYYMMDD)
   - Second: Uses file modification timestamp

2. **Filtering Logic**:
   - If `date_from` is set, files BEFORE that date are skipped
   - If `date_to` is set, files AFTER that date are skipped
   - Both are inclusive (dates at boundaries ARE processed)
   - Leave both empty to disable date filtering

### Examples

#### Example 1: Process January 2024 Only
```ini
date_from = 2024-01-01
date_to = 2024-01-31
```

#### Example 2: Process Recent Files
```ini
date_from = 2024-06-01
date_to = 
```

#### Example 3: Disable Date Filtering
```ini
date_from = 
date_to = 
```

### Filename Date Formats

The date filter can recognize these patterns in filenames:

- `YYYY-MM-DD` (e.g., `replay-2024-01-15.w3g`)
- `MM-DD-YYYY` (e.g., `replay-01-15-2024.w3g`)
- `YYYYMMDD` (e.g., `replay20240115.w3g`)

If no date is found in the filename, the file's modification timestamp is used.

## Logging

The application creates a log file `replay_processor.log` with detailed information about:
- Configuration loaded
- Files skipped due to date filter
- Files processed
- Errors and warnings
- Processing speed

### Log Levels

| Level | Description | Use When |
|-------|-------------|----------|
| `DEBUG` | Detailed information for debugging | Troubleshooting issues |
| `INFO` | General information (default) | Normal operation |
| `WARNING` | Warning messages | Something unexpected happened |
| `ERROR` | Error messages | Something failed |
| `CRITICAL` | Critical errors | System failure |

### Viewing Logs

```bash
# View real-time logs (Windows)
type replay_processor.log

# View last 50 lines
type replay_processor.log | tail -50

# Search for errors
find . -name "*.log" -exec grep -l "ERROR" {} \;
```

## Using via GUI

1. **Load Settings**: Settings are automatically loaded from `config.ini` when the app starts

2. **Override Settings**: Change any field in the GUI and click "Start Processing"
   - GUI values override config.ini for that session only
   - To make changes permanent, the settings are saved back to `config.ini`

3. **Date Filtering via GUI**:
   - "Date From (YYYY-MM-DD)": Optional start date
   - "Date To (YYYY-MM-DD)": Optional end date
   - Leave blank to disable date filtering
   - Invalid dates will show an error message

## Programmatic Usage

If using the components directly in Python:

```python
from config import ConfigManager
from date_filter import DateFilter
from pathlib import Path
from datetime import datetime

# Load configuration
config = ConfigManager('config.ini')

# Get values
batch_size = config.get_int('batch_size')
parser_url = config.get('parser_url')

# Get date range
date_from, date_to = config.get_date_range()

# Create date filter
date_filter = DateFilter(date_from, date_to)

# Check if file should be processed
file_path = Path('replay_2024-01-15.w3g')
should_process, reason = date_filter.should_process(file_path)

if should_process:
    print(f"Process {file_path.name}")
else:
    print(f"Skip {file_path.name}: {reason}")
```

## Best Practices

### 1. Set Up config.ini Once
```bash
# Edit config.ini with your standard settings
# Then it's automatically loaded every time
```

### 2. Use Dry Run First
Always test with `dry_run = true` before executing:
```ini
dry_run = true        # Use this first
```

### 3. Use Date Filtering for Large Collections
If you have thousands of files, filter by date to process only what's needed:
```ini
date_from = 2024-06-01    # Only recent files
```

### 4. Monitor Logs
Check `replay_processor.log` for:
- How many files were skipped due to date filter
- Processing speed
- Any errors

### 5. Adjust Batch Size for Performance
```ini
batch_size = 1000        # Faster for 5000+ files
parallel_threads = 16    # More threads = faster
```

## Troubleshooting

### Issue: Config.ini Not Loading
**Solution**: Delete `config.ini` and restart. It will be recreated with defaults.

### Issue: Date Filter Not Working
**Check**:
1. Date format is `YYYY-MM-DD`
2. Both date_from and date_to are valid dates
3. Check logs for detailed error messages

### Issue: No Files Match Date Filter
**Check**:
1. Verify date range is correct
2. Look at file modification dates
3. Check if filenames contain dates in expected format

### Issue: Slow Processing
**Optimize**:
1. Increase `batch_size`: `1000` or `2000`
2. Increase `parallel_threads`: up to `16`
3. Use `date_from` to filter out old files

## File Structure

```
replay-batch-app/
├── config.ini              ← Configuration file (auto-created)
├── replay_processor.log    ← Log file (auto-created)
├── replay_batch_gui.py     ← Main GUI application
├── config.py               ← Configuration management module
├── date_filter.py          ← Date filtering module
├── logging_setup.py        ← Logging configuration
└── requirements.txt        ← Dependencies
```

## Configuration Precedence

Values are loaded in this order (later overrides earlier):

1. `config.ini` defaults
2. `config.ini` values
3. GUI form values (current session only)
4. Values are saved back to `config.ini` when you close the app

## Configuration Migration

If you have existing `settings.json`:
1. The app reads from `config.ini` first
2. Falls back to `settings.json` if `config.ini` doesn't exist
3. Saves to both for compatibility
4. You can safely delete `settings.json` once migrated
