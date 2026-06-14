import pygame

from gameLogging.logger import getLogger
from lib.graphik.src.graphik import Graphik
from rendering.renderer import Renderer
from rendering.screenshotHelper import takeScreenshot
from ui import palette

_logger = getLogger(__name__)

_FALLBACK_IMAGE_SIZE = 32


# @author Daniel McCoy Stephenson
# @since June 13th, 2026
#
# pygame implementation of the Renderer interface (frontend-abstraction epic
# #433). Composes the vendored Graphik primitive provider rather than modifying
# it: drawing primitives delegate to Graphik, and the display-surface lifecycle
# (clear/present/clip/blit/screenshot/caption) is handled here so screens never
# reach the raw pygame surface directly.
class PygameRenderer(Renderer):
    def __init__(self, graphik: Graphik):
        self.graphik = graphik
        self._imageCache = {}

    def _display(self):
        return self.graphik.getGameDisplay()

    # --- display surface lifecycle ---

    def getDisplaySize(self):
        return self._display().get_size()

    def getDisplayWidth(self):
        return self._display().get_width()

    def getDisplayHeight(self):
        return self._display().get_height()

    def clearScreen(self, color):
        self._display().fill(color)

    def present(self):
        pygame.display.update()

    def setCaption(self, text):
        pygame.display.set_caption(text)

    # --- drawing primitives (delegated to Graphik) ---

    def drawRectangle(self, xpos, ypos, width, height, color):
        self.graphik.drawRectangle(xpos, ypos, width, height, color)

    def drawText(self, text, xpos, ypos, size, color):
        self.graphik.drawText(text, xpos, ypos, size, color)

    def drawTextLeftAligned(self, text, leftX, centerY, size, color):
        font = pygame.font.Font("freesansbold.ttf", size)
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        rect.left = int(leftX)
        rect.centery = int(centerY)
        self.drawImage(surface, rect)

    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        self.graphik.drawButton(
            xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
        )

    def drawTranslucentOverlay(self, color):
        overlay = pygame.Surface(self.getDisplaySize(), pygame.SRCALPHA)
        overlay.fill(color)
        self.drawImage(overlay, (0, 0))

    def drawImage(self, image, position):
        self._display().blit(image, position)

    def loadImage(self, path):
        # Cached per path (game assets are static); a load failure is logged
        # once and replaced with a visible placeholder so a missing asset is
        # obvious in-game rather than crashing the render loop.
        if path not in self._imageCache:
            try:
                self._imageCache[path] = pygame.image.load(path)
            except (pygame.error, FileNotFoundError) as error:
                _logger.warning(
                    "failed to load image asset; using placeholder",
                    imagePath=path,
                    error=str(error),
                )
                self._imageCache[path] = self._createFallbackImage()
        return self._imageCache[path]

    def scaleImage(self, image, size):
        return pygame.transform.scale(image, size)

    def createSurface(self, size):
        return pygame.Surface(size)

    def saveImage(self, image, path):
        pygame.image.save(image, path)

    def tryLoadImage(self, path):
        try:
            return pygame.image.load(path)
        except (FileNotFoundError, pygame.error):
            return None

    @staticmethod
    def _createFallbackImage():
        surface = pygame.Surface((_FALLBACK_IMAGE_SIZE, _FALLBACK_IMAGE_SIZE))
        surface.fill(palette.DEBUG_MAGENTA)
        return surface

    def getGameAreaRect(self):
        return self.graphik.getGameAreaRect()

    # --- region clipping ---

    def setClipRegion(self, rect):
        self._display().set_clip(rect)

    # --- offscreen render target ---

    def getRenderTarget(self):
        return self.graphik.getGameDisplay()

    def setRenderTarget(self, target):
        # Swap the surface the composed Graphik draws onto, so anything that
        # renders through the shared Graphik (e.g. Room.draw) targets it too.
        self.graphik.gameDisplay = target

    # --- screenshots ---

    def captureScreenshot(self):
        takeScreenshot(self._display())
