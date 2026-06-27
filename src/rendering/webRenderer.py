import json

from rendering.renderer import Renderer
from ui.geometry import Rect

_DEFAULT_WIDTH = 800
_DEFAULT_HEIGHT = 600


class _OffscreenSurface:
    """Dummy surface for offscreen render targets (minimap PNG generation).

    Draw calls aimed at an offscreen surface are silently discarded.  The
    minimap feature requires saveImage() + tryLoadImage() round-trips that
    are no-ops in web mode, so rooms will generate without minimap tiles.
    """


# @author Daniel McCoy Stephenson
# @since June 27th, 2026
#
# JSON draw-call renderer for the web frontend.  Every drawing primitive
# appends a compact dict to self._calls; present() serialises the list to
# JSON and pushes it to the browser over WebSocket.  The browser replays the
# draw calls on an HTML5 canvas.
#
# supportsImageLoading() returns True so the game uses the full sprite/tile
# rendering path (same as pygame) instead of the text-mode glyph fallback.
# loadImage() returns the asset path string; the browser fetches the image
# from the HTTP server at /assets/... automatically on first use.
class WebRenderer(Renderer):
    _SCREEN = object()  # sentinel: render target is the main canvas

    def __init__(
        self,
        sendCallback,
        width=_DEFAULT_WIDTH,
        height=_DEFAULT_HEIGHT,
        inputSource=None,
    ):
        self._send = sendCallback
        self._w = int(width)
        self._h = int(height)
        self._inputSource = inputSource
        self._calls = []
        self._target = self._SCREEN
        self._lastPayload = None

    # ── display size ─────────────────────────────────────────────────────────

    def resize(self, width, height):
        self._w = int(width)
        self._h = int(height)

    def getDisplayWidth(self):
        return self._w

    def getDisplayHeight(self):
        return self._h

    def getDisplaySize(self):
        return (self._w, self._h)

    def getGameAreaRect(self):
        side = min(self._w, self._h)
        x = (self._w - side) // 2
        y = (self._h - side) // 2
        return Rect(x, y, side, side)

    # ── lifecycle ──────��─────────────────────────────��───────────────────────

    def supportsImageLoading(self):
        return True

    def setCaption(self, text):
        pass

    def captureScreenshot(self):
        return False

    def present(self):
        if self._target is not self._SCREEN or not self._calls:
            return
        payload = json.dumps(
            {"type": "frame", "w": self._w, "h": self._h, "calls": self._calls},
            separators=(",", ":"),
        )
        self._calls = []
        if payload == self._lastPayload:
            return
        self._lastPayload = payload
        self._send(payload)

    # ── clear ─────────────────────────────────────────────────────────────────

    def clearScreen(self, color):
        self._emit({"op": "clear", "color": _rgb(color)})

    # ── images ───��──────────────────────────────────────────────────────────��

    def loadImage(self, path):
        """Return the asset path; the browser fetches /assets/... via HTTP."""
        return path

    def tryLoadImage(self, path):
        """Minimap requires on-disk PNGs; not supported in web mode."""
        return None

    def scaleImage(self, image, size):
        path = image if isinstance(image, str) else image.get("path", "")
        return {"path": path, "w": int(size[0]), "h": int(size[1])}

    def drawImage(self, image, position):
        call = {"op": "img"}
        if isinstance(image, str):
            call["path"] = image
        else:
            call["path"] = image.get("path", "")
            if "w" in image:
                call["w"] = image["w"]
                call["h"] = image["h"]
        try:
            call["x"] = int(position[0])
            call["y"] = int(position[1])
        except (TypeError, KeyError):
            call["x"] = int(position.x)
            call["y"] = int(position.y)
        self._emit(call)

    def createSurface(self, size):
        return _OffscreenSurface()

    def saveImage(self, image, path):
        pass

    # ── drawing ─────��────────────────────────────────���───────────────────────

    def drawRectangle(self, x, y, w, h, color):
        self._emit(
            {
                "op": "rect",
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
                "color": _rgb(color),
            }
        )

    def drawText(self, text, x, y, size, color):
        self._emit(
            {
                "op": "text",
                "text": str(text),
                "x": int(x),
                "y": int(y),
                "size": int(size),
                "color": _rgb(color),
                "align": "c",
            }
        )

    def drawTextLeftAligned(self, text, x, y, size, color):
        self._emit(
            {
                "op": "text",
                "text": str(text),
                "x": int(x),
                "y": int(y),
                "size": int(size),
                "color": _rgb(color),
                "align": "l",
            }
        )

    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        self._emit(
            {
                "op": "button",
                "x": int(xpos),
                "y": int(ypos),
                "w": int(width),
                "h": int(height),
                "bc": _rgb(colorBox),
                "tc": _rgb(colorText),
                "text": text,
            }
        )
        if self._target is self._SCREEN and self._inputSource is not None:
            mx, my = self._inputSource.getMousePosition()
            mb = self._inputSource.getMouseButtons()
            if mb[0] and xpos <= mx < xpos + width and ypos <= my < ypos + height:
                self._inputSource.consumeLeftClick()
                function()

    def drawTranslucentOverlay(self, color):
        c = list(color[:3]) + [int(color[3]) if len(color) > 3 else 128]
        self._emit({"op": "overlay", "color": c})

    def drawDayNightOverlay(self, gameAreaRect, opacity, lightSources):
        try:
            gx, gy, gw, gh = (
                gameAreaRect.x,
                gameAreaRect.y,
                gameAreaRect.width,
                gameAreaRect.height,
            )
        except AttributeError:
            gx, gy, gw, gh = gameAreaRect
        self._emit(
            {
                "op": "daynight",
                "opacity": int(opacity),
                "lights": [[int(x), int(y), int(r)] for x, y, r in lightSources],
                "rect": [int(gx), int(gy), int(gw), int(gh)],
            }
        )

    # ── clip region ───���──────────────────────────────────────────────────────

    def setClipRegion(self, rect):
        if rect is None:
            self._emit({"op": "unclip"})
        else:
            self._emit(
                {
                    "op": "clip",
                    "x": int(rect.x),
                    "y": int(rect.y),
                    "w": int(rect.width),
                    "h": int(rect.height),
                }
            )

    # ── render target (offscreen suppressed for minimap) ─────────────────────

    def getRenderTarget(self):
        return self._target

    def setRenderTarget(self, target):
        self._target = target if target is not None else self._SCREEN

    # ── internal ─────────────────────────────────��───────────────────────────

    def _emit(self, call):
        if self._target is self._SCREEN:
            self._calls.append(call)
        # offscreen draw calls are silently discarded (minimap not supported)


def _rgb(color):
    return [int(color[0]), int(color[1]), int(color[2])]
