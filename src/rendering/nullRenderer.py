from rendering.renderer import Renderer


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# A headless, backend-neutral Renderer that draws nothing (frontend-abstraction
# epic #433, Phase 5). It exists to prove the seam: game/screen logic can run a
# full draw frame against the Renderer interface with no pygame and no real
# display. Drawing calls are no-ops; queries return sensible defaults so layout
# math resolves. Useful for tests and as the skeleton a real text/web Renderer
# fills in.
class NullRenderer(Renderer):
    def __init__(self, width=800, height=600):
        self._width = width
        self._height = height
        self._renderTarget = object()

    # --- display surface lifecycle ---

    def getDisplaySize(self):
        return (self._width, self._height)

    def getDisplayWidth(self):
        return self._width

    def getDisplayHeight(self):
        return self._height

    def clearScreen(self, color):
        pass

    def present(self):
        pass

    def setCaption(self, text):
        pass

    # --- drawing primitives ---

    def drawRectangle(self, xpos, ypos, width, height, color):
        pass

    def drawText(self, text, xpos, ypos, size, color):
        pass

    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        # Draw-only: a headless renderer produces no clicks, so the callback is
        # never invoked (mirrors the §5.1 "draw is pure" intent).
        pass

    def drawImage(self, image, position):
        pass

    def loadImage(self, path):
        # Opaque handle — the path itself stands in for a backend image.
        return path

    def scaleImage(self, image, size):
        return image

    def getGameAreaRect(self):
        side = min(self._width, self._height)
        xpos = (self._width - side) // 2
        ypos = (self._height - side) // 2
        return (xpos, ypos, side, side)

    # --- region clipping ---

    def setClipRegion(self, rect):
        pass

    # --- offscreen render target ---

    def getRenderTarget(self):
        return self._renderTarget

    def setRenderTarget(self, target):
        self._renderTarget = target

    # --- screenshots ---

    def captureScreenshot(self):
        pass
