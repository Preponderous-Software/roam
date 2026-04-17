from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status
import pygame

# @author Daniel McCoy Stephenson
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

    def switchToWorldScreen(self):
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def switchToStatsScreen(self):
        self.nextScreen = ScreenType.STATS_SCREEN
        self.changeScreen = True

    def switchToInventoryScreen(self):
        self.nextScreen = ScreenType.INVENTORY_SCREEN
        self.changeScreen = True

    def switchToMainMenuScreen(self):
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = True

    def switchToConfigScreen(self):
        self.nextScreen = ScreenType.CONFIG_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        self.nextScreen = ScreenType.NONE
        self.changeScreen = True

    def drawMenuButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 3
        height = y / 10
        # start at top of screen
        xpos = x / 2 - width / 2
        ypos = 0 + height / 2
        margin = 10
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "main menu",
            self.switchToMainMenuScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "stats",
            self.switchToStatsScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "inventory",
            self.switchToInventoryScreen,
        )
        self.drawBackButton()

    def drawBackButton(self):
        # draw in bottom right corner
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
            "back",
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
            self.drawMenuButtons()
            pygame.display.update()

        self.changeScreen = False
        return self.nextScreen
