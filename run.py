#!/usr/bin/env python3
"""
Simple launcher for the Replay Batch Processor GUI
Run this file to start the application
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    try:
        from replay_batch_gui import main
        main()
    except Exception as e:
        print(f"Error starting application: {e}")
        print("\nPlease make sure:")
        print("1. You are in the replay-batch-app directory")
        print("2. Python 3.8+ is installed")
        print("3. Dependencies are installed: pip install -r requirements.txt")
        input("\nPress Enter to exit...")
        sys.exit(1)
