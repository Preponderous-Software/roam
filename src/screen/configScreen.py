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

    def toggleLimitTps(self):
        self.config.limitTps = not self.config.limitTps
        sleep(0.1)

    def togglePushableStone(self):
        self.config.pushableStone = not self.config.pushableStone
        sleep(0.1)

    def toggleDayNightCycle(self):
        self.config.dayNightCycleEnabled = not self.config.dayNightCycleEnabled
        sleep(0.1)

    def drawTitle(self):
        x, y = self.graphik.getGameDisplay().get_size()
        self.graphik.drawText("Settings", x / 2, 25, 36, (255, 255, 255))

    def drawMenuButtons(self):
        # draw buttons in red or green depending on config option value
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 2
        height = y / 10
        # start below title with enough margin to avoid overlap
        xpos = x / 2 - width / 2
        ypos = 70
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
            "Debug Mode",
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
            "Fullscreen",
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
            "Auto Eat Food",
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
            "Remove Dead Creatures",
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
            "Show Minimap",
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
            "Camera Follow Player",
            self.toggleCameraFollowPlayer,
        )

        ypos = ypos + height + margin
        color = (0, 255, 0) if self.config.limitTps else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "Limit Speed",
            self.toggleLimitTps,
        )

        ypos = ypos + height + margin
        color = (0, 255, 0) if self.config.pushableStone else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "Pushable Stone",
            self.togglePushableStone,
        )

        ypos = ypos + height + margin
        color = (0, 255, 0) if self.config.dayNightCycleEnabled else (255, 0, 0)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            color,
            30,
            "Day/Night Cycle",
            self.toggleDayNightCycle,
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
