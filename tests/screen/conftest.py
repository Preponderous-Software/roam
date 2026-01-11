"""Pytest configuration for screen tests."""
import sys
import os
from unittest.mock import MagicMock

# Mock pygame before any test imports
sys.modules['pygame'] = MagicMock()

# Add src to path - go up two levels from tests/screen to get to root, then add src
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
src_path = os.path.join(root_path, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

