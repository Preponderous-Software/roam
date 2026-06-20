import os
import sys

from rendering.renderer import Renderer
from rendering.textGrid import TextGrid
from ui.geometry import Rect
from ui.hotbarLayout import HOTBAR_BOTTOM_OFFSET, HOTBAR_PADDING

# Roguelike-style glyph table: image filename (no extension, lowercased) → char.
# Uppercase = dangerous / solid; lowercase = passive / harmless; symbols = terrain.
_GLYPHS = {
    # terrain
    "grass":                    ".",
    "stone":                    "#",
    "stonefloor":               "-",
    "woodfloor":                "_",
    "fence":                    "|",
    # flora
    "oakwood":                  "T",
    "junglewood":               "T",
    "leaves":                   "*",
    "wheat":                    '"',
    "wheatseed":                ",",
    "youngcrop":                ":",
    "maturecrop":               '"',
    # creatures  (uppercase = dangerous)
    "bear":                     "B",
    "bearonreproductioncooldown": "B",
    "wolf":                     "W",
    "snake":                    "~",
    "deer":                     "d",
    "rabbit":                   "r",
    "chicken":                  "c",
    "chickenonreproductioncooldown": "c",
    # items / food
    "bearmeat":                 "%",
    "chickenmeat":              "%",
    "apple":                    "a",
    "banana":                   "b",
    # furniture / structures
    "chest":                    "[",
    "gravestone":               "+",
    "campfire":                 "^",
    "torch":                    "!",
    "bed":                      "=",
    "stonebed":                 "=",
    # ores
    "coalore":                  "o",
    "ironore":                  "O",
    # misc
    "excrement":                "x",
}

