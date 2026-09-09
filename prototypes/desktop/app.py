"""
Launcher script for the MetroNY Desktop Application.
Maintained for backwards-compatibility with existing launch scripts (start.bat / start.sh).
Delegates execution to the modular entry point in main.py.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()
