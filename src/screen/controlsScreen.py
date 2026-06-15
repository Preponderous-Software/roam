from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from rendering.renderer import Renderer
from rendering.inputSource import InputSource
from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode, displayName, fromInt
from screen.screenType import ScreenType
from screen.screen import Screen
from ui import palette


# @author Copilot
# @since April 19th, 2026
@component
class ControlsScreen(Screen):
    def __init__(
        self,
        renderer: Renderer,
        inputSource: InputSource,
        config: Config,
        keyBindings: KeyBindings,
    ):
        self.renderer = renderer
        self.inputSource = inputSource
        self.config = config
        self.keyBindings = keyBindings
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = False
        self.waitingForKey = None
        self.scrollOffset = 0
        self.pendingBindings = None

    def switchToOptionsScreen(self):
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = True

    def saveAndReturn(self):
        if self.pendingBindings is not None:
            self.keyBindings.bindings = dict(self.pendingBindings)
            self.keyBindings.saveToConfigFile(self.config)
        self.pendingBindings = None
        self.waitingForKey = None
        self.scrollOffset = 0
        self.switchToOptionsScreen()

    def cancelAndReturn(self):
        self.pendingBindings = None
        self.waitingForKey = None
        self.scrollOffset = 0
        self.switchToOptionsScreen()

    def resetToDefaults(self):
        self.pendingBindings = dict(self.keyBindings.DEFAULT_BINDINGS)

    def getActiveBindings(self):
        if self.pendingBindings is not None:
            return self.pendingBindings
        return self.keyBindings.bindings

    def getActiveConflicts(self):
        return self.keyBindings.getConflictsForBindings(self.getActiveBindings())

    def drawTitle(self):
        x, y = self.renderer.getDisplaySize()
        self.renderer.drawText("Controls", x / 2, 25, 36, palette.WHITE)

    def drawBindings(self):
        x, y = self.renderer.getDisplaySize()
        actions = self.keyBindings.getActions()
        bindings = self.getActiveBindings()
        conflicts = self.getActiveConflicts()

        rowHeight = 35
        startY = 60
        labelX = x * 0.15
        keyX = x * 0.65
        buttonWidth = x * 0.25
        buttonHeight = 28

        visibleRows = int((y - startY - 80) / rowHeight)
        maxOffset = max(0, len(actions) - visibleRows)
        self.scrollOffset = max(0, min(self.scrollOffset, maxOffset))

        visibleActions = actions[self.scrollOffset : self.scrollOffset + visibleRows]

        for i, action in enumerate(visibleActions):
            rowY = startY + i * rowHeight
            label = self.keyBindings.getLabel(action)
            key = bindings.get(action, self.keyBindings.DEFAULT_BINDINGS.get(action))
            keyName = displayName(key if isinstance(key, KeyCode) else fromInt(key))

            isConflict = action in conflicts
            labelColor = (255, 100, 100) if isConflict else palette.WHITE
            self.renderer.drawText(
                label, labelX, rowY + buttonHeight / 2, 20, labelColor
            )

            if self.waitingForKey == action:
                bgColor = (100, 100, 255)
                displayText = "Press a key  (Esc cancels)"
            else:
                bgColor = (255, 50, 50) if isConflict else palette.DARKER_GRAY
                displayText = keyName

            self.renderer.drawButton(
                keyX,
                rowY,
                buttonWidth,
                buttonHeight,
                bgColor,
                palette.WHITE,
                18,
                displayText,
                lambda a=action: self.startRemap(a),
            )

        if maxOffset > 0:
            scrollInfo = (
                str(self.scrollOffset + 1)
                + "-"
                + str(min(self.scrollOffset + visibleRows, len(actions)))
                + " of "
                + str(len(actions))
            )
            self.renderer.drawText(scrollInfo, x / 2, y - 70, 16, palette.MEDIUM_GRAY)
            self.renderer.drawText(
                "Scroll or Up/Down to see more", x / 2, y - 92, 14, palette.DIM_GRAY
            )

    def drawBottomButtons(self):
        x, y = self.renderer.getDisplaySize()
        buttonWidth = x / 5
        buttonHeight = 35
        bottomY = y - 45
        margin = 10

        conflicts = self.getActiveConflicts()
        hasConflicts = len(conflicts) > 0

        if hasConflicts:
            conflictCount = len(conflicts)
            noun = "conflict" if conflictCount == 1 else "conflicts"
            message = (
                "Resolve "
                + str(conflictCount)
                + " key "
                + noun
                + " (shown in red) to enable Save"
            )
            self.renderer.drawText(message, x / 2, bottomY - 18, 16, (255, 120, 120))

        totalWidth = buttonWidth * 3 + margin * 2
        startX = (x - totalWidth) / 2

        self.renderer.drawButton(
            startX,
            bottomY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
            20,
            "Reset Defaults",
            self.resetToDefaults,
        )

        if hasConflicts:
            saveColor = palette.DARK_GRAY
        else:
            saveColor = palette.GREEN
        self.renderer.drawButton(
            startX + buttonWidth + margin,
            bottomY,
            buttonWidth,
            buttonHeight,
            saveColor,
            palette.BLACK if not hasConflicts else palette.MEDIUM_GRAY,
            20,
            "Save",
            self.saveAndReturn if not hasConflicts else (lambda: None),
        )

        self.renderer.drawButton(
            startX + 2 * (buttonWidth + margin),
            bottomY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
            20,
            "Cancel",
            self.cancelAndReturn,
        )

    def startRemap(self, action):
        if self.pendingBindings is None:
            self.pendingBindings = dict(self.keyBindings.bindings)
        self.waitingForKey = action

    def handleKeyDownEvent(self, key):
        if self.waitingForKey is not None:
            if key == KeyCode.ESCAPE:
                self.waitingForKey = None
                return
            if key is None:
                # An unmodeled key can't be bound; keep waiting for a real one.
                return
            if self.pendingBindings is None:
                self.pendingBindings = dict(self.keyBindings.bindings)
            self.pendingBindings[self.waitingForKey] = key
            self.waitingForKey = None
            return
        if key == KeyCode.ESCAPE:
            self.cancelAndReturn()
        elif key == KeyCode.UP:
            self.scrollOffset = max(0, self.scrollOffset - 1)
        elif key == KeyCode.DOWN:
            self.scrollOffset += 1
        elif key in (KeyCode.RETURN, KeyCode.KP_ENTER):
            if not self.keyBindings.getConflictsForBindings(
                self.pendingBindings or self.keyBindings.bindings
            ):
                self.saveAndReturn()

    def handleScrollEvent(self, event):
        if event.scrollY > 0:
            self.scrollOffset = max(0, self.scrollOffset - 1)
        elif event.scrollY < 0:
            self.scrollOffset += 1

    def onStart(self):
        self.pendingBindings = None
        self.waitingForKey = None
        self.scrollOffset = 0

    def handleEvent(self, event):
        if event.type == EventType.KEY_DOWN:
            self.handleKeyDownEvent(event.key)
        elif event.type == EventType.MOUSE_WHEEL:
            self.handleScrollEvent(event)

    def draw(self):
        self.renderer.clearScreen(palette.BLACK)
        self.drawTitle()
        self.drawBindings()
        self.drawBottomButtons()