# ANSI foreground color codes per glyph. Standard 8-color palette (codes 30-37,
# 90-97) so they work on every terminal without capability queries.
# Mnemonic: green = nature, yellow = passive/warm, red = dangerous, gray = stone.
_GLYPH_COLORS = {
    "@": 93,   # player        — bright yellow
    ".": 32,   # grass         — green
    "#": 37,   # stone         — white/light-gray
    "-": 90,   # stone floor   — dark gray
    "_": 33,   # wood floor    — yellow-brown
    "|": 33,   # fence         — yellow-brown
    "T": 32,   # trees         — green
    "*": 32,   # leaves        — green
    '"': 33,   # wheat/crop    — yellow
    ",": 33,   # seed          — yellow
    ":": 32,   # young crop    — green
    "B": 31,   # bear          — red
    "W": 91,   # wolf          — bright red
    "~": 32,   # snake         — green
    "d": 33,   # deer          — yellow
    "r": 37,   # rabbit        — white
    "c": 37,   # chicken       — white
    "%": 31,   # meat          — red
    "a": 91,   # apple         — bright red
    "b": 93,   # banana        — bright yellow
    "[": 33,   # chest         — yellow
    "+": 37,   # gravestone    — white
    "^": 91,   # campfire      — bright red
    "!": 93,   # torch         — bright yellow
    "=": 36,   # bed           — cyan
    "o": 90,   # coal ore      — dark gray
    "O": 37,   # iron ore      — white
    "x": 33,   # excrement     — yellow
}


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
        if frame == self._lastFrame:
            return
        newLines = frame.split("\n")
        oldLines = self._lastFrame.split("\n") if self._lastFrame is not None else []
        self._output(_buildDiff(newLines, oldLines))
        self._lastFrame = frame

    def setCaption(self, text):
        self._caption = text

    def getGameAreaRect(self):
        width, height = self.getDisplaySize()
        # Reserve bottom rows for the HUD (hotbar + status box + energy bar).
        # Mirror the pixel formulae in Status.getDefaultRect() and EnergyBar so
        # the game world is always drawn above — not behind — the HUD elements.
        statusBoxHeight = height // 10          # matches Status: height = y / 10
        hudHeight = (HOTBAR_BOTTOM_OFFSET       # hotbar + energy-bar zone
                     + HOTBAR_PADDING           # gap above hotbar
                     + statusBoxHeight          # status box
                     + 10)                      # margin between status and hotbar
        availHeight = max(self.cellHeight, height - hudHeight)
        side = min(width, availHeight)
        return Rect((width - side) // 2, 0, side, side)

    # --- drawing primitives ---

    def drawRectangle(self, xpos, ypos, width, height, color):
        # Fill with spaces so background calls (location tiles, energy bar
        # backdrop, hotbar panel) don't leave box-outline noise on the grid.
        # drawButton() handles its own box, so UI elements are unaffected.
        self.grid.fillRect(
            self._col(xpos),
            self._row(ypos),
            self._cellsWide(width),
            self._cellsHigh(height),
            " ",
        )

    def drawText(self, text, xpos, ypos, size, color):
        col = self._col(xpos) - len(text) // 2
        row = self._row(ypos)
        self.grid.writeText(col, row, text)
        # Clear per-cell colors so text is always readable over overlays
        # (drawTranslucentOverlay dims cells to dark-grey; clearing restores
        # them to the terminal default foreground).
        for offset in range(len(text)):
            self.grid.setColor(col + offset, row, None)

    def drawTextLeftAligned(self, text, leftX, centerY, size, color):
        col = self._col(leftX)
        row = self._row(centerY)
        self.grid.writeText(col, row, text)
        for offset in range(len(text)):
            self.grid.setColor(col + offset, row, None)

    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        column, row = self._col(xpos), self._row(ypos)
        cellsWide, cellsHigh = self._cellsWide(width), self._cellsHigh(height)
        self.grid.drawBox(column, row, cellsWide, cellsHigh)
        labelColumn = column + (cellsWide - len(text)) // 2
        self.grid.writeText(labelColumn, row + cellsHigh // 2, text)

    def drawTranslucentOverlay(self, color):
        # Simulate the darkness backdrop by dimming every cell to dark grey.
        # Subsequent drawText calls clear per-cell colors so overlay text
        # (YOU DIED, PAUSED) stays readable in the terminal default foreground.
        for r in range(self.grid.rows):
            for c in range(self.grid.columns):
                self.grid.setColor(c, r, 90)  # ANSI dark grey

    def drawDayNightOverlay(self, gameAreaRect, opacity, lightSources):
        # Approximate the darkness overlay by dimming cells in the game area.
        # Light sources (torches, campfires) punch bright spots.
        if opacity <= 30:
            return
        gx, gy, gw, gh = gameAreaRect
        startCol = self._col(gx)
        startRow = self._row(gy)
        endCol = min(self.columns, self._col(gx + gw) + 1)
        endRow = min(self.rows, self._row(gy + gh) + 1)
        # Normalise: 0.0 (opacity 30) → 1.0 (opacity 200)
        darkness = (opacity - 30) / 170.0
        halfW = self.cellWidth / 2
        halfH = self.cellHeight / 2
        for row in range(startRow, endRow):
            py = row * self.cellHeight + halfH
            for col in range(startCol, endCol):
                px = col * self.cellWidth + halfW
                litFraction = 0.0
                for lx, ly, lRadius in lightSources:
                    if lRadius <= 0:
                        continue
                    dist = ((px - lx) ** 2 + (py - ly) ** 2) ** 0.5
                    if dist < lRadius:
                        litFraction = max(litFraction, 1.0 - dist / lRadius)
                effectiveDark = darkness * (1.0 - litFraction)
                if effectiveDark < 0.2:
                    pass  # well-lit: no change
                elif effectiveDark < 0.65:
                    self.grid.setColor(col, row, 90)  # dark grey
                else:
                    self.grid.setColor(col, row, 30)  # near-black

    def drawImage(self, image, position):
        # `image` is a one-glyph handle from loadImage; `position` is (x, y) or a
        # rect-like with .x/.y. Place the glyph at the mapped cell.
        x = position[0] if not hasattr(position, "x") else position.x
        y = position[1] if not hasattr(position, "y") else position.y
        glyph = image if isinstance(image, str) and image else "#"
        col, row = self._col(x), self._row(y)
        self.grid.setChar(col, row, glyph[0])
        color = _GLYPH_COLORS.get(glyph[0])
        if color is not None:
            self.grid.setColor(col, row, color)

    def loadImage(self, path):
        # Map each asset to a distinct, meaningful ASCII glyph so the text
        # mode reads like a classic roguelike rather than scattered initials.
        name = os.path.splitext(os.path.basename(str(path)))[0].lower()
        if name.startswith("player"):
            return "@"
        glyph = _GLYPHS.get(name)
        if glyph:
            return glyph
        # Fallback: first letter, uppercase, for any unrecognised asset.
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

    def supportsImageLoading(self):
        return False

    # --- clipping / render target / screenshots (no terminal analogue) ---

    def setClipRegion(self, rect):
        pass

    def getRenderTarget(self):
        return self._renderTarget

    def setRenderTarget(self, target):
        self._renderTarget = target

    def captureScreenshot(self):
        pass

    def drawSelectionHighlight(self, x, y, width, height, color):
        # Highlight the selected slot by recoloring its cells bright yellow.
        # Using fillRect (spaces) would erase the glyphs already drawn there.
        col = self._col(x)
        row = self._row(y)
        cellsWide = max(1, self._cellsWide(width))
        cellsHigh = max(1, self._cellsHigh(height))
        for r in range(row, row + cellsHigh):
            for c in range(col, col + cellsWide):
                self.grid.setColor(c, r, 93)  # bright yellow


def _buildDiff(newLines, oldLines):
    """Return an ANSI escape sequence that updates only the lines that changed.

    On the first call (oldLines=[]), homes the cursor and rewrites every row
    followed by erase-to-EOL (\033[K), then erases below (\033[J).  This
    clears any pre-game content without a blank-screen flash.

    On subsequent calls, only the lines whose content changed are repositioned
    with \033[row;1H and rewritten, each followed by \033[K to wipe stale
    trailing characters.  Lines that are identical to the previous frame are
    left untouched — the terminal keeps them with zero bandwidth cost.

    Neither path uses \033[2J (full clear), so the terminal never shows a
    blank frame between repaints — that was the root cause of the choppiness
    reported on Userland on Android.
    """
    parts = []
    if not oldLines:
        # First render: home cursor, overwrite every row, then clear below.
        parts.append("\033[H")
        for line in newLines:
            parts.append(line + "\033[K\r\n")
        parts.append("\033[J")
    else:
        # Differential update: rewrite only rows that changed.
        for i, line in enumerate(newLines):
            old = oldLines[i] if i < len(oldLines) else None
            if line != old:
                # \033[row;1H  — move to start of that row (1-based)
                # line         — new content (may include ANSI color codes)
                # \033[K       — erase from cursor to end of line
                parts.append(f"\033[{i + 1};1H{line}\033[K")
        # Blank rows that existed in the old frame but not in the new one.
        for i in range(len(newLines), len(oldLines)):
            parts.append(f"\033[{i + 1};1H\033[2K")
    return "".join(parts)


def _printToTerminal(diff):
    # diff is a pre-built ANSI sequence from _buildDiff; just emit and flush.
    if diff:
        sys.stdout.write(diff)
        sys.stdout.flush()
