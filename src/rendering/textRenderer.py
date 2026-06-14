import os
import sys

from rendering.renderer import Renderer
from rendering.textGrid import TextGrid
from ui.geometry import Rect


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Text/terminal implementation of the Renderer interface (frontend-abstraction
# epic #433, the text-UI payoff #239). The game draws in pixel space; this
# renderer maps those coordinates onto a character grid (cellWidth x cellHeight
# pixels per cell) and prints the grid to the terminal. Pixel-graphics effects
# that have no terminal analogue (translucent overlays, offscreen surfaces,
# screenshots) degrade to no-ops; images become a single glyph. The whole run
# loop, layout math, menus and text render faithfully.
class TextRenderer(Renderer):
    def __init__(self, columns=80, rows=24, cellWidth=8, cellHeight=16, output=None):
        self.columns = columns
        self.rows = rows
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        self.grid = TextGrid(columns, rows)
        self._caption = "Roam"
        self._renderTarget = self.grid
        self._lastFrame = None
        # present() writes here; defaults to a terminal repaint. Tests inspect
        # self.grid directly and need no output.
        self._output = output if output is not None else _printToTerminal

    # --- pixel -> cell mapping ---

    def _col(self, x):
        return int(x // self.cellWidth)

    def _row(self, y):
        return int(y // self.cellHeight)

    def _cellsWide(self, width):
        return max(1, int(width // self.cellWidth))

    def _cellsHigh(self, height):
        return max(1, int(height // self.cellHeight))

    # --- display lifecycle ---

    def getDisplaySize(self):
        return (self.columns * self.cellWidth, self.rows * self.cellHeight)

    def getDisplayWidth(self):
        return self.columns * self.cellWidth

    def getDisplayHeight(self):
        return self.rows * self.cellHeight

    def clearScreen(self, color):
        self.grid.clear()

    def present(self):
        # Only repaint when the frame actually changed, so a static screen
        # (e.g. a menu polled every loop) doesn't flood the terminal.
        frame = self.grid.toString()
        if frame != self._lastFrame:
            self._output(frame)
            self._lastFrame = frame

    def setCaption(self, text):
        self._caption = text

    def getGameAreaRect(self):
        width, height = self.getDisplaySize()
        side = min(width, height)
        return Rect((width - side) // 2, (height - side) // 2, side, side)

    # --- drawing primitives ---

    def drawRectangle(self, xpos, ypos, width, height, color):
        # An outlined box reads better in a terminal than a flooded fill.
        self.grid.drawBox(
            self._col(xpos),
            self._row(ypos),
            self._cellsWide(width),
            self._cellsHigh(height),
        )

    def drawText(self, text, xpos, ypos, size, color):
        column = self._col(xpos) - len(text) // 2
        self.grid.writeText(column, self._row(ypos), text)

    def drawTextLeftAligned(self, text, leftX, centerY, size, color):
        self.grid.writeText(self._col(leftX), self._row(centerY), text)

    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        column, row = self._col(xpos), self._row(ypos)
        cellsWide, cellsHigh = self._cellsWide(width), self._cellsHigh(height)
        self.grid.drawBox(column, row, cellsWide, cellsHigh)
        labelColumn = column + (cellsWide - len(text)) // 2
        self.grid.writeText(labelColumn, row + cellsHigh // 2, text)

    def drawTranslucentOverlay(self, color):
        # No per-cell alpha; any banner text drawn over it still shows.
        pass

    def drawDayNightOverlay(self, gameAreaRect, opacity, lightSources):
        # No per-pixel alpha/blend in a terminal; the day/night dimming and
        # light masks are skipped (the world still renders, just unshaded).
        pass

    def drawImage(self, image, position):
        # `image` is a one-glyph handle from loadImage; `position` is (x, y) or a
        # rect-like with .x/.y. Place the glyph at the mapped cell.
        x = position[0] if not hasattr(position, "x") else position.x
        y = position[1] if not hasattr(position, "y") else position.y
        glyph = image if isinstance(image, str) and image else "#"
        self.grid.setChar(self._col(x), self._row(y), glyph[0])

    def loadImage(self, path):
        # Collapse an asset to a single representative glyph.
        name = os.path.splitext(os.path.basename(str(path)))[0].lower()
        if name.startswith("player"):
            return "@"
        return name[0].upper() if name else "#"

    def scaleImage(self, image, size):
        return image

    def createSurface(self, size):
        # No offscreen pixel buffer in text; return an opaque sentinel grid.
        return TextGrid(1, 1)

    def saveImage(self, image, path):
        pass

    def tryLoadImage(self, path):
        return None

    # --- clipping / render target / screenshots (no terminal analogue) ---

    def setClipRegion(self, rect):
        pass

    def getRenderTarget(self):
        return self._renderTarget

    def setRenderTarget(self, target):
        self._renderTarget = target

    def captureScreenshot(self):
        pass


def _printToTerminal(frame):
    # Clear the screen and home the cursor, then paint the frame.
    sys.stdout.write("\033[2J\033[H" + frame + "\n")
    sys.stdout.flush()
