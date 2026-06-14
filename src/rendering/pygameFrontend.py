import pygame

from config.config import Config
from lib.graphik.src.graphik import Graphik
from rendering.pygameInputSource import PygameInputSource
from rendering.pygameRenderer import PygameRenderer

_ICON_PATH = "assets/images/player_down.png"


# @author Daniel McCoy Stephenson
# @since June 13th, 2026
#
# Owns the pygame window lifecycle (frontend-abstraction epic #433): library
# init, display-mode selection, window icon/caption, and teardown. It builds and
# hands back the Renderer the game draws through, so the rest of the game
# depends only on that interface. Selecting a different frontend (text, web)
# would mean providing an analogous factory that returns its own Renderer — no
# game/screen code would change.
class PygameFrontend:
    def __init__(self, config: Config):
        self._config = config
        pygame.init()
        pygame.display.set_icon(pygame.image.load(_ICON_PATH))
        self._inputSource = PygameInputSource()
        self._buildRenderer()

    def _buildRenderer(self):
        self._graphik = Graphik(self._createDisplaySurface())
        self._renderer = PygameRenderer(self._graphik)

    def _createDisplaySurface(self):
        mode = pygame.FULLSCREEN if self._config.fullscreen else pygame.RESIZABLE
        return pygame.display.set_mode(
            (self._config.displayWidth, self._config.displayHeight), mode
        )

    def reset(self):
        """Rebuild the window surface and renderer for a fresh game session
        (return-to-main-menu), mirroring the per-session re-initialization the
        DI container performs."""
        self._buildRenderer()

    def getRenderer(self):
        return self._renderer

    def getInputSource(self):
        return self._inputSource

    def getGraphik(self):
        return self._graphik

    def setCaption(self, caption):
        pygame.display.set_caption(caption)

    def quit(self):
        pygame.quit()


def createFrontend(config: Config) -> PygameFrontend:
    return PygameFrontend(config)
