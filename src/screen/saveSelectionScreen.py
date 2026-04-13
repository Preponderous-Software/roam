import os
import shutil
import datetime
import pygame
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType


# @author Copilot
# @since April 13th, 2026
class SaveSelectionScreen:
    SORT_BY_DATE = "date"
    SORT_BY_NAME = "name"

    def __init__(self, graphik: Graphik, config: Config, initializeWorldScreen):
        self.graphik = graphik
        self.config = config
        self.initializeWorldScreen = initializeWorldScreen
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = False
        self.savesBaseDirectory = "saves"
        self.scrollOffset = 0
        self.sortMode = self.SORT_BY_DATE
        self.cachedSaves = None
        self.confirmingDelete = None
        self.namingNewSave = False
        self.newSaveNameInput = ""

    def refreshSaveCache(self):
        self.cachedSaves = self._scanSaveDirectories()

    def _scanSaveDirectories(self):
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
                    {
                        "name": entry,
                        "path": fullPath,
                        "lastPlayed": lastPlayedDate,
                        "mtime": lastModified,
                    }
                )
        return saves

    def getSaveDirectories(self):
        if self.cachedSaves is None:
            self.refreshSaveCache()
        saves = list(self.cachedSaves)
        if self.sortMode == self.SORT_BY_DATE:
            saves.sort(key=lambda s: s["mtime"], reverse=True)
        else:
            saves.sort(key=lambda s: s["name"].lower())
        return saves

    def selectSave(self, savePath):
        self.config.pathToSaveDirectory = savePath
        pygame.display.set_caption("Roam" + " (" + savePath + ")")
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def startNamingNewSave(self):
        self.namingNewSave = True
        self.newSaveNameInput = ""

    def createNewGameWithName(self, name):
        if not os.path.exists(self.savesBaseDirectory):
            os.makedirs(self.savesBaseDirectory)
        newSavePath = os.path.join(self.savesBaseDirectory, name)
        if os.path.exists(newSavePath):
            return
        os.makedirs(newSavePath)
        self.refreshSaveCache()
        self.selectSave(newSavePath)

    def confirmNewSaveName(self):
        name = self.newSaveNameInput.strip()
        if len(name) == 0:
            name = self._generateSaveName()
        self.namingNewSave = False
        self.newSaveNameInput = ""
        self.createNewGameWithName(name)

    def cancelNamingNewSave(self):
        self.namingNewSave = False
        self.newSaveNameInput = ""

    def _generateSaveName(self):
        if not os.path.exists(self.savesBaseDirectory):
            return "save_1"
        saveNumber = 1
        newSaveName = "save_" + str(saveNumber)
        newSavePath = os.path.join(self.savesBaseDirectory, newSaveName)
        while os.path.exists(newSavePath):
            saveNumber += 1
            newSaveName = "save_" + str(saveNumber)
            newSavePath = os.path.join(self.savesBaseDirectory, newSaveName)
        return newSaveName

    def deleteSave(self, savePath):
        if os.path.isdir(savePath):
            shutil.rmtree(savePath)
        self.confirmingDelete = None
        self.refreshSaveCache()
        saves = self.getSaveDirectories()
        maxOffset = max(0, len(saves) - 1)
        self.scrollOffset = min(self.scrollOffset, maxOffset)

    def toggleSort(self):
        if self.sortMode == self.SORT_BY_DATE:
            self.sortMode = self.SORT_BY_NAME
        else:
            self.sortMode = self.SORT_BY_DATE

    def switchToMainMenuScreen(self):
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = True

    def scrollUp(self):
        self.scrollOffset = max(0, self.scrollOffset - 1)

    def scrollDown(self):
        saves = self.getSaveDirectories()
        maxScrollOffset = max(0, len(saves) - 1)
        self.scrollOffset = min(self.scrollOffset + 1, maxScrollOffset)

    def handleKeyDownEvent(self, key):
        if self.namingNewSave:
            if key == pygame.K_ESCAPE:
                self.cancelNamingNewSave()
            elif key == pygame.K_RETURN:
                self.confirmNewSaveName()
            elif key == pygame.K_BACKSPACE:
                self.newSaveNameInput = self.newSaveNameInput[:-1]
            return
        if key == pygame.K_ESCAPE:
            if self.confirmingDelete is not None:
                self.confirmingDelete = None
            else:
                self.switchToMainMenuScreen()
        elif key == pygame.K_UP:
            self.scrollUp()
        elif key == pygame.K_DOWN:
            self.scrollDown()

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
        saveWidth = x * 0.5
        deleteWidth = x * 0.08
        height = y / 14
        margin = 8
        totalRowWidth = saveWidth + margin + deleteWidth
        xpos = x / 2 - totalRowWidth / 2
        ypos = y / 8
        bottomLimit = y - y / 4
        maxVisible = int((bottomLimit - ypos) / (height + margin))
        visibleSaves = saves[self.scrollOffset : self.scrollOffset + maxVisible]
        interactive = (
            self.confirmingDelete is None and not self.namingNewSave
        )

        for save in visibleSaves:
            label = save["name"] + "  |  " + save["lastPlayed"]
            savePath = save["path"]
            if interactive:
                self.graphik.drawButton(
                    xpos,
                    ypos,
                    saveWidth,
                    height,
                    (255, 255, 255),
                    (0, 0, 0),
                    24,
                    label,
                    lambda p=savePath: self.selectSave(p),
                )
                self.graphik.drawButton(
                    xpos + saveWidth + margin,
                    ypos,
                    deleteWidth,
                    height,
                    (200, 0, 0),
                    (255, 255, 255),
                    20,
                    "X",
                    lambda p=savePath: self._requestDelete(p),
                )
            else:
                self.graphik.drawRectangle(
                    xpos, ypos, saveWidth, height, (180, 180, 180)
                )
                self.graphik.drawText(
                    label,
                    xpos + saveWidth // 2,
                    ypos + height // 2,
                    24,
                    (0, 0, 0),
                )
                self.graphik.drawRectangle(
                    xpos + saveWidth + margin,
                    ypos,
                    deleteWidth,
                    height,
                    (140, 0, 0),
                )
                self.graphik.drawText(
                    "X",
                    xpos + saveWidth + margin + deleteWidth // 2,
                    ypos + height // 2,
                    20,
                    (180, 180, 180),
                )
            ypos += height + margin

    def _requestDelete(self, savePath):
        self.confirmingDelete = savePath

    def drawDeleteConfirmation(self):
        x, y = self.graphik.getGameDisplay().get_size()
        overlayWidth = x * 0.5
        overlayHeight = y * 0.3
        overlayX = x / 2 - overlayWidth / 2
        overlayY = y / 2 - overlayHeight / 2
        self.graphik.drawRectangle(
            overlayX, overlayY, overlayWidth, overlayHeight, (50, 50, 50)
        )
        saveName = os.path.basename(self.confirmingDelete)
        self.graphik.drawText(
            "Delete '" + saveName + "'?",
            x / 2,
            overlayY + overlayHeight * 0.3,
            28,
            (255, 255, 255),
        )
        buttonWidth = overlayWidth * 0.35
        buttonHeight = overlayHeight * 0.25
        buttonMargin = 20
        totalBtnWidth = buttonWidth * 2 + buttonMargin
        btnStartX = x / 2 - totalBtnWidth / 2
        btnY = overlayY + overlayHeight * 0.6
        self.graphik.drawButton(
            btnStartX,
            btnY,
            buttonWidth,
            buttonHeight,
            (200, 0, 0),
            (255, 255, 255),
            24,
            "Delete",
            lambda: self.deleteSave(self.confirmingDelete),
        )
        self.graphik.drawButton(
            btnStartX + buttonWidth + buttonMargin,
            btnY,
            buttonWidth,
            buttonHeight,
            (255, 255, 255),
            (0, 0, 0),
            24,
            "Cancel",
            lambda: setattr(self, "confirmingDelete", None),
        )

    def drawNamingDialog(self):
        x, y = self.graphik.getGameDisplay().get_size()
        overlayWidth = x * 0.5
        overlayHeight = y * 0.35
        overlayX = x / 2 - overlayWidth / 2
        overlayY = y / 2 - overlayHeight / 2
        self.graphik.drawRectangle(
            overlayX, overlayY, overlayWidth, overlayHeight, (50, 50, 50)
        )
        self.graphik.drawText(
            "Enter save name:",
            x / 2,
            overlayY + overlayHeight * 0.2,
            28,
            (255, 255, 255),
        )
        inputWidth = overlayWidth * 0.8
        inputHeight = overlayHeight * 0.18
        inputX = x / 2 - inputWidth / 2
        inputY = overlayY + overlayHeight * 0.38
        self.graphik.drawRectangle(
            inputX, inputY, inputWidth, inputHeight, (255, 255, 255)
        )
        displayText = self.newSaveNameInput + "_"
        self.graphik.drawText(
            displayText,
            x / 2,
            inputY + inputHeight / 2,
            24,
            (0, 0, 0),
        )
        self.graphik.drawText(
            "(Enter to confirm, Escape to cancel)",
            x / 2,
            overlayY + overlayHeight * 0.65,
            18,
            (200, 200, 200),
        )
        buttonWidth = overlayWidth * 0.35
        buttonHeight = overlayHeight * 0.18
        buttonMargin = 20
        totalBtnWidth = buttonWidth * 2 + buttonMargin
        btnStartX = x / 2 - totalBtnWidth / 2
        btnY = overlayY + overlayHeight * 0.78
        self.graphik.drawButton(
            btnStartX,
            btnY,
            buttonWidth,
            buttonHeight,
            (255, 255, 255),
            (0, 0, 0),
            24,
            "Create",
            self.confirmNewSaveName,
        )
        self.graphik.drawButton(
            btnStartX + buttonWidth + buttonMargin,
            btnY,
            buttonWidth,
            buttonHeight,
            (255, 255, 255),
            (0, 0, 0),
            24,
            "Cancel",
            self.cancelNamingNewSave,
        )

    def drawBottomButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        buttonWidth = x / 5
        buttonHeight = y / 10
        margin = 20
        totalWidth = buttonWidth * 3 + margin * 2
        startX = x / 2 - totalWidth / 2
        ypos = y - buttonHeight - y / 12
        interactive = (
            self.confirmingDelete is None and not self.namingNewSave
        )

        if interactive:
            self.graphik.drawButton(
                startX,
                ypos,
                buttonWidth,
                buttonHeight,
                (255, 255, 255),
                (0, 0, 0),
                30,
                "New Game",
                self.startNamingNewSave,
            )

            sortLabel = "Sort: Date" if self.sortMode == self.SORT_BY_DATE else "Sort: Name"
            self.graphik.drawButton(
                startX + buttonWidth + margin,
                ypos,
                buttonWidth,
                buttonHeight,
                (255, 255, 255),
                (0, 0, 0),
                26,
                sortLabel,
                self.toggleSort,
            )

            self.graphik.drawButton(
                startX + (buttonWidth + margin) * 2,
                ypos,
                buttonWidth,
                buttonHeight,
                (255, 255, 255),
                (0, 0, 0),
                30,
                "Back",
                self.switchToMainMenuScreen,
            )
        else:
            sortLabel = "Sort: Date" if self.sortMode == self.SORT_BY_DATE else "Sort: Name"
            for i, label in enumerate(["New Game", sortLabel, "Back"]):
                bx = startX + (buttonWidth + margin) * i
                self.graphik.drawRectangle(
                    bx, ypos, buttonWidth, buttonHeight, (180, 180, 180)
                )
                self.graphik.drawText(
                    label,
                    bx + buttonWidth // 2,
                    ypos + buttonHeight // 2,
                    26 if i == 1 else 30,
                    (80, 80, 80),
                )

    def run(self):
        self.refreshSaveCache()

        # Wait for mouse button release to prevent click pass-through
        # from the previous screen (e.g. the main menu "play" button).
        while pygame.mouse.get_pressed()[0]:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break

            if self.changeScreen:
                break

            pygame.time.wait(10)

        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)
                elif event.type == pygame.MOUSEWHEEL:
                    if event.y > 0:
                        self.scrollUp()
                    elif event.y < 0:
                        self.scrollDown()
                elif event.type == pygame.TEXTINPUT:
                    if self.namingNewSave:
                        for ch in event.text:
                            if ch.isalnum() or ch in "-_ ":
                                self.newSaveNameInput += ch

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawTitle()

            saves = self.getSaveDirectories()
            if len(saves) == 0:
                self.drawNoSavesMessage()
            else:
                self.drawSaveList(saves)

            self.drawBottomButtons()

            if self.confirmingDelete is not None:
                self.drawDeleteConfirmation()
            elif self.namingNewSave:
                self.drawNamingDialog()

            pygame.display.update()

        if self.nextScreen == ScreenType.WORLD_SCREEN:
            self.initializeWorldScreen()

        self.changeScreen = False
        self.scrollOffset = 0
        self.confirmingDelete = None
        self.namingNewSave = False
        self.newSaveNameInput = ""
        return self.nextScreen
