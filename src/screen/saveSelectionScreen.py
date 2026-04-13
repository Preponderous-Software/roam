import os
import datetime
import pygame
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType


# @author Copilot
# @since April 13th, 2026
class SaveSelectionScreen:
    def __init__(self, graphik: Graphik, config: Config, initializeWorldScreen):
        self.graphik = graphik
        self.config = config
        self.initializeWorldScreen = initializeWorldScreen
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = False
        self.savesBaseDirectory = "saves"
        self.scrollOffset = 0

    def getSaveDirectories(self):
        if not os.path.exists(self.savesBaseDirectory):
            return []
        saves = []
        for entry in os.listdir(self.savesBaseDirectory):
            fullPath = os.path.join(self.savesBaseDirectory, entry)
            if os.path.isdir(fullPath):
                lastModified = os.path.getmtime(fullPath)
                lastPlayedDate = datetime.datetime.fromtimestamp(lastModified).strftime(
                    "%Y-%m-%d %H:%M"
                )
                saves.append(
                    {"name": entry, "path": fullPath, "lastPlayed": lastPlayedDate}
                )
        saves.sort(key=lambda s: os.path.getmtime(s["path"]), reverse=True)
        return saves

    def selectSave(self, savePath):
        self.config.pathToSaveDirectory = savePath
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def createNewGame(self):
        if not os.path.exists(self.savesBaseDirectory):
            os.makedirs(self.savesBaseDirectory)
        existingSaves = self.getSaveDirectories()
        existingNames = [s["name"] for s in existingSaves]
        saveNumber = 1
        while "save_" + str(saveNumber) in existingNames:
            saveNumber += 1
        newSaveName = "save_" + str(saveNumber)
        newSavePath = os.path.join(self.savesBaseDirectory, newSaveName)
        os.makedirs(newSavePath)
        self.selectSave(newSavePath)

    def switchToMainMenuScreen(self):
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = True

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
            self.switchToMainMenuScreen()
        elif key == pygame.K_UP:
            self.scrollOffset = max(0, self.scrollOffset - 1)
        elif key == pygame.K_DOWN:
            self.scrollOffset += 1

    def drawTitle(self):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = x / 2
        ypos = y / 12
        self.graphik.drawText("Select Save", xpos, ypos, 48, (255, 255, 255))

    def drawNoSavesMessage(self):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = x / 2
        ypos = y / 3
        self.graphik.drawText(
            "No save files found.", xpos, ypos, 28, (255, 255, 255)
        )
        ypos += 40
        self.graphik.drawText(
            'Click "New Game" to start playing!',
            xpos,
            ypos,
            24,
            (200, 200, 200),
        )

    def drawSaveList(self, saves):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x * 0.6
        height = y / 12
        xpos = x / 2 - width / 2
        ypos = y / 6
        margin = 8

        maxVisible = int((y * 0.6) / (height + margin))
        visibleSaves = saves[self.scrollOffset : self.scrollOffset + maxVisible]

        for save in visibleSaves:
            label = save["name"] + "  |  " + save["lastPlayed"]
            savePath = save["path"]
            self.graphik.drawButton(
                xpos,
                ypos,
                width,
                height,
                (255, 255, 255),
                (0, 0, 0),
                24,
                label,
                lambda p=savePath: self.selectSave(p),
            )
            ypos += height + margin

    def drawBottomButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        buttonWidth = x / 4
        buttonHeight = y / 10
        margin = 20
        totalWidth = buttonWidth * 2 + margin
        startX = x / 2 - totalWidth / 2
        ypos = y - buttonHeight - y / 12

        self.graphik.drawButton(
            startX,
            ypos,
            buttonWidth,
            buttonHeight,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "New Game",
            self.createNewGame,
        )
        self.graphik.drawButton(
            startX + buttonWidth + margin,
            ypos,
            buttonWidth,
            buttonHeight,
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
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawTitle()

            saves = self.getSaveDirectories()
            if len(saves) == 0:
                self.drawNoSavesMessage()
            else:
                self.drawSaveList(saves)

            self.drawBottomButtons()
            pygame.display.update()

        if self.nextScreen == ScreenType.WORLD_SCREEN:
            self.initializeWorldScreen()

        self.changeScreen = False
        self.scrollOffset = 0
        return self.nextScreen
