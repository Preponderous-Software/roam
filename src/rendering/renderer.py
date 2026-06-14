from abc import ABC, abstractmethod


# @author Daniel McCoy Stephenson
# @since June 13th, 2026
#
# Backend-neutral drawing interface for Roam (frontend-abstraction epic #433).
#
# Screens and HUD widgets depend on this interface rather than on pygame so the
# same game logic can drive multiple frontends (pygame today; text/web later).
# The pygame implementation is rendering/pygameRenderer.py; a future frontend
# implements the same methods against its own backend. Colors are the plain
# (R, G, B) tuples from ui/palette.py.
class Renderer(ABC):
    # --- display surface lifecycle ---

    @abstractmethod
    def getDisplaySize(self):
        """Return the display size as a (width, height) tuple."""

    @abstractmethod
    def getDisplayWidth(self):
        """Return the display width in pixels."""

    @abstractmethod
    def getDisplayHeight(self):
        """Return the display height in pixels."""

    @abstractmethod
    def clearScreen(self, color):
        """Fill the entire display with a single color."""

    @abstractmethod
    def present(self):
        """Flush the frame drawn so far to the screen."""

    @abstractmethod
    def setCaption(self, text):
        """Set the application window caption."""

    # --- drawing primitives ---

    @abstractmethod
    def drawRectangle(self, xpos, ypos, width, height, color):
        """Draw a filled rectangle."""

    @abstractmethod
    def drawText(self, text, xpos, ypos, size, color):
        """Draw text centered on (xpos, ypos)."""

    @abstractmethod
    def drawTextLeftAligned(self, text, leftX, centerY, size, color):
        """Draw text with its left edge at leftX, vertically centered on centerY.
        Text metrics stay inside the backend so callers need no pixel math."""

    @abstractmethod
    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        """Draw an immediate-mode button and invoke function when clicked."""

    @abstractmethod
    def drawTranslucentOverlay(self, color):
        """Fill the whole display with a translucent (R, G, B, A) color — e.g. a
        pause/death dimming layer. Backends without alpha may approximate or
        skip it."""

    @abstractmethod
    def drawImage(self, image, position):
        """Draw an image at position (an (x, y) tuple or a rect-like dest)."""

    @abstractmethod
    def loadImage(self, path):
        """Load (and cache) a static image asset by path, returning an opaque
        image handle. A missing/unreadable asset yields a visible placeholder
        rather than raising, so a bad asset is obvious in-game."""

    @abstractmethod
    def scaleImage(self, image, size):
        """Return a copy of image scaled to size (a (width, height) tuple)."""

    @abstractmethod
    def getGameAreaRect(self):
        """Return the centered square play-area rect for the current display."""

    # --- region clipping ---

    @abstractmethod
    def setClipRegion(self, rect):
        """Restrict drawing to rect; pass None to clear the clip region."""

    # --- offscreen render target ---

    @abstractmethod
    def getRenderTarget(self):
        """Return an opaque handle to the current drawing target (for save/restore)."""

    @abstractmethod
    def setRenderTarget(self, target):
        """Redirect subsequent drawing to target (an opaque handle from
        getRenderTarget, or a backend surface) so a frame can be rendered
        off-screen; pass the saved handle back to restore the display."""

    # --- screenshots ---

    @abstractmethod
    def captureScreenshot(self):
        """Save a screenshot of the current frame to the screenshots folder."""
