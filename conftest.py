"""
Pytest configuration file to set up Python path for test discovery.
This ensures that modules can be imported correctly during test collection.
"""
import sys
import os

# Add src and its subdirectories to Python path for imports
repo_root = os.path.dirname(os.path.abspath(__file__))
paths_to_add = [
    repo_root,
    os.path.join(repo_root, 'src'),
    os.path.join(repo_root, 'src', 'entity'),
    os.path.join(repo_root, 'src', 'screen'),
]

for path in paths_to_add:
    if path not in sys.path:
        sys.path.insert(0, path)
