"""Minimal static file server for the Pyodide-based Roam game.

Adds the Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy headers
required for SharedArrayBuffer (used for input delivery from the main thread
to the Python Worker).

Routes:
  /  /play  /play/  → web/index.html
  /web/...           → web/ directory (game.zip, game-worker.js, etc.)
  /assets/...        → assets/ directory (tile sprites)
  /schemas/...       → schemas/ directory
  everything else    → 404
"""

import http.server
import os
from urllib.parse import unquote, urlparse

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_WEB_DIR = os.path.dirname(__file__)


class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=_ROOT, **kwargs)

    def _is_index(self):
        path = unquote(urlparse(self.path).path)
        return path in ("/", "/play", "/play/", "/index.html")

    def _send_index(self, include_body):
        index = os.path.join(_WEB_DIR, "index.html")
        with open(index, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def do_GET(self):
        if self._is_index():
            self._send_index(include_body=True)
            return
        super().do_GET()

    def do_HEAD(self):
        # Without this, HEAD /play falls through to the static-file lookup and
        # 404s while GET /play is 200 — link checkers and crawlers use HEAD.
        if self._is_index():
            self._send_index(include_body=False)
            return
        super().do_HEAD()

    def end_headers(self):
        # Required for SharedArrayBuffer (Pyodide Worker input delivery)
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        path = getattr(self, "path", "") or ""
        bare = path.split("?")[0]
        if bare.endswith("game_version.txt"):
            # Never cache — the Worker fetches this to get the current zip hash.
            self.send_header("Cache-Control", "no-store")
        elif any(bare.endswith(ext) for ext in (".zip", ".js")):
            # Revalidate on every request so a new deploy is always picked up.
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


class _Server(http.server.HTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Roam game server: http://localhost:{port}/play")
    _Server(("", port), _Handler).serve_forever()
