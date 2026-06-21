import os
import shutil
import datetime
import time
from config.config import Config
from gameLogging.logger import getLogger
from rendering.renderer import Renderer
from rendering.inputSource import InputSource
from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode
from screen.screenType import ScreenType
from screen.screen import Screen
from ui import palette

_logger = getLogger(__name__)


# @author Copilot
# @since April 13th, 2026
class SaveSelectionScreen(Screen):
    SORT_BY_DATE = "date"
    SORT_BY_NAME = "name"

    def __init__(
        self,
        renderer: Renderer,
        inputSource: InputSource,
        config: Config,
        initializeWorldScreen,
    ):
        self.renderer = renderer
        self.inputSource = inputSource
        self.config = config
        self.initializeWorldScreen = initializeWorldScreen
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = False
        self.savesBaseDirectory = Config.getSavesBaseDirectory()
        self.scrollOffset = 0
        self._selectedIndex = 0
        self.sortMode = self.SORT_BY_DATE
        self.cachedSaves = None
        self.confirmingDelete = None
        self.namingNewSave = False
        self.newSaveNameInput = ""
        self.newSaveNameError = ""
        # When naming opens via the 'C' key, that keypress also arrives as a
        # text-input event in the same batch; suppress text input for the frame
        # it opens so 'c' isn't typed into the new name. Cleared each draw().
        self._suppressTextInput = False

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
        self.renderer.setCaption("Roam" + " (" + savePath + ")")
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True
        _logger.info("save selected", savePath=savePath)

    def startNamingNewSave(self):
        self.namingNewSave = True
        self._suppressTextInput = True
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
        self._selectedIndex = min(self._selectedIndex, maxOffset)

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

    def _moveCursorUp(self, saves, maxVisible):
        if self._selectedIndex > 0:
            self._selectedIndex -= 1
            if self._selectedIndex < self.scrollOffset:
                self.scrollOffset = self._selectedIndex

    def _moveCursorDown(self, saves, maxVisible):
        if self._selectedIndex < len(saves) - 1:
            self._selectedIndex += 1
            if self._selectedIndex >= self.scrollOffset + maxVisible:
                self.scrollOffset = self._selectedIndex - maxVisible + 1

    def handleKeyDownEvent(self, key):
        if self.namingNewSave:
            if key == KeyCode.ESCAPE:
                self.cancelNamingNewSave()
            elif key == KeyCode.RETURN:
                self.confirmNewSaveName()
            elif key == KeyCode.BACKSPACE:
                self.newSaveNameInput = self.newSaveNameInput[:-1]
                self.newSaveNameError = ""
            return
        if self.confirmingDelete is not None:
            if key == KeyCode.ESCAPE:
                self.confirmingDelete = None
            elif key in (KeyCode.RETURN, KeyCode.KP_ENTER):
                self.deleteSave(self.confirmingDelete)
            return
        if key == KeyCode.ESCAPE:
            self.switchToMainMenuScreen()
        elif key == KeyCode.UP:
            saves = self.getSaveDirectories()
            maxVisible = self._maxVisible()
            self._moveCursorUp(saves, maxVisible)
        elif key == KeyCode.DOWN:
            saves = self.getSaveDirectories()
            maxVisible = self._maxVisible()
            self._moveCursorDown(saves, maxVisible)
        elif key == KeyCode.RETURN:
            self.selectHighlightedSave()
        elif key == KeyCode.C:
            self.startNamingNewSave()
        elif key == KeyCode.T:
            self.toggleSort()

    def _maxVisible(self):
        """Number of save rows that fit on screen (approximated from display height)."""
        _, y = self.renderer.getDisplaySize()
        height = y / 14
        margin = 8
        ypos = y / 8
        bottomLimit = y - y / 4
        return max(1, int((bottomLimit - ypos) / (height + margin)))

    def getHighlightedSaveIndex(self):
        return self._selectedIndex

    def selectHighlightedSave(self):
        """Enter the world with the keyboard-highlighted save, or start naming a
        new one if there are no saves yet (so Enter always does something)."""
        saves = self.getSaveDirectories()
        if saves:
            index = min(self.getHighlightedSaveIndex(), len(saves) - 1)
            self.selectSave(saves[index]["path"])
        else:
            self.startNamingNewSave()

    def drawTitle(self):
        x, y = self.renderer.getDisplaySize()
        xpos = x / 2
        ypos = y / 12
        self.renderer.drawText("Select Save", xpos, ypos, 48, palette.WHITE)

    def drawNoSavesMessage(self):
        x, y = self.renderer.getDisplaySize()
        xpos = x / 2
        ypos = y / 3
        self.renderer.drawText("No save files found.", xpos, ypos, 28, palette.WHITE)
        ypos += 40
        self.renderer.drawText(
            "Press C to create a new save.",
            xpos,
            ypos,
            24,
            palette.GRAY,
        )

    def drawSaveList(self, saves):
        x, y = self.renderer.getDisplaySize()
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
            self.renderer.drawText(
                scrollInfo, x / 2, ypos - 18, 14, palette.MEDIUM_GRAY
            )

        for rowIndex, save in enumerate(visibleSaves):
            absoluteIndex = self.scrollOffset + rowIndex
            isSelected = interactive and absoluteIndex == self._selectedIndex
            marker = "> " if isSelected else ""
            label = marker + save["name"] + "  |  " + save["lastPlayed"]
            savePath = save["path"]
            if interactive:
                self.renderer.drawButton(
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
                if isSelected:
                    self.renderer.drawSelectionHighlight(
                        xpos, ypos, saveWidth, height, (255, 255, 0)
                    )
                self.renderer.drawButton(
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
                self.renderer.drawRectangle(
                    xpos, ypos, saveWidth, height, palette.MEDIUM_GRAY
                )
                self.renderer.drawText(
                    label,
                    xpos + saveWidth // 2,
                    ypos + height // 2,
                    24,
                    palette.BLACK,
                )
                self.renderer.drawRectangle(
                    xpos + saveWidth + margin,
                    ypos,
                    deleteWidth,
                    height,
                    (140, 0, 0),
                )
                self.renderer.drawText(
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
        x, y = self.renderer.getDisplaySize()
        overlayWidth = x * 0.5
        overlayHeight = y * 0.3
        overlayX = x / 2 - overlayWidth / 2
        overlayY = y / 2 - overlayHeight / 2
        self.renderer.drawRectangle(
            overlayX, overlayY, overlayWidth, overlayHeight, palette.CHARCOAL
        )
        saveName = os.path.basename(self.confirmingDelete)
        self.renderer.drawText(
            "Delete '" + saveName + "'?",
            x / 2,
            overlayY + overlayHeight * 0.25,
            28,
            palette.WHITE,
        )
        self.renderer.drawText(
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
        self.renderer.drawButton(
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
        self.renderer.drawButton(
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
        self.renderer.drawText(
            "Enter: confirm  -  Esc: cancel",
            x / 2,
            btnY + buttonHeight + 8,
            14,
            palette.DIM_GRAY,
        )

    def drawNamingDialog(self):
        x, y = self.renderer.getDisplaySize()
        overlayWidth = x * 0.5
        overlayHeight = y * 0.35
        overlayX = x / 2 - overlayWidth / 2
        overlayY = y / 2 - overlayHeight / 2
        self.renderer.drawRectangle(
            overlayX, overlayY, overlayWidth, overlayHeight, palette.CHARCOAL
        )
        self.renderer.drawText(
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
        self.renderer.drawRectangle(
            inputX, inputY, inputWidth, inputHeight, palette.WHITE
        )
        displayText = self.newSaveNameInput + "_"
        self.renderer.drawText(
            displayText,
            x / 2,
            inputY + inputHeight / 2,
            24,
            palette.BLACK,
        )
        if self.newSaveNameError:
            self.renderer.drawText(
                self.newSaveNameError,
                x / 2,
                overlayY + overlayHeight * 0.60,
                18,
                (255, 120, 120),
            )
        self.renderer.drawText(
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
        self.renderer.drawButton(
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
        self.renderer.drawButton(
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
        x, y = self.renderer.getDisplaySize()
        buttonWidth = x / 5
        buttonHeight = y / 10
        margin = 20
        totalWidth = buttonWidth * 3 + margin * 2
        startX = x / 2 - totalWidth / 2
        ypos = y - buttonHeight - y / 12
        interactive = self.confirmingDelete is None and not self.namingNewSave

        if interactive:
            self.renderer.drawButton(
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
            self.renderer.drawButton(
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

            self.renderer.drawButton(
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
                self.renderer.drawRectangle(
                    bx, ypos, buttonWidth, buttonHeight, palette.MEDIUM_GRAY
                )
                self.renderer.drawText(
                    label,
                    bx + buttonWidth // 2,
                    ypos + buttonHeight // 2,
                    26 if i == 1 else 30,
                    (80, 80, 80),
                )

    def onStart(self):
        self.refreshSaveCache()

        # Wait for mouse button release to prevent click pass-through
        # from the previous screen (e.g. the main menu "play" button).
        while self.inputSource.getMouseButtons()[0]:
            for event in self.inputSource.pollEvents():
                if event.type == EventType.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break

            if self.changeScreen:
                break

            time.sleep(0.01)

    def handleEvent(self, event):
        if event.type == EventType.KEY_DOWN:
            self.handleKeyDownEvent(event.key)
        elif event.type == EventType.MOUSE_WHEEL:
            saves = self.getSaveDirectories()
            maxVisible = self._maxVisible()
            if event.scrollY > 0:
                self._moveCursorUp(saves, maxVisible)
            elif event.scrollY < 0:
                self._moveCursorDown(saves, maxVisible)
        elif event.type == EventType.TEXT_INPUT:
            if self.namingNewSave and not self._suppressTextInput:
                for ch in event.text:
                    if ch.isalnum() or ch in "-_ ":
                        self.newSaveNameInput += ch
                        self.newSaveNameError = ""

    def draw(self):
        # The text-input suppression only lasts the frame naming opened in.
        self._suppressTextInput = False
        self.renderer.clearScreen(palette.BLACK)
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
        else:
            self.drawControlsHint()

    def drawControlsHint(self):
        x, y = self.renderer.getDisplaySize()
        self.renderer.drawText(
            "Up/Down: choose  -  Enter: play  -  C: new save  -  T: sort  -  Esc: back",
            x / 2,
            y - 14,
            16,
            palette.MEDIUM_GRAY,
        )

    def onExit(self):
        if self.nextScreen == ScreenType.WORLD_SCREEN:
            self.initializeWorldScreen()

        self.scrollOffset = 0
        self._selectedIndex = 0
        self.confirmingDelete = None
        self.namingNewSave = False
        self.newSaveNameInput = ""
