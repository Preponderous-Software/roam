import pygame

from lib.graphik.src.graphik import Graphik
from rendering.renderer import Renderer
from screen.screenshotHelper import takeScreenshot


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

    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        self.graphik.drawButton(
            xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
        )

    def drawImage(self, image, position):
        self._display().blit(image, position)

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
