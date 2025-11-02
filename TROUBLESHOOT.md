# INSTALL.bat Issues - Troubleshooting Guide

## Common Errors & Fixes

### Error 1: "Python is not installed or not in PATH"
**Cause**: Python is not installed or not added to Windows PATH

**Solution**:
1. Install Python from https://www.python.org/downloads/
2. During installation, **CHECK** "Add Python to PATH"
3. Restart your computer
4. Try INSTALL.bat again

### Error 2: "Failed to install dependencies"
**Cause**: pip package manager has issues

**Solution Option A** (Automatic - NEW):
- INSTALL.bat now handles this automatically and tries alternative method

**Solution Option B** (Manual):
```
1. Open Command Prompt
2. cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
3. python -m pip install --upgrade pip
4. python -m pip install requests pyinstaller
5. python build.py
```

### Error 3: Build Failed / PyInstaller Not Found
**Cause**: PyInstaller not installed

**Solution** (Now Fixed):
- build.py now automatically installs PyInstaller if missing
- Just run INSTALL.bat again

### Error 4: "Module not found" or import errors
**Cause**: Missing dependencies

**Solution**:
```
python -m pip install requests
python replay_batch_gui.py
```

## Quick Fixes

### If INSTALL.bat fails:

**Option 1: Manual Installation**
```
1. Open Command Prompt
2. cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
3. pip install requests
4. python replay_batch_gui.py
```

**Option 2: Just Run the App**
```
1. Double-click run.bat
2. It will try to install dependencies automatically
```

**Option 3: Python Command Line**
```
1. Open Command Prompt
2. cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
3. python build.py
4. If that works, run: python replay_batch_gui.py
```

## Testing Each Step

### Test Python Installation
```
python --version
```
Should show: Python 3.8.x or higher

### Test pip
```
python -m pip --version
```
Should show version information

### Test Requests Installation
```
python -m pip install requests
```

### Test Application
```
python replay_batch_gui.py
```
Should open the GUI window

### Test Build (Optional)
```
python -m pip install pyinstaller
python build.py
```

## Most Likely Solution

If INSTALL.bat fails, try this (all one line):

```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app && python -m pip install requests && python replay_batch_gui.py
```

This will:
1. Navigate to the app folder
2. Install the requests package
3. Run the application

## If Still Having Issues

### Check These Files Exist:
```
✓ C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app\replay_batch_gui.py
✓ C:\Users\Admin\Desktop\Git\replay-project\replay_replays.py
✓ C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app\run.bat
```

### Verify Python:
```
1. Open Command Prompt
2. Type: python
3. Type: import sys; print(sys.version)
4. Should show Python 3.8+
5. Type: exit()
```

### Clear Cache and Reinstall:
```
python -m pip install --upgrade --force-reinstall requests
```

## Contact Information

If you're still stuck:
1. Note the exact error message
2. Check that all files are in their correct locations
3. Try running from Command Prompt to see full error messages
4. Verify Python is installed correctly

## Files That Were Fixed

The following files have been updated to be more robust:

- **INSTALL.bat** - Now handles more errors gracefully
- **run.bat** - Tries .exe first, then Python
- **build.py** - Auto-installs PyInstaller if needed
- **replay_batch_gui.py** - Better error handling for imports

These changes should prevent most common errors!
