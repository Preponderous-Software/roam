from config.config import Config
from rendering.textClock import TextClock
from rendering.textInputSource import TextInputSource
from rendering.textRenderer import TextRenderer


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Text/terminal frontend (frontend-abstraction epic #433, text-UI #239). The
# counterpart to PygameFrontend: it builds the three interface implementations
# the game depends on and hands them back, with no pygame and no window. This is
# the concrete demonstration that a second frontend is two classes plus a
# factory branch — no game-logic change.
class TextFrontend:
    def __init__(self, config: Config):
        self._config = config
        self._build()

    def _build(self):
        self._renderer = TextRenderer()
        self._inputSource = TextInputSource()
        self._clock = TextClock()

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
        pass


def createTextFrontend(config: Config) -> TextFrontend:
    return TextFrontend(config)
