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
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = 70
        margin = 10

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

        for label, attribute in toggleButtons:
            color = (0, 255, 0) if getattr(self.config, attribute) else (255, 0, 0)
            self.graphik.drawButton(
                xpos,
                ypos,
                width,
                height,
                (255, 255, 255),
                color,
                30,
                label,
                lambda attr=attribute: self._toggleConfigAttribute(attr),
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
            self.switchToMainMenuScreen,
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
