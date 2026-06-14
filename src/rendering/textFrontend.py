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
class TextFrontend:
    def __init__(self, config: Config):
        self._config = config
        self._terminalState = None
        self._enterCbreakMode()
        self._build()

    def _build(self):
        self._renderer = TextRenderer()
        self._inputSource = TextInputSource()
        self._clock = TextClock()

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
