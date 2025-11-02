#!/usr/bin/env python3
"""
Build script to create a Windows executable from the GUI application
Requires: pyinstaller

To use:
1. Install dependencies: pip install -r requirements.txt
2. Run this script: python build.py
"""

import os
import sys
import subprocess
from pathlib import Path

def build_executable():
    """Build the Windows executable"""
    
    script_path = Path(__file__).parent / "replay_batch_gui.py"
    dist_path = Path(__file__).parent / "dist"
    build_path = Path(__file__).parent / "build"
    
    print("Building Windows executable...")
    print(f"Script: {script_path}")
    print(f"Output: {dist_path}\n")
    
    # Check if pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("ERROR: PyInstaller is not installed!")
        print("Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            import PyInstaller
        except Exception as e:
            print(f"ERROR: Failed to install PyInstaller: {e}")
            print("Install it manually with: pip install pyinstaller")
            return False
    
    # Build command - start with basic command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Create single executable
        "--windowed",  # No console window
        "--name", "ReplayBatchProcessor",
        "--distpath", str(dist_path),
        "--workpath", str(build_path),
        "--specpath", str(Path(__file__).parent),
        str(script_path)
    ]
    
    # Add icon if it exists
    icon_path = Path(__file__).parent / "replay_icon.ico"
    if icon_path.exists():
        cmd.insert(5, "--icon")
        cmd.insert(6, str(icon_path))
    
    # Add rename_replays.py if it exists
    rename_file = Path(__file__).parent.parent / "rename_replays.py"
    if rename_file.exists():
        cmd.extend(["--add-data", f"{str(rename_file)};."])
    
    # Remove None values from command
    cmd = [x for x in cmd if x is not None]
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "="*60)
        print("[OK] Build successful!")
        print("="*60)
        print(f"\nExecutable created at: {dist_path / 'ReplayBatchProcessor.exe'}")
        print("\nYou can now run the .exe file directly without Python installed!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed with error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
