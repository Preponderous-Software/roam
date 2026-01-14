import os
import pygame
from config.config import Config

from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType

# @author Daniel McCoy Stephenson
class MainMenuScreen:
    def __init__(self, graphik: Graphik, config: Config, initializeWorldScreen):
        self.graphik = graphik
        self.config = config
        self.running = True
        self.initializeWorldScreen = initializeWorldScreen
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False

    def switchToWorldScreen(self):
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def switchToJoinSessionScreen(self):
        self.nextScreen = ScreenType.JOIN_SESSION_SCREEN
        self.changeScreen = True

    def switchToConfigScreen(self):
        self.nextScreen = ScreenType.CONFIG_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawText(self):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = x / 2
        ypos = y / 10
        self.graphik.drawText("Roam", xpos, ypos, 64, (255, 255, 255))
        ypos = y / 3
        self.graphik.drawText(
            "press any key to start!", xpos, ypos, 32, (255, 255, 255)
        )

    def drawMenuButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 5
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = y / 2 - height / 2
        margin = 10
        backgroundColor = (255, 255, 255)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "play",
            self.switchToWorldScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "join session",
            self.switchToJoinSessionScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "config",
            self.switchToConfigScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "quit",
            self.quitApplication,
        )

    def drawVersion(self):
        if os.path.isfile("version.txt"):
            with open("version.txt", "r") as file:
                version = file.read()

                # display centered at bottom of screen
                self.graphik.drawText(
                    version,
                    self.graphik.getGameDisplay().get_size()[0] / 2,
                    self.graphik.getGameDisplay().get_size()[1] - 10,
                    16,
                    (255, 255, 255),
                )

    def handleKeyDownEvent(self, key):
        self.switchToWorldScreen()

    def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawText()
            self.drawMenuButtons()
            self.drawVersion()
            pygame.display.update()
        self.initializeWorldScreen()
        self.changeScreen = False
        return self.nextScreen
