import math

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
        # Day/night compositing caches (moved off worldScreen so the effect is
        # entirely the backend's concern): radial light masks by radius, masks
        # pre-scaled by (radius, opacity), and the reused overlay surface.
        self._lightMaskCache = {}
        self._scaledMaskCache = {}
        self._dayNightOverlay = None
        self._dayNightOverlaySize = None

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

    def drawDayNightOverlay(self, gameAreaRect, opacity, lightSources):
        if opacity <= 0:
            return
        gx, gy, gw, gh = gameAreaRect
        size = (int(gw), int(gh))
        if self._dayNightOverlay is None or self._dayNightOverlaySize != size:
            self._dayNightOverlay = pygame.Surface(size, pygame.SRCALPHA)
            self._dayNightOverlaySize = size
            self._scaledMaskCache.clear()
        overlay = self._dayNightOverlay
        overlay.fill((0, 0, 0, opacity))
        for screenX, screenY, radiusPx in lightSources:
            if radiusPx <= 0:
                continue
            cacheKey = (radiusPx, opacity)
            scaledMask = self._scaledMaskCache.get(cacheKey)
            if scaledMask is None:
                scaledMask = self._dayNightLightMask(radiusPx).copy()
                scaledMask.fill(
                    (255, 255, 255, opacity), special_flags=pygame.BLEND_RGBA_MULT
                )
                self._scaledMaskCache[cacheKey] = scaledMask
            overlay.blit(
                scaledMask,
                (int(screenX - gx - radiusPx), int(screenY - gy - radiusPx)),
                special_flags=pygame.BLEND_RGBA_MIN,
            )
        self.drawImage(overlay, (gx, gy))

    def _dayNightLightMask(self, radiusPx):
        # Radial mask: (0,0,0,255) opaque at the edge, alpha 0 (lit) at the
        # centre. Blitted with BLEND_RGBA_MIN it punches a smooth circular hole
        # in the dimming overlay. Cached per radius (the per-pixel build is the
        # expensive part).
        if radiusPx <= 0:
            radiusPx = 1
        cached = self._lightMaskCache.get(radiusPx)
        if cached is not None:
            return cached
        size = radiusPx * 2
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 255))
        center = radiusPx
        radiusSq = radiusPx * radiusPx
        invRadius = 255.0 / radiusPx
        for y in range(size):
            dy = y - center
            dySq = dy * dy
            for x in range(size):
                dx = x - center
                distSq = dx * dx + dySq
                if distSq < radiusSq:
                    alpha = int(math.sqrt(distSq) * invRadius + 0.5)
                    mask.set_at((x, y), (0, 0, 0, alpha))
        self._lightMaskCache[radiusPx] = mask
        return mask

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
        return True
