import time
from appContainer import component
from config.config import Config
from rendering.renderer import Renderer
from screen.screenType import ScreenType
from screen.screen import Screen
from ui.status import Status
import pygame
from ui import palette


# @author Daniel McCoy Stephenson
@component
class ConfigScreen(Screen):
    def __init__(self, renderer: Renderer, config: Config, status: Status):
        self.renderer = renderer
        self.config = config
        self.status = status
        self.running = True
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = False
        self.scrollOffset = 0
        self._lastToggleAt = 0.0
        self._toggleCooldown = 0.25

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
        now = time.time()
        if now - self._lastToggleAt < self._toggleCooldown:
            return
        self._lastToggleAt = now
        setattr(self.config, attributeName, not getattr(self.config, attributeName))

    def drawTitle(self):
        x, y = self.renderer.getDisplaySize()
        self.renderer.drawText("Settings", x / 2, 25, 36, palette.WHITE)
        self.renderer.drawText(
            "Click a setting to toggle it", x / 2, 50, 14, palette.MEDIUM_GRAY
        )

    def drawMenuButtons(self):
        x, y = self.renderer.getDisplaySize()
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

        visibleRows = max(
            1, int((y - startY - 80) / rowHeight)
        )  # 80px reserved for bottom Back button
        maxOffset = max(0, len(toggleButtons) - visibleRows)
        self.scrollOffset = max(0, min(self.scrollOffset, maxOffset))

        visibleToggles = toggleButtons[
            self.scrollOffset : self.scrollOffset + visibleRows
        ]

        for i, (label, attribute) in enumerate(visibleToggles):
            rowY = startY + i * rowHeight
            isOn = bool(getattr(self.config, attribute))
            color = (0, 255, 0) if isOn else (255, 0, 0)
            stateText = "ON" if isOn else "OFF"
            self.renderer.drawButton(
                xpos,
                rowY,
                width,
                buttonHeight,
                palette.WHITE,
                color,
                20,
                label + ": " + stateText,
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
            self.renderer.drawText(scrollInfo, x / 2, y - 70, 16, palette.MEDIUM_GRAY)

    def drawBottomButtons(self):
        x, y = self.renderer.getDisplaySize()
        buttonWidth = x / 5
        buttonHeight = 35
        bottomY = y - 45  # 45px from the bottom edge, matching ControlsScreen
        self.renderer.drawButton(
            x / 2 - buttonWidth / 2,
            bottomY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
            20,
            "Back",
            self.switchToMainMenuScreen,
        )

    def handleScrollEvent(self, event):
        if event.y > 0:
            self.scrollOffset = max(0, self.scrollOffset - 1)
        elif event.y < 0:
            self.scrollOffset += 1

    def onStart(self):
        self.scrollOffset = 0

    def handleEvent(self, event):
        if event.type == pygame.KEYDOWN:
            self.handleKeyDownEvent(event.key)
        elif event.type == pygame.MOUSEWHEEL:
            self.handleScrollEvent(event)

    def draw(self):
        self.renderer.clearScreen(palette.BLACK)
        self.drawTitle()
        self.drawMenuButtons()
        self.drawBottomButtons()
