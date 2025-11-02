# 🚀 GETTING STARTED - Replay Batch Processor

## ⚡ Super Quick Start (5 minutes)

### Step 1: Install Everything
Open Command Prompt and paste this (one line):
```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app && INSTALL.bat
```

Or just **double-click INSTALL.bat** in the replay-batch-app folder

### Step 2: Run the App
**Double-click**: `dist\ReplayBatchProcessor.exe`

### Step 3: Use the App
1. Enter player name: `crucibles`
2. Click "Browse..." for Source Folder: `C:\Users\Admin\Desktop\Git\replay-project\Replay`
3. Click "Browse..." for Output Folder: `C:\Users\Admin\Desktop\Git\replay-project\Replay\crucibles`
4. Check "Dry Run" (to preview first)
5. Click "Start Processing"
6. Review the log
7. Uncheck "Dry Run"
8. Click "Start Processing" again (for real)

Done! ✅

---

## 📋 What Each File Does

| Filename | What It Is | When To Use |
|----------|-----------|-----------|
| **INSTALL.bat** | Setup installer | First time only - double-click it |
| **run.bat** | Quick launcher | Every time you want to run the app |
| **ReplayBatchProcessor.exe** | The app itself | After INSTALL.bat, double-click this |
| **INDEX.md** | File guide | If you're lost, read this |
| **APP_SUMMARY.md** | What it does | For a quick overview |
| **SETUP.md** | How to install | For step-by-step instructions |
| **README.md** | Complete guide | For detailed documentation |

---

## 🎯 What The App Does

```
Your Replays    →  [Replay Batch Processor]  →  Organized By Player
(mixed files)          (GUI App)                 (neat folders)
```

The app:
- ✅ Reads replay files from a source folder
- ✅ Filters by player name you choose
- ✅ Organizes them into output folder
- ✅ Shows progress in real-time
- ✅ Lets you preview before executing

---

## 3️⃣ Installation Methods

### Method 1: One-Click Installer (EASIEST) ⭐
```
1. Double-click: INSTALL.bat
2. Wait for completion
3. Double-click: dist\ReplayBatchProcessor.exe
```

### Method 2: Manual Command Line
```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
pip install -r requirements.txt
python build.py
dist\ReplayBatchProcessor.exe
```

### Method 3: No Build (Quick Test)
```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
pip install -r requirements.txt
python replay_batch_gui.py
```

---

## ❌ Common Problems & Solutions

### Problem: "Python not found"
**Solution**: Install Python from https://www.python.org/downloads/
- Download Python 3.10+
- During install, **CHECK** "Add Python to PATH"
- Restart your computer
- Try INSTALL.bat again

### Problem: "Build failed" or "PyInstaller not found"
**Solution**: Run this in Command Prompt:
```
pip install --force-reinstall pyinstaller
python build.py
```

### Problem: "Parser not responding"
**Solution**: 
- Make sure your replay parser is running at http://localhost:3000
- Check that it's accessible
- Verify the parser is working before running the app

### Problem: "No .w3g files found"
**Solution**:
- Check that your Source Folder is correct
- Make sure it contains .w3g replay files
- Check folder permissions

### Problem: "GUI won't open"
**Solution**: Run this in Command Prompt to see the error:
```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app
python replay_batch_gui.py
```

---

## 📂 Folder Structure After Setup

```
replay-batch-app/
├── replay_batch_gui.py      ← Main app (Python code)
├── build.py                 ← Builds the .exe
├── run.bat                  ← Launches the app
├── run.py                   ← Python launcher
├── INSTALL.bat              ← Setup installer ⬅ RUN THIS FIRST!
├── requirements.txt         ← Packages to install
├── settings.json            ← Your saved settings (auto-created)
├── *.md                     ← Documentation files
└── dist/
    └── ReplayBatchProcessor.exe  ← YOUR APP (created by INSTALL.bat)
```

---

## ✨ Features

