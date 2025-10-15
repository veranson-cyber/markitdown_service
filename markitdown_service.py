#!/usr/bin/env python3
"""
MarkItDown service entrypoint (extracted)
"""

from pathlib import Path
import sys
import os

# Add parent directory to sys.path to allow local imports if needed
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from markitdown_service import main

if __name__ == '__main__':
    main()
