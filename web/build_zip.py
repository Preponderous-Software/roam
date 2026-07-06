#!/usr/bin/env python3
"""Build web/game.zip — run at Docker build time via Dockerfile RUN step.

Bundles the Python source tree, schemas, and config into a single zip that
the browser's Pyodide Worker downloads and unpacks into its virtual filesystem.

Also writes web/game_version.txt containing the SHA-256 of the zip so the
Worker can request game.zip?v=<hash> — a content-addressed URL that forces
the browser to fetch a new zip whenever the source changes.
"""
import hashlib
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
    # Web Worker support modules (entry point + Pyodide compat shim)
    for _web_file in ("web/pyodide_main.py", "web/pyodide_compat.py"):
        if os.path.exists(_web_file):
            z.write(_web_file, _web_file)

with open("web/game.zip", "rb") as _f:
    _digest = hashlib.sha256(_f.read()).hexdigest()
with open("web/game_version.txt", "w") as _f:
    _f.write(_digest)

print(f"Built web/game.zip ({_digest[:12]})")
