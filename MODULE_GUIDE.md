# Module Guide - Developer Reference

## Overview

This guide explains how to use each module in the Replay Batch Processor for developers who want to extend or use the components.

## Module Architecture

```
┌─────────────────────────────────────────┐
│     replay_batch_gui.py                 │
│   (Main GUI Application)                │
├─────────────────────────────────────────┤
│  ┌───────────────┬──────────────────┐  │
│  │  config.py    │  date_filter.py  │  │
│  │  (Config Mgmt)│ (File Filtering) │  │
│  └───────────────┴──────────────────┘  │
│           ↓              ↓               │
│  ┌────────────────────────────────┐    │
│  │   logging_setup.py             │    │
│  │  (Logging Configuration)       │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## 1. config.py - Configuration Management

### Purpose
Manages application configuration from `config.ini` file with support for defaults, type conversion, and overrides.

### Main Class: ConfigManager

```python
from config import ConfigManager

# Create instance
config = ConfigManager('config.ini')

# Get string value
url = config.get('parser_url')

# Get with default
folder = config.get('input_folder', default='./input')

# Get integer value
batch_size = config.get_int('batch_size', default=500)

# Get boolean value
dry_run = config.get_bool('dry_run', default=True)

# Get date range for filtering
date_from, date_to = config.get_date_range()

# Set a value
config.set('parser_url', 'http://localhost:8080')

# Save changes to file
config.save_config()

# Override multiple values at once
args = {
    'batch_size': 1000,
    'parser_url': 'http://example.com:3000'
}
config.override_from_cli_args(args)
```

### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `__init__` | `config_file` | - | Initialize and load config file |
| `load_config` | - | - | Load from file or create defaults |
| `get` | `key, section, default` | Any | Get string value |
| `get_int` | `key, section, default` | int | Get integer value |
| `get_bool` | `key, section, default` | bool | Get boolean value |
| `set` | `key, value, section` | - | Set a value |
| `save_config` | - | - | Save to file |
| `get_date_range` | - | (datetime, datetime) | Get date range for filtering |
| `override_from_cli_args` | `args_dict` | - | Override with CLI arguments |

### Configuration Sections

Default section is `[SETTINGS]`:

```ini
[SETTINGS]
key = value
key2 = value2
```

Access other sections:
```python
value = config.get('key', section='OTHER_SECTION')
```

### Default Values

Automatically created on first run:

```python
DEFAULTS = {
    'SETTINGS': {
        'input_folder': './input',
        'output_folder': './output',
        'parser_url': 'http://localhost:3000',
        'batch_size': '500',
        'parallel_threads': '8',
        'date_from': '',
        'date_to': '',
        'log_level': 'INFO',
        'dry_run': 'true',
        'skip_existing': 'true',
    }
}
```

### Error Handling

- Returns default value if key not found
- Handles missing sections gracefully
- Date parsing raises `ValueError` with clear error message
- File I/O errors are logged as warnings

### Best Practices

✅ Load once at startup:
```python
config = ConfigManager('config.ini')
```

✅ Access via accessors:
```python
value = config.get_int('batch_size')  # Better than int(config.get(...))
```

✅ Use defaults:
```python
value = config.get('key', default='fallback_value')
```

❌ Don't parse types manually:
```python
# Bad: Manual type conversion
config.get('batch_size')  # Returns string '500'
int(config.get('batch_size'))  # Manual conversion

# Good: Use type-safe getter
config.get_int('batch_size')  # Returns int 500
```

## 2. date_filter.py - Date-Based Filtering

### Purpose
Filters files based on date ranges extracted from filenames or file metadata.

### Main Class: DateFilter

```python
from date_filter import DateFilter
from datetime import datetime
from pathlib import Path

# Create filter for date range
date_from = datetime(2024, 1, 1)
date_to = datetime(2024, 1, 31)
filter = DateFilter(date_from, date_to)

# Check if file should be processed
file_path = Path('replay_2024-01-15.w3g')
should_process, reason = filter.should_process(file_path)

if should_process:
    print(f"Process: {file_path.name}")
else:
    print(f"Skip: {file_path.name} - {reason}")

# Create filter with no lower bound
filter = DateFilter(date_from=datetime(2024, 1, 1), date_to=None)

# Create filter with no date filtering
filter = DateFilter()  # Both None = disabled
if filter.enabled:
    print("Filter is active")
else:
    print("Filter is disabled")
