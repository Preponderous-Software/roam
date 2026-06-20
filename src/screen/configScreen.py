import time
from appContainer import component
from config.config import Config
from rendering.renderer import Renderer
from rendering.inputSource import InputSource
from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode
from screen.screenType import ScreenType
from screen.screen import Screen
from ui.status import Status
from ui import palette


# @author Daniel McCoy Stephenson
@component
class ConfigScreen(Screen):
    def __init__(
        self,
        renderer: Renderer,
        inputSource: InputSource,
        config: Config,
        status: Status,
    ):
        self.renderer = renderer
        self.inputSource = inputSource
        self.config = config
        self.status = status
        self.running = True
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = False
        self.scrollOffset = 0
        self._lastToggleAt = 0.0
        self._toggleCooldown = 0.25
        self._cursor = 0
        self._toggleButtons = [
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

    def handleKeyDownEvent(self, key):
        n = len(self._toggleButtons)
        if key == KeyCode.ESCAPE:
            self.switchToMainMenuScreen()
        elif key == KeyCode.UP:
            self._cursor = (self._cursor - 1) % n
            self.scrollOffset = min(self.scrollOffset, self._cursor)
        elif key == KeyCode.DOWN:
            self._cursor = (self._cursor + 1) % n
        elif key in (KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE):
            _, attribute = self._toggleButtons[self._cursor]
            self._toggleConfigAttribute(attribute)

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
            "Up/Down: navigate  -  Enter/Space: toggle",
            x / 2, 50, 14, palette.MEDIUM_GRAY
        )

    def drawMenuButtons(self):
        x, y = self.renderer.getDisplaySize()
        width = x / 2
        xpos = x / 2 - width / 2
        rowHeight = 35
        buttonHeight = 28
        startY = 60

        toggleButtons = self._toggleButtons
        visibleRows = max(1, int((y - startY - 80) / rowHeight))
        maxOffset = max(0, len(toggleButtons) - visibleRows)

        # Keep the cursor visible: scroll down if cursor is below the window.
        if self._cursor >= self.scrollOffset + visibleRows:
            self.scrollOffset = self._cursor - visibleRows + 1
        self.scrollOffset = max(0, min(self.scrollOffset, maxOffset))

        visibleToggles = toggleButtons[self.scrollOffset : self.scrollOffset + visibleRows]

        for i, (label, attribute) in enumerate(visibleToggles):
            absIndex = self.scrollOffset + i
            selected = absIndex == self._cursor
            rowY = startY + i * rowHeight
            isOn = bool(getattr(self.config, attribute))
            valueColor = (0, 200, 0) if isOn else (200, 50, 50)
            stateText = "ON" if isOn else "OFF"
            bg = palette.LIGHT_GRAY if selected else palette.WHITE
            displayLabel = ("> " if selected else "  ") + label + ": " + stateText
            self.renderer.drawButton(
                xpos, rowY, width, buttonHeight,
                bg, valueColor, 20,
                displayLabel,
                lambda attr=attribute: self._toggleConfigAttribute(attr),
            )
            if selected:
                self.renderer.drawSelectionHighlight(
                    xpos, rowY, width, buttonHeight, (255, 255, 0)
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
        n = len(self._toggleButtons)
        if event.scrollY > 0:
            self._cursor = max(0, self._cursor - 1)
        elif event.scrollY < 0:
            self._cursor = min(n - 1, self._cursor + 1)

    def onStart(self):
        self.scrollOffset = 0
        self._cursor = 0

    def handleEvent(self, event):
        if event.type == EventType.KEY_DOWN:
            self.handleKeyDownEvent(event.key)
        elif event.type == EventType.MOUSE_WHEEL:
            self.handleScrollEvent(event)

    def draw(self):
        self.renderer.clearScreen(palette.BLACK)
        self.drawTitle()
        self.drawMenuButtons()
        self.drawBottomButtons()
