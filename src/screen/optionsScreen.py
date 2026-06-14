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
class OptionsScreen(Screen):
    def __init__(
        self, renderer: Renderer, inputSource: InputSource, config: Config, status: Status
    ):
        self.renderer = renderer
        self.inputSource = inputSource
        self.config = config
        self.status = status
        self.running = True
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.confirmingMainMenu = False

    def handleKeyDownEvent(self, key):
        if key == KeyCode.ESCAPE:
            if self.confirmingMainMenu:
                self.confirmingMainMenu = False
            else:
                self.switchToWorldScreen()

    def _switchToScreen(self, screenType):
        self.nextScreen = screenType
        self.changeScreen = True

    def switchToWorldScreen(self):
        self._switchToScreen(ScreenType.WORLD_SCREEN)

    def switchToStatsScreen(self):
        self._switchToScreen(ScreenType.STATS_SCREEN)

    def switchToInventoryScreen(self):
        self._switchToScreen(ScreenType.INVENTORY_SCREEN)

    def switchToMainMenuScreen(self):
        self._switchToScreen(ScreenType.MAIN_MENU_SCREEN)

    def requestMainMenuConfirmation(self):
        self.confirmingMainMenu = True

    def cancelMainMenuConfirmation(self):
        self.confirmingMainMenu = False

    def switchToConfigScreen(self):
        self._switchToScreen(ScreenType.CONFIG_SCREEN)

    def switchToControlsScreen(self):
        self._switchToScreen(ScreenType.CONTROLS_SCREEN)

    def switchToCodexScreen(self):
        self._switchToScreen(ScreenType.CODEX_SCREEN)

    def quitApplication(self):
        self._switchToScreen(ScreenType.NONE)

    def drawTitle(self):
        x, y = self.renderer.getDisplaySize()
        self.renderer.drawText("Menu", x / 2, 25, 36, palette.WHITE)

    def drawMenuButtons(self):
        x, y = self.renderer.getDisplaySize()
        width = x / 3
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = 70
        margin = 10

        menuItems = [
            ("Quit to Main Menu", self.requestMainMenuConfirmation),
            ("Stats", self.switchToStatsScreen),
            ("Inventory", self.switchToInventoryScreen),
            ("Controls", self.switchToControlsScreen),
            ("Codex", self.switchToCodexScreen),
        ]

        for label, callback in menuItems:
            self.renderer.drawButton(
                xpos,
                ypos,
                width,
                height,
                palette.WHITE,
                palette.BLACK,
                30,
                label,
                callback,
            )
            ypos = ypos + height + margin

        self.drawBackButton()

    def drawBackButton(self):
        x, y = self.renderer.getDisplaySize()
        width = x / 3
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = y / 2 - height / 2 + width
        self.renderer.drawButton(
            xpos,
            ypos,
            width,
            height,
            palette.WHITE,
            palette.BLACK,
            30,
            "Back",
            self.switchToWorldScreen,
        )

    def drawMainMenuConfirmation(self):
        x, y = self.renderer.getDisplaySize()
        overlayWidth = x * 0.6
        overlayHeight = y * 0.35
        overlayX = x / 2 - overlayWidth / 2
        overlayY = y / 2 - overlayHeight / 2
        self.renderer.drawRectangle(
            overlayX, overlayY, overlayWidth, overlayHeight, palette.CHARCOAL
        )
        self.renderer.drawText(
            "Return to main menu?",
            x / 2,
            overlayY + overlayHeight * 0.22,
            28,
            palette.WHITE,
        )
        self.renderer.drawText(
            "Your current session will end.",
            x / 2,
            overlayY + overlayHeight * 0.42,
            18,
            palette.GRAY,
        )
        self.renderer.drawText(
            "Your progress will be saved automatically.",
            x / 2,
            overlayY + overlayHeight * 0.55,
            18,
            (160, 200, 160),
        )
        buttonWidth = overlayWidth * 0.35
        buttonHeight = overlayHeight * 0.22
        buttonMargin = 20
        totalBtnWidth = buttonWidth * 2 + buttonMargin
        btnStartX = x / 2 - totalBtnWidth / 2
        btnY = overlayY + overlayHeight * 0.68
        self.renderer.drawButton(
            btnStartX,
            btnY,
            buttonWidth,
            buttonHeight,
            palette.RED,
            palette.WHITE,
            22,
            "Quit to Menu",
            self.switchToMainMenuScreen,
        )
        self.renderer.drawButton(
            btnStartX + buttonWidth + buttonMargin,
            btnY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
            22,
            "Cancel",
            self.cancelMainMenuConfirmation,
        )

    def handleEvent(self, event):
        if event.type == EventType.KEY_DOWN:
            self.handleKeyDownEvent(event.key)

    def draw(self):
        self.renderer.clearScreen(palette.BLACK)
        self.drawTitle()
        if self.confirmingMainMenu:
            # Skip the menu buttons while confirming so their click
            # rects don't fire through the overlay.
            self.drawMainMenuConfirmation()
        else:
            self.drawMenuButtons()

    def onExit(self):
        self.confirmingMainMenu = False
