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
    """Build the Windows executable using the spec file"""
    
    script_dir = Path(__file__).parent
    spec_file = script_dir / "ReplayBatchProcessor.spec"
    dist_path = script_dir / "dist"
    
    print("Building Windows executable...")
    print(f"Spec: {spec_file}")
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
    
    # Build command using spec file
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(spec_file)
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "="*60)
        print("[OK] Build successful!")
        print("="*60)
        print(f"\nExecutable: {dist_path / 'ReplayBatchProcessor.exe'}")
        print("ReplayRenamer is inlined - no external files needed.")
        print("You can distribute the .exe file standalone!")
        
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
