from rendering.textRenderer import TextRenderer, _buildDiff

_DEFAULT_COLUMNS = 120
_DEFAULT_ROWS = 36


# @author Daniel McCoy Stephenson
# @since June 27th, 2026
#
# WebSocket implementation of Renderer (web-frontend epic). Inherits all of
# TextRenderer's drawing logic unchanged; the main overrides are:
#   - present(): sends the ANSI diff to the browser via a thread-safe callback
#   - drawButton(): mirrors PygameRenderer's hit-test logic so tapping a button
#     in the browser calls its callback, just like clicking in pygame does.
#
# The inputSource reference is injected by WebSession so drawButton() can read
# mouse state without going through pygame.  It is only used during drawing
# (same pattern as PygameRenderer.drawButton), so the coupling is narrow.
class WebRenderer(TextRenderer):
    def __init__(
        self,
        sendCallback,
        columns=_DEFAULT_COLUMNS,
        rows=_DEFAULT_ROWS,
        inputSource=None,
    ):
        super().__init__(columns=columns, rows=rows)
        self._sendCallback = sendCallback
        self._inputSource = inputSource

    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        super().drawButton(
            xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
        )
        if self._inputSource is None:
            return
        mx, my = self._inputSource.getMousePosition()
        mb = self._inputSource.getMouseButtons()
        if mb[0] and xpos <= mx < xpos + width and ypos <= my < ypos + height:
            # Consume the click immediately so the callback isn't called again
            # on the next frame before the mouse_up message arrives (~80 ms).
            self._inputSource.consumeLeftClick()
            function()

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
