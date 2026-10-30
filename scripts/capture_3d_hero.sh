#!/usr/bin/env bash
# capture_3d_hero.sh: re-record the README hero media for the 3D view
# (pics/roam3d-hero.gif and pics/roam3d-hero.png) from the real browser build.
#
# Usage (from the repo root):
#   ./scripts/capture_3d_hero.sh
#
# Needs Python 3 with Pillow (requirements.txt) and Node with Playwright
# (npm install -g playwright && npx playwright install chromium). Takes a few
# minutes: the 3D scene is drawn by Chromium's software WebGL, one frame at a
# time. Every run walks a freshly generated world, so look at the result
# before committing it.
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
PORT="${PORT:-8080}"
FRAMES="$(mktemp -d)"
trap 'kill "${SERVER_PID:-}" 2>/dev/null || true; rm -rf "$FRAMES"' EXIT

"$PYTHON" web/build_zip.py
PORT="$PORT" "$PYTHON" web/serve.py &
SERVER_PID=$!
for _ in $(seq 1 20); do
    curl -sf "http://localhost:$PORT/" > /dev/null && break
    sleep 1
done

node scripts/capture_3d_hero.js "http://localhost:$PORT" "$FRAMES"
"$PYTHON" scripts/make_3d_hero.py "$FRAMES" --out-dir pics
