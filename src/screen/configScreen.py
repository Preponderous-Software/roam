from time import sleep
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status
import pygame

# @author Daniel McCoy Stephenson
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

    def toggleDebug(self):
        self.config.debug = not self.config.debug
        sleep(0.1)

    def toggleFullscreen(self):
        self.config.fullscreen = not self.config.fullscreen
        sleep(0.1)

    def toggleAutoEatFoodInInventory(self):
        self.config.autoEatFoodInInventory = not self.config.autoEatFoodInInventory
        sleep(0.1)

    def toggleRemoveDeadEntities(self):
        self.config.removeDeadEntities = not self.config.removeDeadEntities
        sleep(0.1)

    def toggleShowMiniMap(self):
        self.config.showMiniMap = not self.config.showMiniMap
        sleep(0.1)

    def toggleCameraFollowPlayer(self):
        self.config.cameraFollowPlayer = not self.config.cameraFollowPlayer
        sleep(0.1)

    def drawMenuButtons(self):
        # draw buttons in red or green depending on config option value
        # config options to include: debug, fullscreen, autoEatInInventory
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 2
        height = y / 10
        # start at top of screen
        xpos = x / 2 - width / 2
        ypos = 0 + height / 2
        margin = 10
        color = (0, 255, 0) if self.config.debug else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "debug",
            self.toggleDebug,
        )
        ypos = ypos + height + margin
        color = (0, 255, 0) if self.config.fullscreen else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "fullscreen",
            self.toggleFullscreen,
        )
        ypos = ypos + height + margin
        color = (0, 255, 0) if self.config.autoEatFoodInInventory else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "auto eat in inventory",
            self.toggleAutoEatFoodInInventory,
        )
        ypos = ypos + height + margin
        color = (0, 255, 0) if self.config.removeDeadEntities else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "remove dead entities",
            self.toggleRemoveDeadEntities,
        )
        ypos = ypos + height + margin
        color = (0, 255, 0) if self.config.showMiniMap else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "show minimap",
            self.toggleShowMiniMap,
        )
        ypos = ypos + height + margin
        color = (0, 255, 0) if self.config.cameraFollowPlayer else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "camera follow player",
            self.toggleCameraFollowPlayer,
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
            self.drawMenuButtons()
            pygame.display.update()

        self.changeScreen = False
        return self.nextScreen