```

### Methods

| Method | Parameters | Returns | Description |
|--------|----------|---------|-------------|
| `__init__` | `date_from, date_to` | - | Initialize filter |
| `should_process` | `file_path` | (bool, str) | Check if file should be processed |
| `_get_file_date` | `file_path` | datetime \| None | Extract date from file |
| `_parse_date_from_filename` | `filename` | datetime \| None | Parse date from filename |

### Supported Date Formats in Filenames

- `YYYY-MM-DD` (e.g., `replay-2024-01-15.w3g`)
- `MM-DD-YYYY` (e.g., `replay-01-15-2024.w3g`)
- `YYYYMMDD` (e.g., `replay20240115.w3g`)

### Return Values

```python
should_process, reason = filter.should_process(file_path)

# Success
should_process = True
reason = ""

# Skipped - before date range
should_process = False
reason = "Before date range (2024-01-10)"

# Skipped - after date range
should_process = False
reason = "After date range (2024-02-01)"

# No date found
should_process = False
reason = "Could not determine file date"
```

### Date Detection Priority

1. Parse date from filename using regex patterns
2. Fall back to file modification timestamp
3. Return None if both fail (file will be skipped)

### Usage Examples

#### Filter for Specific Month
```python
filter = DateFilter(
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 1, 31)
)
```

#### Filter for Recent Files
```python
from datetime import datetime, timedelta

today = datetime.now()
one_month_ago = today - timedelta(days=30)

filter = DateFilter(date_from=one_month_ago)
```

#### Process All Files
```python
filter = DateFilter()  # No filtering
```

#### Batch Process with Filtering
```python
filter = DateFilter(date_from=datetime(2024, 6, 1))
files = Path('replays').glob('*.w3g')

skipped = 0
processed = 0

for file in files:
    should_process, reason = filter.should_process(file)
    if should_process:
        # Process file
        processed += 1
    else:
        # Skip file, log reason
        skipped += 1
        print(f"Skip {file.name}: {reason}")

print(f"Processed: {processed}, Skipped: {skipped}")
```

### Best Practices

✅ Always check `filter.enabled` before processing:
```python
if filter.enabled:
    should_process, reason = filter.should_process(file)
```

✅ Log skip reasons for debugging:
```python
if not should_process:
    logging.info(f"Skipped {file.name}: {reason}")
```

✅ Use date ranges instead of individual dates:
```python
# Better: Range
filter = DateFilter(date_from, date_to)

# Less flexible: Single check
if file_date == target_date:
    process(file)
```

❌ Don't ignore skip reasons:
```python
# Bad: Ignoring why file was skipped
for file in files:
    filter.should_process(file)  # Reason ignored

# Good: Log the reason
for file in files:
    ok, reason = filter.should_process(file)
    if not ok:
        logger.info(f"Skip: {reason}")
```

## 3. logging_setup.py - Logging Configuration

### Purpose
Configure consistent application-wide logging with file and console handlers.

### Main Function: setup_logging

```python
from logging_setup import setup_logging
import logging

# Basic setup with defaults
setup_logging()

# Custom configuration
setup_logging(
    log_level='DEBUG',
    log_file='app.log',
    console_output=True
)

# No file logging
setup_logging(log_level='INFO', log_file=None)

# Now use standard logging
logger = logging.getLogger(__name__)
logger.info("This will be logged to both file and console")
logger.error("Error message")
logger.debug("Debug message (only if level=DEBUG)")
```

### Function Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_level` | str | 'INFO' | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `log_file` | str | 'replay_processor.log' | Path to log file or None to disable |
| `console_output` | bool | True | Output to console (stdout) |

### Log Levels

| Level | Priority | Use Case |
|-------|----------|----------|
| `DEBUG` | Lowest | Detailed info for debugging |
| `INFO` | Low | General informational messages |
| `WARNING` | Medium | Warning messages |
| `ERROR` | High | Error messages |
| `CRITICAL` | Highest | Critical errors |

### Log Format

```
2024-03-05 14:32:10 - module.name - INFO - Message text
```

Parts:
- Timestamp: `YYYY-MM-DD HH:MM:SS`
- Module: `module.submodule` (from logger name)
- Level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- Message: Actual log message

### File Handler Features

- **Rotating**: Automatically creates backup files when size limit reached
- **Max Size**: 10MB per log file
- **Backups**: Keeps 5 backup files
- **Auto Directory**: Creates log directory if missing

### Usage Examples

#### Typical Application Setup
```python
from logging_setup import setup_logging
import logging

# At application startup
setup_logging(log_level='INFO', log_file='app.log')

# Throughout application
logger = logging.getLogger(__name__)
logger.info("Application started")
logger.warning("Something unexpected")
logger.error("An error occurred")
```

