#!/usr/bin/env python3
"""Build the browser game as a static site for arcade (Stephenson-Software RFC 0006/0012).

arcade serves a ``kind: static`` game as plain files at the root of its own
host (https://roam.play.danielstephenson.dev), so the site is laid out exactly
as web/serve.py lays out the repository for the page:

    index.html              <- web/index.html (serve.py answers / with it)
    web/game-worker.js      <- the Pyodide Worker
    web/saves.js            <- the Saves panel (download / load a saves file)
    web/arcade-scores.js    <- arcade-social's client (achievements, leaderboards)
    web/game.zip            <- built by web/build_zip.py
    web/game_version.txt    <- the zip's content hash (cache-busting)
    assets/...              <- tile sprites, fetched by the page as /assets/...

Nothing else is copied: the Python sources reach the browser only inside
game.zip, and serve.py itself is not part of the site. arcade-deploy writes
version.txt at the site's root.

The page uses root-relative URLs (/web/..., /assets/...), so the site must be
served at the root of its host; arcade does exactly that. The game needs
SharedArrayBuffer, so the arcade registry entry needs ``isolation: on``.

Usage (from anywhere):
    python3 web/build_arcade_site.py [OUT_DIR]     # default: build/arcade-site
"""

import os
import runpy
import shutil
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# (source relative to ROOT, destination relative to the site root)
FILES = (
    ("web/index.html", "index.html"),
    ("web/game-worker.js", "web/game-worker.js"),
    ("web/saves.js", "web/saves.js"),
    ("web/arcade-scores.js", "web/arcade-scores.js"),
    ("web/game.zip", "web/game.zip"),
    ("web/game_version.txt", "web/game_version.txt"),
)
DIRECTORIES = (("assets", "assets"),)


def assemble(root, out):
    """Copy an already-built web bundle from ``root`` into a fresh ``out``."""
    if os.path.exists(out):
        raise SystemExit(f"{out} already exists; remove it or pass another OUT_DIR")
    for src, _ in FILES:
        if not os.path.isfile(os.path.join(root, src)):
            raise SystemExit(f"{src} is missing (run web/build_zip.py first)")
    os.makedirs(out)
    for src, dst in FILES:
        target = os.path.join(out, dst)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(os.path.join(root, src), target)
    for src, dst in DIRECTORIES:
        shutil.copytree(
            os.path.join(root, src),
            os.path.join(out, dst),
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".*"),
        )


def main(argv):
    out = os.path.abspath(argv[1] if len(argv) > 1 else "build/arcade-site")
    os.chdir(ROOT)  # build_zip.py works relative to the repository root
    runpy.run_path(os.path.join("web", "build_zip.py"), run_name="__main__")
    assemble(ROOT, out)
    count = sum(len(files) for _, _, files in os.walk(out))
    print(f"Built the arcade site at {out} ({count} files)")


if __name__ == "__main__":
    main(sys.argv)
