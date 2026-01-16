"""Pytest configuration for screen tests."""
import sys
import os
import pytest


def pytest_configure(config):
    """Configure pytest before test collection."""
    # Add src directories to path
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    src_path = os.path.join(root_path, 'src')
    src_screen_path = os.path.join(src_path, 'screen')
    src_entity_path = os.path.join(src_path, 'entity')
    
    for path in [root_path, src_path, src_screen_path, src_entity_path]:
        if path not in sys.path:
            sys.path.insert(0, path)