- 🖥️ **Graphical Interface** - No command line needed
- 👤 **Player Filtering** - Choose which player to process
- 📁 **Folder Selection** - Browse and pick folders
- 🔄 **Batch Processing** - Process many files efficiently
- 👁️ **Preview Mode** - See what would happen before executing
- 📊 **Live Progress Log** - Watch everything in real-time
- 💾 **Settings Saved** - Your preferences persist
- 🔧 **Customizable** - Change parser URL, batch size, etc.

---

## 🎮 Using The App

### Basic Workflow

1. **Open** → Double-click run.bat or ReplayBatchProcessor.exe
2. **Enter Player Name** → Type "crucibles" or your player name
3. **Select Source** → Click Browse, find your Replay folder
4. **Select Output** → Click Browse, pick where to save
5. **Preview** → Check "Dry Run", click "Start Processing"
6. **Review Log** → Check what would be created
7. **Execute** → Uncheck "Dry Run", click "Start Processing"
8. **Done** → Files are organized!

### Dry Run Mode (RECOMMENDED)

Always do this first:
```
✓ Check "Dry Run (preview without creating files)"
✓ Click "Start Processing"
✓ Watch the log
✓ Verify it looks right
✓ Uncheck "Dry Run" if happy
✓ Click "Start Processing" for real
```

---

## 🎯 Example Usage

**I want to organize replays for "crucibles"**

1. Open the app
2. Player Name: `crucibles`
3. Source: `C:\Users\Admin\Desktop\Git\replay-project\Replay`
4. Output: `C:\Users\Admin\Desktop\Git\replay-project\Replay\crucibles`
5. Dry Run: ✓ (checked)
6. Start → Check log → OK? → Uncheck → Start again

**Result**: Replays organized in `Replay\crucibles\` by character!

---

## 💡 Tips & Tricks

- **Always dry run first** - Safety first!
- **Check the log** - Shows exactly what's happening
- **Save your settings** - They're auto-saved
- **Fast processing** - Increase batch size to 100+
- **Multiple players** - Run the app multiple times
- **Share the .exe** - Give dist/ReplayBatchProcessor.exe to others
- **Desktop shortcut** - Right-click .exe → Send to → Desktop

---

## 🆘 Need Help?

### Quick Links
- **Quick overview**: Read `APP_SUMMARY.md`
- **Step-by-step**: Read `SETUP.md`
- **Everything**: Read `README.md`
- **File guide**: Read `INDEX.md`

### Troubleshooting
1. Check the log for error messages
2. Verify settings are correct
3. Make sure parser is running
4. Check folder permissions
5. Read the README.md for detailed help

---

## ✅ Checklist

```
Before you start:
□ Python 3.8+ installed (or using .exe)
□ Replay files in source folder
□ Parser running at http://localhost:3000
□ Write access to output folder

To install:
□ Run INSTALL.bat (or follow Method 2/3)
□ Wait for "Setup Complete" message

To use:
□ Double-click run.bat or ReplayBatchProcessor.exe
□ Fill in player name and folders
□ Run Dry Run first
□ Review log
□ Execute for real
□ Check output folder
□ ✅ Done!
```

---

## 🚀 Ready?

### Option A: One Command (Easiest)
```
cd C:\Users\Admin\Desktop\Git\replay-project\replay-batch-app && INSTALL.bat
```

### Option B: Double-Click Installer
```
Find: replay-batch-app\INSTALL.bat
Double-click it
```

### Option C: Manual Setup
```
1. pip install -r requirements.txt
2. python build.py
3. dist\ReplayBatchProcessor.exe
```

---

## 📞 Still Having Issues?

1. **Read the full docs**: Open `README.md` in Notepad
2. **Check error messages**: Run from command line to see output
3. **Verify setup**: Try running INSTALL.bat again
4. **Test parser**: Visit http://localhost:3000 in your browser

---

**Good luck! The app will make batch processing your replays super easy! 🎉**

Questions? Read the documentation files in this folder.
