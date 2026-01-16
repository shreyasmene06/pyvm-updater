# conftest.py - Pytest configuration for pyvm-updater tests
"""Configure pytest to properly find the src/pyvm_updater package."""

import sys
from pathlib import Path

# Add the src directory to sys.path for test discovery
src_path = Path(__file__).parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
