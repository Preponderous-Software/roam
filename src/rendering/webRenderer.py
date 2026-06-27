from rendering.textRenderer import TextRenderer, _buildDiff

_DEFAULT_COLUMNS = 120
_DEFAULT_ROWS = 36


# @author Daniel McCoy Stephenson
# @since June 27th, 2026
#
# WebSocket implementation of Renderer (web-frontend epic). Inherits all of
# TextRenderer's drawing logic unchanged; the only override is present(), which
# sends the ANSI diff to the connected browser via a thread-safe callback
# instead of writing to stdout. The callback is provided by WebSession so the
# renderer itself is unaware of asyncio.
class WebRenderer(TextRenderer):
    def __init__(self, sendCallback, columns=_DEFAULT_COLUMNS, rows=_DEFAULT_ROWS):
        super().__init__(columns=columns, rows=rows)
        self._sendCallback = sendCallback

    def present(self):
        frame = self.grid.toString()
        if frame == self._lastFrame:
            return
        newLines = frame.split("\n")
        oldLines = self._lastFrame.split("\n") if self._lastFrame is not None else []
        diff = _buildDiff(newLines, oldLines)
        self._lastFrame = frame
        if diff:
            self._sendCallback(diff)
