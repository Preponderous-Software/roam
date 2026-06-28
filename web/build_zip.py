#!/usr/bin/env python3
"""Build web/game.zip — run at Docker build time via Dockerfile RUN step.

Bundles the Python source tree, schemas, and config into a single zip that
the browser's Pyodide Worker downloads and unpacks into its virtual filesystem.
"""
import os
import zipfile

with zipfile.ZipFile("web/game.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk("src"):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if not f.endswith(".pyc"):
                path = os.path.join(root, f)
                z.write(path, path)
    for root, dirs, files in os.walk("schemas"):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            z.write(os.path.join(root, f), os.path.join(root, f))
    for name in ("config.yml", "version.txt"):
        if os.path.exists(name):
            z.write(name, name)

print("Built web/game.zip")
