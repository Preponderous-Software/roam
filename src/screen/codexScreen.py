import pygame
from appContainer import component
from codex.codex import Codex, ALL_LIVING_ENTITY_TYPES, ENTITY_IMAGE_PATHS
from config.config import Config
from config.keyBindings import KeyBindings
from rendering.renderer import Renderer
from screen.screenType import ScreenType
from gameLogging.logger import getLogger
from ui import palette

_logger = getLogger(__name__)


# @author Copilot
# @since April 20th, 2026
@component
class CodexScreen:
    def __init__(
        self,
        renderer: Renderer,
        config: Config,
        codex: Codex,
        keyBindings: KeyBindings,
    ):
        self.renderer = renderer
        self.config = config
        self.codex = codex
        self.keyBindings = keyBindings
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.returnScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.scrollOffset = 0
        self._imageCache = {}
        self._fontCache = {}

    def setReturnScreen(self, screenType):
        self.returnScreen = screenType

    def switchToReturnScreen(self):
        self.nextScreen = self.returnScreen
        self.changeScreen = True

    def drawTitle(self):
        x, y = self.renderer.getDisplaySize()
        self.renderer.drawText("Codex", x / 2, 25, 36, palette.WHITE)
        discoveredCount = len(self.codex.getDiscoveredEntities())
        totalCount = len(ALL_LIVING_ENTITY_TYPES)
        self.renderer.drawText(
            f"{discoveredCount} of {totalCount} discovered",
            x / 2,
            50,
            16,
            palette.MEDIUM_GRAY,
        )

    def _getEntityImage(self, entityName):
        if entityName not in self._imageCache:
            imagePath = ENTITY_IMAGE_PATHS.get(entityName)
            if imagePath is not None:
                try:
                    img = pygame.image.load(imagePath)
                    self._imageCache[entityName] = pygame.transform.scale(img, (32, 32))
                except (pygame.error, FileNotFoundError) as e:
                    _logger.error(
                        "failed to load codex entity image",
                        entity=entityName,
                        error=str(e),
                    )
                    self._imageCache[entityName] = None
            else:
                self._imageCache[entityName] = None
        return self._imageCache[entityName]

    def _getFont(self, size):
        if size not in self._fontCache:
            self._fontCache[size] = pygame.font.Font("freesansbold.ttf", size)
        return self._fontCache[size]

    def _drawTextLeftAligned(self, text, leftX, centerY, size, color):
        """Draw text left-aligned starting at leftX, vertically centered at centerY."""
        font = self._getFont(size)
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        rect.left = int(leftX)
        rect.centery = int(centerY)
        self.renderer.drawImage(surface, rect)

    def drawEntries(self):
        x, y = self.renderer.getDisplaySize()
        entries = ALL_LIVING_ENTITY_TYPES

        rowHeight = 45
        startY = 85
        imageSize = 32
        imageX = x * 0.25
        nameX = imageX + imageSize + 16

        visibleRows = max(1, int((y - startY - 80) / rowHeight))
        maxOffset = max(0, len(entries) - visibleRows)
        self.scrollOffset = max(0, min(self.scrollOffset, maxOffset))

        visibleEntries = entries[self.scrollOffset : self.scrollOffset + visibleRows]

        for i, entityName in enumerate(visibleEntries):
            rowY = startY + i * rowHeight
            discovered = self.codex.hasDiscovered(entityName)

            if discovered:
                # Draw entity image
                img = self._getEntityImage(entityName)
                if img is not None:
                    self.renderer.drawImage(img, (int(imageX), int(rowY + 2)))
                # Draw entity name left-aligned after the image
                self._drawTextLeftAligned(
                    entityName,
                    nameX,
                    rowY + rowHeight / 2,
                    22,
                    palette.WHITE,
                )
            else:
                # Undiscovered entry
                self._drawTextLeftAligned(
                    "???",
                    nameX,
                    rowY + rowHeight / 2,
                    22,
                    palette.DARK_GRAY,
                )

        if maxOffset > 0:
            scrollInfo = (
                str(self.scrollOffset + 1)
                + "-"
                + str(min(self.scrollOffset + visibleRows, len(entries)))
                + " of "
                + str(len(entries))
            )
            self.renderer.drawText(scrollInfo, x / 2, y - 70, 16, palette.MEDIUM_GRAY)
            self.renderer.drawText(
                "Scroll to see more", x / 2, y - 92, 14, palette.DIM_GRAY
            )

    def drawBackButton(self):
        x, y = self.renderer.getDisplaySize()
        buttonWidth = x / 5
        buttonHeight = 35
        bottomY = y - 45
        startX = (x - buttonWidth) / 2
        self.renderer.drawButton(
            startX,
            bottomY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
            20,
            "Back",
            self.switchToReturnScreen,
        )

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE or key == self.keyBindings.getKey("codex"):
            self.switchToReturnScreen()

    def handleScrollEvent(self, event):
        if event.y > 0:
            self.scrollOffset = max(0, self.scrollOffset - 1)
        elif event.y < 0:
            self.scrollOffset += 1

    def run(self):
        self.scrollOffset = 0
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ScreenType.NONE
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)
                elif event.type == pygame.MOUSEWHEEL:
                    self.handleScrollEvent(event)

            self.renderer.clearScreen(palette.BLACK)
            self.drawTitle()
            self.drawEntries()
            self.drawBackButton()
            self.renderer.present()

        self.changeScreen = False
        return self.nextScreen
