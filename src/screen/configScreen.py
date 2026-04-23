from time import sleep
from appContainer import component
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status
import pygame


# @author Daniel McCoy Stephenson
@component
class ConfigScreen:
    def __init__(self, graphik: Graphik, config: Config, status: Status):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.running = True
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = False
        self.scrollOffset = 0

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
            self.switchToMainMenuScreen()

    def switchToMainMenuScreen(self):
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        self.nextScreen = ScreenType.NONE
        self.changeScreen = True

    def _toggleConfigAttribute(self, attributeName):
        setattr(self.config, attributeName, not getattr(self.config, attributeName))
        sleep(0.1)

    def drawTitle(self):
        x, y = self.graphik.getGameDisplay().get_size()
        self.graphik.drawText("Settings", x / 2, 25, 36, (255, 255, 255))

    def drawMenuButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 2
        xpos = x / 2 - width / 2
        rowHeight = 35
        buttonHeight = 28
        startY = 60

        toggleButtons = [
            ("Debug Mode", "debug"),
            ("Fullscreen", "fullscreen"),
            ("Auto Eat Food", "autoEatFoodInInventory"),
            ("Remove Dead Creatures", "removeDeadEntities"),
            ("Show Minimap", "showMiniMap"),
            ("Camera Follow Player", "cameraFollowPlayer"),
            ("Limit Speed", "limitTps"),
            ("Pushable Stone", "pushableStone"),
            ("Day/Night Cycle", "dayNightCycleEnabled"),
        ]

        visibleRows = int((y - startY - 80) / rowHeight)  # 80px reserved for bottom Back button
        maxOffset = max(0, len(toggleButtons) - visibleRows)
        self.scrollOffset = max(0, min(self.scrollOffset, maxOffset))

        visibleToggles = toggleButtons[self.scrollOffset : self.scrollOffset + visibleRows]

        for i, (label, attribute) in enumerate(visibleToggles):
            rowY = startY + i * rowHeight
            color = (0, 255, 0) if getattr(self.config, attribute) else (255, 0, 0)
            self.graphik.drawButton(
                xpos,
                rowY,
                width,
                buttonHeight,
                (255, 255, 255),
                color,
                20,
                label,
                lambda attr=attribute: self._toggleConfigAttribute(attr),
            )

        if maxOffset > 0:
            scrollInfo = (
                str(self.scrollOffset + 1)
                + "-"
                + str(min(self.scrollOffset + visibleRows, len(toggleButtons)))
                + " of "
                + str(len(toggleButtons))
            )
            self.graphik.drawText(scrollInfo, x / 2, y - 70, 16, (180, 180, 180))

    def drawBottomButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        buttonWidth = x / 5
        buttonHeight = 35
        bottomY = y - 45  # 45px from the bottom edge, matching ControlsScreen
        self.graphik.drawButton(
            x / 2 - buttonWidth / 2,
            bottomY,
            buttonWidth,
            buttonHeight,
            (255, 255, 255),
            (0, 0, 0),
            20,
            "Back",
            self.switchToMainMenuScreen,
        )

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
            self.drawMenuButtons()
            self.drawBottomButtons()
            pygame.display.update()

        self.changeScreen = False
        return self.nextScreen
