import os
import shutil
import datetime
import pygame
from config.config import Config
from gameLogging.logger import getLogger
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui import palette

_logger = getLogger(__name__)


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
        self.savesBaseDirectory = Config.getSavesBaseDirectory()
        self.scrollOffset = 0
        self.sortMode = self.SORT_BY_DATE
        self.cachedSaves = None
        self.confirmingDelete = None
        self.namingNewSave = False
        self.newSaveNameInput = ""
        self.newSaveNameError = ""

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
        _logger.info("save selected", savePath=savePath)

    def startNamingNewSave(self):
        self.namingNewSave = True
        self.newSaveNameInput = ""
        self.newSaveNameError = ""

    def _isValidSaveName(self, name):
        if not name or name != name.strip():
            return False
        if os.sep in name or "/" in name or "\\" in name:
            return False
        if ".." in name:
            return False
        if os.path.isabs(name):
            return False
        return True

    def createNewGameWithName(self, name):
        if not self._isValidSaveName(name):
            return
        if not os.path.exists(self.savesBaseDirectory):
            os.makedirs(self.savesBaseDirectory)
        newSavePath = os.path.join(self.savesBaseDirectory, name)
        if os.path.exists(newSavePath):
            return
        os.makedirs(newSavePath)
        self.refreshSaveCache()
        _logger.info("new save created", savePath=newSavePath)
        self.selectSave(newSavePath)

    def confirmNewSaveName(self):
        name = self.newSaveNameInput.strip()
        if len(name) == 0:
            name = self._generateSaveName()
        elif os.path.exists(os.path.join(self.savesBaseDirectory, name)):
            self.newSaveNameError = f'A save named "{name}" already exists.'
            return
        self.namingNewSave = False
        self.newSaveNameInput = ""
        self.newSaveNameError = ""
        self.createNewGameWithName(name)

    def cancelNamingNewSave(self):
        self.namingNewSave = False
        self.newSaveNameInput = ""
        self.newSaveNameError = ""

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
        resolvedPath = os.path.realpath(savePath)
        resolvedBase = os.path.realpath(self.savesBaseDirectory)
        if not resolvedPath.startswith(resolvedBase + os.sep):
            self.confirmingDelete = None
            return
        if os.path.isdir(savePath):
            shutil.rmtree(savePath)
            _logger.info("save deleted", savePath=savePath)
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
                self.newSaveNameError = ""
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
        self.graphik.drawText("Select Save", xpos, ypos, 48, palette.WHITE)

    def drawNoSavesMessage(self):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = x / 2
        ypos = y / 3
        self.graphik.drawText("No save files found.", xpos, ypos, 28, palette.WHITE)
        ypos += 40
        self.graphik.drawText(
            'Click "New Game" to start playing!',
            xpos,
            ypos,
            24,
            palette.GRAY,
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
        interactive = self.confirmingDelete is None and not self.namingNewSave

        if len(saves) > maxVisible:
            shownEnd = min(self.scrollOffset + maxVisible, len(saves))
            scrollInfo = (
                f"{self.scrollOffset + 1}-{shownEnd} of {len(saves)}"
                "  -  scroll or arrow keys"
            )
            self.graphik.drawText(scrollInfo, x / 2, ypos - 18, 14, palette.MEDIUM_GRAY)

        for save in visibleSaves:
            label = save["name"] + "  |  " + save["lastPlayed"]
            savePath = save["path"]
            if interactive:
                self.graphik.drawButton(
                    xpos,
                    ypos,
                    saveWidth,
                    height,
                    palette.WHITE,
                    palette.BLACK,
                    24,
                    label,
                    lambda p=savePath: self.selectSave(p),
                )
                self.graphik.drawButton(
                    xpos + saveWidth + margin,
                    ypos,
                    deleteWidth,
                    height,
                    palette.RED,
                    palette.WHITE,
                    20,
                    "X",
                    lambda p=savePath: self._requestDelete(p),
                )
            else:
                self.graphik.drawRectangle(
                    xpos, ypos, saveWidth, height, palette.MEDIUM_GRAY
                )
                self.graphik.drawText(
                    label,
                    xpos + saveWidth // 2,
                    ypos + height // 2,
                    24,
                    palette.BLACK,
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
                    palette.MEDIUM_GRAY,
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
            overlayX, overlayY, overlayWidth, overlayHeight, palette.CHARCOAL
        )
        saveName = os.path.basename(self.confirmingDelete)
        self.graphik.drawText(
            "Delete '" + saveName + "'?",
            x / 2,
            overlayY + overlayHeight * 0.25,
            28,
            palette.WHITE,
        )
        self.graphik.drawText(
            "This cannot be undone.",
            x / 2,
            overlayY + overlayHeight * 0.42,
            18,
            (255, 140, 140),
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
            palette.RED,
            palette.WHITE,
            24,
            "Delete",
            lambda: self.deleteSave(self.confirmingDelete),
        )
        self.graphik.drawButton(
            btnStartX + buttonWidth + buttonMargin,
            btnY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
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
            overlayX, overlayY, overlayWidth, overlayHeight, palette.CHARCOAL
        )
        self.graphik.drawText(
            "Enter save name:",
            x / 2,
            overlayY + overlayHeight * 0.2,
            28,
            palette.WHITE,
        )
        inputWidth = overlayWidth * 0.8
        inputHeight = overlayHeight * 0.18
        inputX = x / 2 - inputWidth / 2
        inputY = overlayY + overlayHeight * 0.38
        self.graphik.drawRectangle(
            inputX, inputY, inputWidth, inputHeight, palette.WHITE
        )
        displayText = self.newSaveNameInput + "_"
        self.graphik.drawText(
            displayText,
            x / 2,
            inputY + inputHeight / 2,
            24,
            palette.BLACK,
        )
        if self.newSaveNameError:
            self.graphik.drawText(
                self.newSaveNameError,
                x / 2,
                overlayY + overlayHeight * 0.60,
                18,
                (255, 120, 120),
            )
        self.graphik.drawText(
            "(Enter to confirm, Escape to cancel)",
            x / 2,
            overlayY + overlayHeight * 0.68,
            16,
            palette.MEDIUM_GRAY,
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
            palette.WHITE,
            palette.BLACK,
            24,
            "Create",
            self.confirmNewSaveName,
        )
        self.graphik.drawButton(
            btnStartX + buttonWidth + buttonMargin,
            btnY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
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
        interactive = self.confirmingDelete is None and not self.namingNewSave

        if interactive:
            self.graphik.drawButton(
                startX,
                ypos,
                buttonWidth,
                buttonHeight,
                palette.WHITE,
                palette.BLACK,
                30,
                "New Game",
                self.startNamingNewSave,
            )

            sortLabel = (
                "Sorted: Date" if self.sortMode == self.SORT_BY_DATE else "Sorted: Name"
            )
            self.graphik.drawButton(
                startX + buttonWidth + margin,
                ypos,
                buttonWidth,
                buttonHeight,
                palette.WHITE,
                palette.BLACK,
                26,
                sortLabel,
                self.toggleSort,
            )

            self.graphik.drawButton(
                startX + (buttonWidth + margin) * 2,
                ypos,
                buttonWidth,
                buttonHeight,
                palette.WHITE,
                palette.BLACK,
                30,
                "Back",
                self.switchToMainMenuScreen,
            )
        else:
            sortLabel = (
                "Sorted: Date" if self.sortMode == self.SORT_BY_DATE else "Sorted: Name"
            )
            for i, label in enumerate(["New Game", sortLabel, "Back"]):
                bx = startX + (buttonWidth + margin) * i
                self.graphik.drawRectangle(
                    bx, ypos, buttonWidth, buttonHeight, palette.MEDIUM_GRAY
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
                                self.newSaveNameError = ""

            self.graphik.getGameDisplay().fill(palette.BLACK)
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