#### Debugging Information
```python
setup_logging(log_level='DEBUG')

logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {some_var}")
logger.debug(f"Function args: {args}")
```

#### Production Setup
```python
setup_logging(
    log_level='WARNING',  # Only warnings and errors
    log_file='/var/log/myapp.log',
    console_output=False  # Log to file only
)
```

### Best Practices

✅ Call at application startup:
```python
if __name__ == '__main__':
    setup_logging()
    # rest of code
```

✅ Use module-level loggers:
```python
logger = logging.getLogger(__name__)  # Gets loggers like "config", "date_filter"
```

✅ Use appropriate log levels:
```python
logger.info("File processed successfully")  # General info
logger.warning("Cache miss, recomputing")   # Something unexpected
logger.error("Failed to process file")      # Error occurred
logger.debug(f"Debug info: {variable}")     # Only during debugging
```

❌ Don't use print() for application info:
```python
# Bad
print(f"Processing file: {filename}")

# Good
logger.info(f"Processing file: {filename}")
```

## Integration Example

### Complete Application Setup

```python
from config import ConfigManager
from date_filter import DateFilter
from logging_setup import setup_logging
from pathlib import Path
import logging

# 1. Setup logging first
setup_logging(log_level='INFO', log_file='app.log')
logger = logging.getLogger(__name__)

# 2. Load configuration
config = ConfigManager('config.ini')
logger.info("Configuration loaded")

# 3. Get date filtering parameters
date_from, date_to = config.get_date_range()

# 4. Create date filter
date_filter = DateFilter(date_from, date_to)

# 5. Process files
input_folder = Path(config.get('input_folder'))
files = list(input_folder.glob('*.w3g'))
logger.info(f"Found {len(files)} files")

processed = 0
skipped = 0

for file in files:
    # Check date filter
    should_process, reason = date_filter.should_process(file)
    
    if not should_process:
        logger.info(f"Skipped {file.name}: {reason}")
        skipped += 1
        continue
    
    # Process file
    try:
        result = process_file(file)
        logger.info(f"Processed {file.name}")
        processed += 1
    except Exception as e:
        logger.error(f"Error processing {file.name}: {e}")

# 6. Report results
logger.info(f"Complete: {processed} processed, {skipped} skipped")
```

## Common Patterns

### Pattern 1: Configuration with Defaults
```python
config = ConfigManager('config.ini')
batch_size = config.get_int('batch_size', default=500)
threads = config.get_int('parallel_threads', default=8)
```

### Pattern 2: Date Range Filtering
```python
config = ConfigManager('config.ini')
date_from, date_to = config.get_date_range()
filter = DateFilter(date_from, date_to)

for file in Path.glob('*.w3g'):
    ok, reason = filter.should_process(file)
    if ok:
        process(file)
```

### Pattern 3: Configured Logging
```python
config = ConfigManager('config.ini')
setup_logging(log_level=config.get('log_level', 'INFO'))
logger = logging.getLogger(__name__)
logger.info("Started with configuration")
```

### Pattern 4: Override Configuration
```python
config = ConfigManager('config.ini')

# Override from arguments
args = {
    'batch_size': 1000,
    'parser_url': 'http://custom.parser:3000'
}
config.override_from_cli_args(args)
```

## Testing Modules

### Test ConfigManager
```python
def test_config_manager():
    config = ConfigManager('test.ini')
    
    # Test get/set
    config.set('test_key', 'test_value')
    assert config.get('test_key') == 'test_value'
    
    # Test type conversion
    config.set('int_key', '100')
    assert config.get_int('int_key') == 100
    
    # Test save/load
    config.save_config()
    config2 = ConfigManager('test.ini')
    assert config2.get('test_key') == 'test_value'
```

### Test DateFilter
```python
def test_date_filter():
    from datetime import datetime
    
    filter = DateFilter(
        datetime(2024, 1, 1),
        datetime(2024, 1, 31)
    )
    
    # File within range should pass
    ok, _ = filter.should_process(Path('replay-2024-01-15.w3g'))
    assert ok == True
    
    # File outside range should fail
    ok, _ = filter.should_process(Path('replay-2023-12-31.w3g'))
    assert ok == False
```

## Summary

- **config.py**: Use for all configuration needs
- **date_filter.py**: Use for date-based file filtering
- **logging_setup.py**: Use for consistent application logging
- **Compose them**: Together they provide a complete foundation for file processing applications
