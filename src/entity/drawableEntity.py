import pygame
from lib.pyenvlib.entity import Entity
from gameLogging.logger import getLogger
from ui import palette

_logger = getLogger(__name__)


# @author Daniel McCoy Stephenson
# @since August 5th, 2022
class DrawableEntity(Entity):
    _imageCache = {}
    _FALLBACK_SIZE = 32

    def __init__(self, name, imagePath, solid=False):
        Entity.__init__(self, name)
        self.imagePath = imagePath
        self.solid = solid

    def isSolid(self):
        return self.solid

    def getImage(self):
        if self.imagePath not in DrawableEntity._imageCache:
            try:
                DrawableEntity._imageCache[self.imagePath] = pygame.image.load(
                    self.imagePath
                )
            except (pygame.error, FileNotFoundError) as e:
                _logger.warning(
                    "failed to load image asset; using placeholder",
                    imagePath=self.imagePath,
                    error=str(e),
                )
                DrawableEntity._imageCache[
                    self.imagePath
                ] = DrawableEntity._createFallbackSurface()
        return DrawableEntity._imageCache[self.imagePath]

    @staticmethod
    def _createFallbackSurface():
        # A visibly-wrong magenta square so a missing asset is obvious in-game
        # rather than crashing the render loop. Cached per path so the failing
        # load is not retried and the warning is logged only once.
        size = DrawableEntity._FALLBACK_SIZE
        surface = pygame.Surface((size, size))
        surface.fill(palette.DEBUG_MAGENTA)
        return surface

    def getImagePath(self):
        return self.imagePath

    def setImagePath(self, imagePath):
        self.imagePath = imagePath
