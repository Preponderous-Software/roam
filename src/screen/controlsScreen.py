import pygame
from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui import palette


# @author Copilot
# @since April 19th, 2026
@component
class ControlsScreen:
    def __init__(self, graphik: Graphik, config: Config, keyBindings: KeyBindings):
        self.graphik = graphik
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
        x, y = self.graphik.getGameDisplay().get_size()
        self.graphik.drawText("Controls", x / 2, 25, 36, palette.WHITE)

    def drawBindings(self):
        x, y = self.graphik.getGameDisplay().get_size()
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
            keyName = pygame.key.name(key) if key is not None else "None"

            isConflict = action in conflicts
            labelColor = (255, 100, 100) if isConflict else palette.WHITE
            self.graphik.drawText(
                label, labelX, rowY + buttonHeight / 2, 20, labelColor
            )

            if self.waitingForKey == action:
                bgColor = (100, 100, 255)
                displayText = "Press a key  (Esc cancels)"
            else:
                bgColor = (255, 50, 50) if isConflict else palette.DARKER_GRAY
                displayText = keyName

            self.graphik.drawButton(
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
            self.graphik.drawText(scrollInfo, x / 2, y - 70, 16, palette.MEDIUM_GRAY)
            self.graphik.drawText(
                "Scroll to see more", x / 2, y - 92, 14, palette.DIM_GRAY
            )

    def drawBottomButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
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
            self.graphik.drawText(message, x / 2, bottomY - 18, 16, (255, 120, 120))

        totalWidth = buttonWidth * 3 + margin * 2
        startX = (x - totalWidth) / 2

        self.graphik.drawButton(
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
        self.graphik.drawButton(
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

        self.graphik.drawButton(
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
            if key == pygame.K_ESCAPE:
                self.waitingForKey = None
                return
            if self.pendingBindings is None:
                self.pendingBindings = dict(self.keyBindings.bindings)
            self.pendingBindings[self.waitingForKey] = key
            self.waitingForKey = None
            return
        if key == pygame.K_ESCAPE:
            self.cancelAndReturn()

    def handleScrollEvent(self, event):
        if event.y > 0:
            self.scrollOffset = max(0, self.scrollOffset - 1)
        elif event.y < 0:
            self.scrollOffset += 1

    def run(self):
        self.pendingBindings = None
        self.waitingForKey = None
        self.scrollOffset = 0
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ScreenType.NONE
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)
                elif event.type == pygame.MOUSEWHEEL:
                    self.handleScrollEvent(event)

            self.graphik.getGameDisplay().fill(palette.BLACK)
            self.drawTitle()
            self.drawBindings()
            self.drawBottomButtons()
            pygame.display.update()

        self.changeScreen = False
        return self.nextScreen
