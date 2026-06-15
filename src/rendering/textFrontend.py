import os
import sys

from config.config import Config
from rendering.textClock import TextClock
from rendering.textInputSource import TextInputSource
from rendering.textRenderer import TextRenderer


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Text/terminal frontend (frontend-abstraction epic #433, text-UI #239). The
# counterpart to PygameFrontend: it builds the three interface implementations
# the game depends on and hands them back, with no pygame and no window. It also
# owns the terminal lifecycle — putting the TTY into cbreak mode so single
# keystrokes reach the game without Enter, and restoring it on quit. This is the
# concrete demonstration that a second frontend is a few classes plus a factory
# branch — no game-logic change.
#
# Known limitations / UX divergences from the pygame frontend
# -----------------------------------------------------------
# INPUT
#   - No mouse. getMousePosition() always returns (0, 0) and getMouseButtons()
#     always returns (False, False, False). As a result:
#       * Gather (left-click): use G to gather from the tile in front of you.
#       * Place (right-click): use F to place/interact with the tile in front of you.
#       * Hotbar slots cannot be clicked; use 1–0 keys instead.
#       * HUD elements (hotbar, minimap, status) cannot be dragged.
#       * The "hover over a tile to show its name" status tooltip always reads
#         whatever entity is at grid cell (0, 0).
#       * The scroll wheel cannot cycle the hotbar; use 1–0 or [ ] instead.
#   - No held-key state. isPressed() always returns False, so Run (hold Shift)
#     and Crouch (hold Ctrl) have no effect. Each directional keypress moves
#     the player exactly one tile (a synthetic KEY_UP follows each movement
#     KEY_DOWN to prevent OS key-repeat from causing continuous walking).
#   - Terminal resize mid-session is not detected. The grid is sized once at
#     startup from os.get_terminal_size(); restart the game after resizing.
#
# RENDERING
#   - No day/night overlay. drawDayNightOverlay() is a no-op, so the world
#     always appears fully lit regardless of the in-game time of day.
#   - No minimap. tryLoadImage() returns None so the minimap never renders,
#     and saveImage() is a no-op so room PNGs are never written — the map
#     image file is never generated either.
#   - No screenshots. captureScreenshot() is a no-op.
#   - No translucent overlays. The death and pause screens show their text
#     banners but not the darkening dim layer behind them.
#   - No colour. All glyphs are the same terminal foreground colour; entities
#     that differ only by colour (e.g. day-phase indicators) look identical.
#   - One glyph per tile. Only the topmost entity on a location is shown; a
#     grass tile covered by stone covered by the player shows only '@'.
#
# HUD LAYOUT
#   - The hotbar, status box, and energy bar are positioned using pixel offsets
#     designed for the graphical build (HOTBAR_BOTTOM_OFFSET = 150 px). On a
#     small terminal they may overlap the game-world area rather than sitting
#     below it. The energy number is always visible on the last row; the hotbar
#     items appear as glyphs wherever the pixel math maps them.
class TextFrontend:
    def __init__(self, config: Config):
        self._config = config
        self._terminalState = None
        self._enterCbreakMode()
        self._build()

    def _build(self):
        self._renderer = TextRenderer(columns=self._termCols(), rows=self._termRows())
        self._inputSource = TextInputSource()
        self._clock = TextClock()

    def _termCols(self):
        try:
            cols = os.get_terminal_size().columns
            return cols if cols > 0 else 80
        except OSError:
            return 80

    def _termRows(self):
        try:
            lines = os.get_terminal_size().lines
            return lines if lines > 0 else 24
        except OSError:
            return 24

    def _enterCbreakMode(self):
        # Non-canonical, no-echo input so keystrokes arrive immediately. Skipped
        # when stdin is not a real terminal (tests, pipes) — and a no-op on
        # platforms without termios (e.g. Windows), where the default line input
        # still works.
        try:
            if not sys.stdin.isatty():
                return
            import termios
            import tty

            self._terminalState = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except (ImportError, OSError, ValueError):
            self._terminalState = None

    def reset(self):
        self._build()

    def getRenderer(self):
        return self._renderer

    def getInputSource(self):
        return self._inputSource

    def getClock(self):
        return self._clock

    def setCaption(self, caption):
        self._renderer.setCaption(caption)

    def quit(self):
        if self._terminalState is not None:
            import termios

            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._terminalState)
            self._terminalState = None


def createTextFrontend(config: Config) -> TextFrontend:
    return TextFrontend(config)
