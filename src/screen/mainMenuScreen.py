import webbrowser

import pygame
from appContainer import component
from config.config import Config

from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from update.updateChecker import UpdateChecker
from ui import palette


# @author Daniel McCoy Stephenson
@component
class MainMenuScreen:
    def __init__(self, graphik: Graphik, config: Config, updateChecker: UpdateChecker):
        self.graphik = graphik
        self.config = config
        self.updateChecker = updateChecker
        self.running = True
        self.nextScreen = ScreenType.SAVE_SELECTION_SCREEN
        self.changeScreen = False
        self._cachedVersionLabel = None

    def switchToSaveSelectionScreen(self):
        self.nextScreen = ScreenType.SAVE_SELECTION_SCREEN
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
        self.graphik.drawText("Roam", xpos, ypos, 64, palette.WHITE)
        ypos = y / 3
        self.graphik.drawText(
            "Explore a procedurally-generated world", xpos, ypos, 24, palette.GRAY
        )

    def drawMenuButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 5
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = y / 2 - height / 2
        margin = 10
        backgroundColor = palette.WHITE
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            palette.BLACK,
            30,
            "Play",
            self.switchToSaveSelectionScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            palette.BLACK,
            30,
            "Settings",
            self.switchToConfigScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            palette.BLACK,
            30,
            "Quit",
            self.quitApplication,
        )
        ypos = ypos + height + margin + 6
        self.graphik.drawText(
            "Enter / Space: Play  -  Esc: Quit",
            x / 2,
            ypos,
            16,
            (160, 160, 160),
        )

    def drawVersion(self):
        if self._cachedVersionLabel is None:
            version = self.config.getVersion()
            if not version or version == "unknown":
                return
            self._cachedVersionLabel = "Roam v" + version

        self.graphik.drawText(
            self._cachedVersionLabel,
            self.graphik.getGameDisplay().get_size()[0] / 2,
            self.graphik.getGameDisplay().get_size()[1] - 10,
            16,
            palette.WHITE,
        )

    def drawUpdateBanner(self):
        if not self.updateChecker.isUpdateAvailable():
            return
        x, y = self.graphik.getGameDisplay().get_size()
        self.graphik.drawText(
            "Update available: v"
            + str(self.updateChecker.getLatestVersion())
            + "  -  press U to download",
            x / 2,
            y * 0.42,
            18,
            (255, 220, 120),
        )

    def openUpdatePage(self):
        if not self.updateChecker.isUpdateAvailable():
            return
        webbrowser.open(self.updateChecker.getReleasesUrl())

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
            self.quitApplication()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.switchToSaveSelectionScreen()
        elif key == pygame.K_u:
            self.openUpdatePage()

    def run(self):
        self.updateChecker.checkForUpdatesAsync()
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)

            self.graphik.getGameDisplay().fill(palette.BLACK)
            self.drawText()
            self.drawMenuButtons()
            self.drawUpdateBanner()
            self.drawVersion()
            pygame.display.update()
        self.changeScreen = False
        return self.nextScreen
