from appContainer import component
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status
import pygame


# @author Daniel McCoy Stephenson
@component
class OptionsScreen:
    def __init__(self, graphik: Graphik, config: Config, status: Status):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.running = True
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
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

    def switchToConfigScreen(self):
        self._switchToScreen(ScreenType.CONFIG_SCREEN)

    def switchToControlsScreen(self):
        self._switchToScreen(ScreenType.CONTROLS_SCREEN)

    def switchToCodexScreen(self):
        self._switchToScreen(ScreenType.CODEX_SCREEN)

    def quitApplication(self):
        self._switchToScreen(ScreenType.NONE)

    def drawTitle(self):
        x, y = self.graphik.getGameDisplay().get_size()
        self.graphik.drawText("Menu", x / 2, 25, 36, (255, 255, 255))

    def drawMenuButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 3
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = 70
        margin = 10

        menuItems = [
            ("Main Menu", self.switchToMainMenuScreen),
            ("Stats", self.switchToStatsScreen),
            ("Inventory", self.switchToInventoryScreen),
            ("Controls", self.switchToControlsScreen),
            ("Codex", self.switchToCodexScreen),
        ]

        for label, callback in menuItems:
            self.graphik.drawButton(
                xpos,
                ypos,
                width,
                height,
                (255, 255, 255),
                (0, 0, 0),
                30,
                label,
                callback,
            )
            ypos = ypos + height + margin

        self.drawBackButton()

    def drawBackButton(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 3
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = y / 2 - height / 2 + width
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "Back",
            self.switchToWorldScreen,
        )

    def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ScreenType.NONE
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawTitle()
            self.drawMenuButtons()
            pygame.display.update()

        self.changeScreen = False
        return self.nextScreen
