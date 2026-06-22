from appContainer import component
from codex.codex import (
    Codex,
    ALL_ENTITY_TYPES,
    ALL_LIVING_ENTITY_TYPES,
    ENTITY_DISPLAY_NAMES,
    ENTITY_IMAGE_PATHS,
)
from config.config import Config
from config.keyBindings import KeyBindings
from rendering.renderer import Renderer
from rendering.inputSource import InputSource
from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode
from screen.screenType import ScreenType
from screen.screen import Screen
from ui import palette


# @author Copilot
# @since April 20th, 2026
@component
class CodexScreen(Screen):
    def __init__(
        self,
        renderer: Renderer,
        inputSource: InputSource,
        config: Config,
        codex: Codex,
        keyBindings: KeyBindings,
    ):
        self.renderer = renderer
        self.inputSource = inputSource
        self.config = config
        self.codex = codex
        self.keyBindings = keyBindings
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.returnScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.scrollOffset = 0
        self._imageCache = {}

    def setReturnScreen(self, screenType):
        self.returnScreen = screenType

    def switchToReturnScreen(self):
        self.nextScreen = self.returnScreen
        self.changeScreen = True

    def drawTitle(self):
        x, y = self.renderer.getDisplaySize()
        self.renderer.drawText("Codex", x / 2, 25, 36, palette.WHITE)
        discoveredCount = len(self.codex.getDiscoveredEntities())
        totalCount = len(ALL_ENTITY_TYPES)
        self.renderer.drawText(
            f"{discoveredCount} of {totalCount} discovered",
            x / 2,
            50,
            16,
            palette.MEDIUM_GRAY,
        )

    def _getEntityImage(self, entityName):
        # Load + scale through the Renderer (cached per entity). A missing path
        # yields None (the entry is drawn without an icon); a load failure is
        # handled by the Renderer, which returns its visible placeholder.
        if entityName not in self._imageCache:
            imagePath = ENTITY_IMAGE_PATHS.get(entityName)
            if imagePath is None:
                self._imageCache[entityName] = None
            else:
                image = self.renderer.loadImage(imagePath)
                self._imageCache[entityName] = self.renderer.scaleImage(image, (32, 32))
        return self._imageCache[entityName]

    def drawEntries(self):
        x, y = self.renderer.getDisplaySize()
        entries = ALL_ENTITY_TYPES

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

            displayName = ENTITY_DISPLAY_NAMES.get(entityName, entityName)
            if discovered:
                # Draw entity image
                img = self._getEntityImage(entityName)
                if img is not None:
                    self.renderer.drawImage(img, (int(imageX), int(rowY + 2)))
                # Draw entity name left-aligned after the image
                self.renderer.drawTextLeftAligned(
                    displayName,
                    nameX,
                    rowY + rowHeight / 2,
                    22,
                    palette.WHITE,
                )
            else:
                # Undiscovered entry
                self.renderer.drawTextLeftAligned(
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
                "Up/Down to see more", x / 2, y - 92, 14, palette.DIM_GRAY
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
        if key == KeyCode.ESCAPE or key == self.keyBindings.getKey("codex"):
            self.switchToReturnScreen()
        elif key in (KeyCode.UP, KeyCode.W):
            self.scrollOffset = max(0, self.scrollOffset - 1)
        elif key in (KeyCode.DOWN, KeyCode.S):
            self.scrollOffset += 1

    def handleScrollEvent(self, event):
        if event.scrollY > 0:
            self.scrollOffset = max(0, self.scrollOffset - 1)
        elif event.scrollY < 0:
            self.scrollOffset += 1

    def onStart(self):
        self.scrollOffset = 0

    def handleEvent(self, event):
        if event.type == EventType.KEY_DOWN:
            self.handleKeyDownEvent(event.key)
        elif event.type == EventType.MOUSE_WHEEL:
            self.handleScrollEvent(event)

    def draw(self):
        self.renderer.clearScreen(palette.BLACK)
        self.drawTitle()
        self.drawEntries()
        self.drawBackButton()
