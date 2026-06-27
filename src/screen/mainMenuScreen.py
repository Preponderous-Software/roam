import webbrowser

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
        self._selectedIndex = 0  # 0=Play, 1=Settings, 2=Quit

    def switchToSaveSelectionScreen(self):
        self.nextScreen = ScreenType.SAVE_SELECTION_SCREEN
        self.changeScreen = True

    def switchToConfigScreen(self):
        self.nextScreen = ScreenType.CONFIG_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        # Request shutdown the backend-neutral way: returning NONE to the main
        # loop lets Roam.quitApplication do the real teardown (save window size,
        # frontend.quit()) instead of calling pygame directly here.
        self.nextScreen = ScreenType.NONE
        self.changeScreen = True

    def drawText(self):
        x, y = self.renderer.getDisplaySize()
        xpos = x / 2
        ypos = y / 10
        self.renderer.drawText("Roam", xpos, ypos, 64, palette.WHITE)
        ypos = y / 3
        self.renderer.drawText(
            "Explore a procedurally-generated world", xpos, ypos, 24, palette.GRAY
        )

    _MENU_ITEMS = [
        ("Play", "switchToSaveSelectionScreen"),
        ("Settings", "switchToConfigScreen"),
        ("Quit", "quitApplication"),
    ]

    def drawMenuButtons(self):
        x, y = self.renderer.getDisplaySize()
        width = x / 5
        height = y / 10
        xpos = x / 2 - width / 2
        startY = y / 2 - height / 2
        margin = 10
        for i, (label, method) in enumerate(self._MENU_ITEMS):
            btnY = startY + i * (height + margin)
            self.renderer.drawButton(
                xpos,
                btnY,
                width,
                height,
                palette.WHITE,
                palette.BLACK,
                30,
                label,
                getattr(self, method),
            )
            if i == self._selectedIndex:
                self.renderer.drawSelectionHighlight(
                    xpos, btnY, width, height, (255, 255, 0)
                )
        hintY = startY + len(self._MENU_ITEMS) * (height + margin) + 6
        selectedLabel = self._MENU_ITEMS[self._selectedIndex][0]
        self.renderer.drawText(
            f"W/S or Up/Down: navigate  -  Enter: {selectedLabel}  -  Esc: Quit",
            x / 2,
            hintY,
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
        elif key in (KeyCode.UP, KeyCode.W):
            self._selectedIndex = (self._selectedIndex - 1) % len(self._MENU_ITEMS)
        elif key in (KeyCode.DOWN, KeyCode.S):
            self._selectedIndex = (self._selectedIndex + 1) % len(self._MENU_ITEMS)
        elif key in (KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE):
            getattr(self, self._MENU_ITEMS[self._selectedIndex][1])()
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
