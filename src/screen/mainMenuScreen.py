import webbrowser

import pygame
from appContainer import component
from config.config import Config

from rendering.renderer import Renderer
from rendering.inputSource import InputSource
from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode
from screen.screenType import ScreenType
from screen.screen import Screen
from update.updateChecker import UpdateChecker
from ui import palette


# @author Daniel McCoy Stephenson
@component
class MainMenuScreen(Screen):
    def __init__(
        self,
        renderer: Renderer,
        inputSource: InputSource,
        config: Config,
        updateChecker: UpdateChecker,
    ):
        self.renderer = renderer
        self.inputSource = inputSource
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
        x, y = self.renderer.getDisplaySize()
        xpos = x / 2
        ypos = y / 10
        self.renderer.drawText("Roam", xpos, ypos, 64, palette.WHITE)
        ypos = y / 3
        self.renderer.drawText(
            "Explore a procedurally-generated world", xpos, ypos, 24, palette.GRAY
        )

    def drawMenuButtons(self):
        x, y = self.renderer.getDisplaySize()
        width = x / 5
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = y / 2 - height / 2
        margin = 10
        backgroundColor = palette.WHITE
        self.renderer.drawButton(
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
        self.renderer.drawButton(
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
        self.renderer.drawButton(
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
        self.renderer.drawText(
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

        self.renderer.drawText(
            self._cachedVersionLabel,
            self.renderer.getDisplaySize()[0] / 2,
            self.renderer.getDisplaySize()[1] - 10,
            16,
            palette.WHITE,
        )

    def drawUpdateBanner(self):
        if not self.updateChecker.isUpdateAvailable():
            return
        x, y = self.renderer.getDisplaySize()
        self.renderer.drawText(
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
        if key == KeyCode.ESCAPE:
            self.quitApplication()
        elif key in (KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE):
            self.switchToSaveSelectionScreen()
        elif key == KeyCode.U:
            self.openUpdatePage()

    def onStart(self):
        self.updateChecker.checkForUpdatesAsync()

    def handleEvent(self, event):
        if event.type == EventType.KEY_DOWN:
            self.handleKeyDownEvent(event.key)

    def draw(self):
        self.renderer.clearScreen(palette.BLACK)
        self.drawText()
        self.drawMenuButtons()
        self.drawUpdateBanner()
        self.drawVersion()
