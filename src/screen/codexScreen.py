import pygame
from appContainer import component
from codex.codex import Codex
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType


# All known living entity types for the codex display.
ALL_LIVING_ENTITY_TYPES = ["Bear", "Chicken"]

# Maps entity class names to their asset image paths.
ENTITY_IMAGE_PATHS = {
    "Bear": "assets/images/bear.png",
    "Chicken": "assets/images/chicken.png",
}


# @author Copilot
# @since April 20th, 2026
@component
class CodexScreen:
    def __init__(self, graphik: Graphik, config: Config, codex: Codex):
        self.graphik = graphik
        self.config = config
        self.codex = codex
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.scrollOffset = 0
        self._imageCache = {}

    def switchToWorldScreen(self):
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def drawTitle(self):
        x, y = self.graphik.getGameDisplay().get_size()
        self.graphik.drawText("Codex", x / 2, 25, 36, (255, 255, 255))

    def _getEntityImage(self, entityName):
        if entityName not in self._imageCache:
            imagePath = ENTITY_IMAGE_PATHS.get(entityName)
            if imagePath is not None:
                try:
                    img = pygame.image.load(imagePath)
                    self._imageCache[entityName] = pygame.transform.scale(img, (32, 32))
                except Exception:
                    self._imageCache[entityName] = None
            else:
                self._imageCache[entityName] = None
        return self._imageCache[entityName]

    def drawEntries(self):
        x, y = self.graphik.getGameDisplay().get_size()
        entries = ALL_LIVING_ENTITY_TYPES

        rowHeight = 45
        startY = 60
        imageX = x * 0.25
        nameX = x * 0.25 + 45

        visibleRows = int((y - startY - 80) / rowHeight)
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
                    self.graphik.getGameDisplay().blit(
                        img, (int(imageX), int(rowY + 2))
                    )
                # Draw entity name
                self.graphik.drawText(
                    entityName,
                    nameX,
                    rowY + rowHeight / 2,
                    22,
                    (255, 255, 255),
                )
            else:
                # Undiscovered entry
                self.graphik.drawText(
                    "???",
                    nameX,
                    rowY + rowHeight / 2,
                    22,
                    (100, 100, 100),
                )

        if maxOffset > 0:
            scrollInfo = (
                str(self.scrollOffset + 1)
                + "-"
                + str(min(self.scrollOffset + visibleRows, len(entries)))
                + " of "
                + str(len(entries))
            )
            self.graphik.drawText(scrollInfo, x / 2, y - 70, 16, (180, 180, 180))

    def drawBackButton(self):
        x, y = self.graphik.getGameDisplay().get_size()
        buttonWidth = x / 5
        buttonHeight = 35
        bottomY = y - 45
        startX = (x - buttonWidth) / 2
        self.graphik.drawButton(
            startX,
            bottomY,
            buttonWidth,
            buttonHeight,
            (255, 255, 255),
            (0, 0, 0),
            20,
            "Back",
            self.switchToWorldScreen,
        )

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
            self.switchToWorldScreen()

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

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawTitle()
            self.drawEntries()
            self.drawBackButton()
            pygame.display.update()

        self.changeScreen = False
        return self.nextScreen
