import asyncio
import functools
import http.server
import os
import re
import threading

from rendering.inputEvent import EventType, InputEvent
from rendering.textClock import TextClock
from rendering.webInputSource import WebInputSource
from rendering.webRenderer import WebRenderer, _DEFAULT_COLUMNS, _DEFAULT_ROWS

# CSI 8 ; <rows> ; <cols> t  — the standard xterm window-resize report that
# xterm-addon-fit sends to tell the server its computed terminal dimensions.
_RESIZE_RE = re.compile(r"\x1b\[8;(\d+);(\d+)t")

_DEFAULT_WS_PORT = 8765
_DEFAULT_HTTP_PORT = 8080


# @author Daniel McCoy Stephenson
# @since June 27th, 2026
#
# Per-connection frontend: owns one WebRenderer + WebInputSource + TextClock for
# a single browser session.  Implements the same interface as PygameFrontend /
# TextFrontend (getRenderer, getInputSource, getClock, setCaption, reset, quit)
# so Roam.__init__ can accept it as a drop-in frontend.  Thread-safe I/O is
# handled by _enqueueFrame (game thread → asyncio send queue) and feed()
# (asyncio receive → input queue).
class WebSession:
    def __init__(self, websocket, loop):
        self._websocket = websocket
        self._loop = loop
        self._stopped = threading.Event()
        self._build()

    def _build(self):
        self._sendQueue = asyncio.Queue()
        self._renderer = WebRenderer(self._enqueueFrame)
        self._inputSource = WebInputSource()
        self._clock = TextClock()

    def _enqueueFrame(self, data):
        asyncio.run_coroutine_threadsafe(self._sendQueue.put(data), self._loop)

    def feedInput(self, data):
        # Intercept the xterm resize report (CSI 8 ; rows ; cols t) before it
        # reaches the ANSI key parser — it's a terminal control sequence, not a
        # keystroke.  The renderer's resize() forces a full redraw at the new size.
        m = _RESIZE_RE.fullmatch(data.strip())
        if m:
            rows, cols = int(m.group(1)), int(m.group(2))
            if cols > 0 and rows > 0:
                self._renderer.resize(cols, rows)
                # Mirror what TextFrontend does on SIGWINCH: queue a WINDOW_RESIZE
                # event so screens recalculate their pixel layout for the new size.
                self._inputSource.queueEvent(
                    InputEvent(EventType.WINDOW_RESIZE, size=(cols, rows))
                )
            return
        self._inputSource.feed(data)

    # --- Frontend interface (mirrors PygameFrontend / TextFrontend) ---

    def getRenderer(self):
        return self._renderer

    def getInputSource(self):
        return self._inputSource

    def getClock(self):
        return self._clock

    def setCaption(self, caption):
        self._renderer.setCaption(caption)

    def reset(self):
        # Rebuild renderer/input for a fresh game session (return-to-main-menu),
        # keeping the same _enqueueFrame callback so the WebSocket is unchanged.
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
#   - HTTP on httpPort: serves web/index.html so players can open a browser URL.
#   - WebSocket on wsPort: each connection spawns a WebSession + a game thread.
#
# gameFactory(session) is called in a daemon thread per connection; it should
# run the full Roam game loop and return (or raise SystemExit) when the session
# ends.  Multiple concurrent sessions are supported — each gets its own
# independent game state.
class WebFrontend:
    def __init__(self, wsPort=_DEFAULT_WS_PORT, httpPort=_DEFAULT_HTTP_PORT):
        self._wsPort = wsPort
        self._httpPort = httpPort

    def serve(self, gameFactory):
        """Block until Ctrl+C, accepting WebSocket connections and running a
        game session per connection."""
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
    """Serve web/ over HTTP on a background daemon thread."""
    webDir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "web")
    )

    class _QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=webDir, **kwargs)

        def log_message(self, format, *args):
            pass

    class _ReuseServer(http.server.HTTPServer):
        allow_reuse_address = True

    httpd = _ReuseServer(("", port), _QuietHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def createWebFrontend(wsPort=_DEFAULT_WS_PORT, httpPort=_DEFAULT_HTTP_PORT):
    return WebFrontend(wsPort=wsPort, httpPort=httpPort)
