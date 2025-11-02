# Replay Batch Processor - Application Files

## 📁 Application Location
```
C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app\
```

## 🚀 Getting Started (Choose One)

### For Windows Users (Easiest)
```
1. Double-click: INSTALL.bat
   → This installs everything and builds the .exe

2. Double-click: dist\ReplayBatchProcessor.exe
   → Run the application!
```

### For Command Line Users
```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
pip install -r requirements.txt
python build.py
dist\ReplayBatchProcessor.exe
```

### For Quick Testing (No Build)
```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
pip install -r requirements.txt
python replay_batch_gui.py
```

## 📄 File Descriptions

### Startup Files
- **INSTALL.bat** ← Double-click this first to set everything up
- **run.bat** ← Double-click to run the application
- **run.py** - Python launcher script

### Application Files
- **replay_batch_gui.py** - Main GUI application (Python source)
- **build.py** - Script to create the Windows executable

### Configuration Files
- **requirements.txt** - Python dependencies
- **settings.json** - User settings (auto-created on first run)

### Documentation
- **APP_SUMMARY.md** - Quick overview of the application ⬅ START HERE
- **README.md** - Full comprehensive documentation
- **SETUP.md** - Detailed setup instructions
- **INDEX.md** - This file

### Output
- **dist/** - Folder containing the built executable
  - **ReplayBatchProcessor.exe** - Standalone Windows application (created by build.py)

## 📋 Quick Setup Checklist

```
□ 1. Double-click INSTALL.bat
□ 2. Wait for setup to complete
□ 3. Double-click dist\ReplayBatchProcessor.exe
□ 4. Enter your player name and folder paths
□ 5. Click "Start Processing"
```

## 🎯 What You Can Do

1. **Process Replay Files**
   - Select source folder with .w3g replay files
   - Choose player name to filter by
   - Select output folder for processed files
   
2. **Preview Before Executing**
   - Use "Dry Run" mode to preview changes
   - Check the log to see what would happen
   - Execute for real when ready

3. **Automate Workflow**
   - Save your settings (auto-saved)
   - Process multiple players sequentially
   - Export executable for others to use

4. **Customize Settings**
   - Configure parser URL
   - Adjust batch size
   - Set preferred folders

## 💾 Files Location

| File | Location | Purpose |
|------|----------|---------|
| GUI App | replay_batch_gui.py | Main application (Python) |
| Executable | dist/ReplayBatchProcessor.exe | Compiled Windows app |
| Settings | settings.json | Stores your preferences |
| Dependencies | requirements.txt | Python packages needed |
| Builder | build.py | Creates the .exe |
| Launcher | run.bat | Double-click to run |

## ⚙️ System Requirements

- Windows 7 or higher
- 100MB+ free disk space
- Replay parser running at http://localhost:3000
- (Optional: Python 3.8+ if running from source)

## 🔧 Troubleshooting

### App Won't Start
1. Check that Python 3.8+ is installed
2. Run INSTALL.bat to set up dependencies
3. Try running from command line to see errors

### Parser Not Connecting
1. Verify replay parser is running
2. Check parser URL in the GUI
3. Ensure port 3000 is accessible

### Build Failed
1. Update pip: `python -m pip install --upgrade pip`
2. Reinstall PyInstaller: `pip install --force-reinstall pyinstaller`
3. Run INSTALL.bat again

## 📚 Documentation

- **APP_SUMMARY.md** - High-level overview (5 min read)
- **SETUP.md** - Step-by-step instructions (10 min read)
- **README.md** - Complete documentation (20 min read)

## 🎁 What's Included

✓ Full-featured GUI application
✓ Windows executable builder
✓ Batch processing support
✓ Real-time progress logging
✓ Settings persistence
✓ Dry run mode for safety
✓ Complete documentation
✓ Easy installer script
✓ Multiple launch options

## 🚀 Next Steps

1. **First Time?**
   → Read APP_SUMMARY.md (quick overview)

2. **Ready to Install?**
   → Double-click INSTALL.bat

3. **Need Help?**
   → Check SETUP.md or README.md

4. **Want to Customize?**
   → Edit replay_batch_gui.py and rebuild

## 📝 Version Info

- **App Version**: 1.0
- **Python Version**: 3.8+
- **Dependencies**: requests, pyinstaller
- **Platform**: Windows 7+
- **Build Tool**: PyInstaller

## 💡 Tips

- Always run Dry Run first to preview changes
- Save the executable somewhere safe
- Create a desktop shortcut for easy access
- Settings are automatically saved
- Log shows all details of what's happening

## ❓ FAQ

**Q: Do I need Python to run the .exe?**
A: No! The .exe is completely standalone.

**Q: Can I share the .exe with others?**
A: Yes! The dist/ReplayBatchProcessor.exe works on any Windows 7+ machine.

**Q: Where are my settings saved?**
A: In settings.json in the replay-batch-app folder.

**Q: Can I process multiple players at once?**
A: Not simultaneously, but you can run the app multiple times.

**Q: What if the parser is down?**
A: The app will show an error. Make sure your parser is running.

---

**Ready?** → Double-click `INSTALL.bat` to get started!
