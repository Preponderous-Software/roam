import asyncio
import functools
import http.server
import json
import os
import threading

from rendering.inputEvent import EventType, InputEvent
from rendering.textClock import TextClock
from rendering.webInputSource import WebInputSource
from rendering.webRenderer import WebRenderer, _DEFAULT_WIDTH, _DEFAULT_HEIGHT

_DEFAULT_WS_PORT = 8765
_DEFAULT_HTTP_PORT = 8080


# @author Daniel McCoy Stephenson
# @since June 27th, 2026
#
# Per-connection frontend: owns one WebRenderer + WebInputSource + TextClock for
# a single browser session.  Implements the same interface as PygameFrontend /
# TextFrontend (getRenderer, getInputSource, getClock, setCaption, reset, quit)
# so Roam.__init__ can accept it as a drop-in frontend.
#
# Input protocol (browser → server, all messages are JSON strings):
#   {"type":"resize",    "w":800, "h":600}         — viewport size changed
#   {"type":"mouse_down","x":320,"y":240,"button":1} — tap / left-click
#   {"type":"mouse_up",  "x":320,"y":240,"button":1} — release
#   raw ANSI bytes (e.g. "\x1b[A" for ↑, "g" for gather) — keyboard / D-pad
#
# Output protocol (server → browser):
#   JSON frame: {"type":"frame","w":W,"h":H,"calls":[{op,…},…]}
class WebSession:
    def __init__(self, websocket, loop):
        self._websocket = websocket
        self._loop = loop
        self._stopped = threading.Event()
        self._build()

    def _build(self):
        self._sendQueue = asyncio.Queue()
        self._inputSource = WebInputSource()
        self._renderer = WebRenderer(self._enqueueFrame, inputSource=self._inputSource)
        self._clock = TextClock()

    def _enqueueFrame(self, data):
        asyncio.run_coroutine_threadsafe(self._sendQueue.put(data), self._loop)

    def feedInput(self, data):
        # --- JSON control messages (resize, mouse) ---
        if data.startswith("{"):
            try:
                msg = json.loads(data)
                t = msg.get("type")

                if t == "resize":
                    w, h = int(msg.get("w", 0)), int(msg.get("h", 0))
                    if w > 0 and h > 0:
                        self._renderer.resize(w, h)
                        self._inputSource.queueEvent(
                            InputEvent(EventType.WINDOW_RESIZE, size=(w, h))
                        )
                    return

                if t in ("mouse_down", "mouse_up"):
                    self._inputSource.updateMouse(
                        int(msg.get("x", 0)),
                        int(msg.get("y", 0)),
                        int(msg.get("button", 1)),
                        t == "mouse_down",
                    )
                    return

                if t == "mouse_move":
                    self._inputSource.moveMouse(
                        int(msg.get("x", 0)),
                        int(msg.get("y", 0)),
                    )
                    return
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        # --- ANSI key sequences from keyboard / on-screen buttons ---
        self._inputSource.feed(data)

    # --- Frontend interface (mirrors PygameFrontend / TextFrontend) ---

    def getRenderer(self):
        return self._renderer

    def getInputSource(self):
        return self._inputSource

    def getClock(self):
        return self._clock

    def setCaption(self, caption):
        pass

    def reset(self):
        self._build()

    def quit(self):
        self._stopped.set()
        asyncio.run_coroutine_threadsafe(self._sendQueue.put(None), self._loop)

    # --- Async I/O pump (runs on the event loop, not the game thread) ---

    async def runIO(self):
        async def _send():
            while True:
                data = await self._sendQueue.get()
                if data is None:
                    return
                try:
                    await self._websocket.send(data)
                except Exception:
                    return

        async def _receive():
            try:
                async for message in self._websocket:
                    self.feedInput(message)
            except Exception:
                pass

        await asyncio.gather(_send(), _receive(), return_exceptions=True)


# @author Daniel McCoy Stephenson
# @since June 27th, 2026
#
# WebSocket game server.  serve(gameFactory) starts two listeners:
#   - HTTP on httpPort: serves web/index.html + game assets (assets/ dir)
#   - WebSocket on wsPort: each connection spawns a WebSession + a game thread.
class WebFrontend:
    def __init__(self, wsPort=_DEFAULT_WS_PORT, httpPort=_DEFAULT_HTTP_PORT):
        self._wsPort = wsPort
        self._httpPort = httpPort

    def serve(self, gameFactory):
        try:
            asyncio.run(self._serveAsync(gameFactory))
        except KeyboardInterrupt:
            pass

    async def _serveAsync(self, gameFactory):
        import websockets

        _startHttpServer(self._httpPort)
        print(f"Roam web server: http://localhost:{self._httpPort}/")
        print(f"  (WebSocket on ws://localhost:{self._wsPort})")
        print("Press Ctrl+C to stop.")

        async def handler(websocket):
            loop = asyncio.get_event_loop()
            session = WebSession(websocket, loop)

            def runGame():
                try:
                    gameFactory(session)
                except (SystemExit, KeyboardInterrupt):
                    pass
                except Exception:
                    import traceback

                    traceback.print_exc()
                finally:
                    session.quit()

            game_thread = threading.Thread(target=runGame, daemon=True)
            game_thread.start()
            await session.runIO()
            game_thread.join(timeout=3.0)

        async with websockets.serve(handler, "0.0.0.0", self._wsPort):
            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                pass


def _startHttpServer(port):
    """Serve web/index.html + game assets (assets/) over HTTP.

    Routes:
      /            → web/index.html
      /index.html  → web/index.html
      /assets/...  → <projectRoot>/assets/...   (tile sprites etc.)
      anything else → 404
    """
    webDir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "web")
    )
    rootDir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Closure-based handler so webDir / rootDir are captured without needing
    # instance state on the handler class.
    def _makeHandler(webDir, rootDir):
        class _Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=rootDir, **kwargs)

            def translate_path(self, path):
                from urllib.parse import unquote, urlparse

                path = unquote(urlparse(path).path)
                if path in ("/", "/index.html"):
                    return os.path.join(webDir, "index.html")
                # /assets/... served directly from project root
                return super().translate_path(path)

            def log_message(self, *args):
                pass

        return _Handler

    class _ReuseServer(http.server.HTTPServer):
        allow_reuse_address = True

    httpd = _ReuseServer(("", port), _makeHandler(webDir, rootDir))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def createWebFrontend(wsPort=_DEFAULT_WS_PORT, httpPort=_DEFAULT_HTTP_PORT):
    return WebFrontend(wsPort=wsPort, httpPort=httpPort)
