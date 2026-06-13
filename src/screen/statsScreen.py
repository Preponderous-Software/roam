from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from rendering.renderer import Renderer
from screen.screenType import ScreenType
from stats.stats import Stats
from goals.goals import Goals
from ui.status import Status
import pygame
from ui import palette


# @author Daniel McCoy Stephenson
@component
class StatsScreen:
    def __init__(
        self,
        renderer: Renderer,
        config: Config,
        status: Status,
        stats: Stats,
        keyBindings: KeyBindings,
        goals: Goals,
    ):
        self.renderer = renderer
        self.config = config
        self.status = status
        self.stats = stats
        self.keyBindings = keyBindings
        self.goals = goals
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = False

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
            self.switchToOptionsScreen()
        elif key == self.keyBindings.getKey("screenshot"):
            self.renderer.captureScreenshot()

    def switchToOptionsScreen(self):
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawStats(self):
        x, y = self.renderer.getDisplaySize()

        self.renderer.drawText("Statistics", x / 2, 25, 36, palette.WHITE)

        lineSpacing = y / 10
        xpos = x / 2
        ypos = 70

        text = "Score: " + str(self.stats.getScore())
        self.renderer.drawText(text, xpos, ypos, 30, palette.WHITE)
        self.renderer.drawText(
            "(+1 per new area or meal, -10% per death)",
            xpos,
            ypos + 24,
            16,
            (170, 170, 170),
        )

        text = "Rooms Explored: " + str(self.stats.getRoomsExplored())
        self.renderer.drawText(text, xpos, ypos + lineSpacing, 30, palette.WHITE)

        text = "Food Eaten: " + str(self.stats.getFoodEaten())
        self.renderer.drawText(text, xpos, ypos + lineSpacing * 2, 30, palette.WHITE)

        text = "Deaths: " + str(self.stats.getNumberOfDeaths())
        self.renderer.drawText(text, xpos, ypos + lineSpacing * 3, 30, palette.WHITE)

        self.drawGoals(xpos, ypos + lineSpacing * 3 + 60)

    def drawGoals(self, xpos, startY):
        completed = self.goals.getCompletedCount()
        total = self.goals.getTotalCount()
        allComplete = total > 0 and completed == total
        header = "Goals (" + str(completed) + "/" + str(total) + ")"
        if allComplete:
            header += " - All complete!"
        headerColor = (120, 220, 120) if allComplete else palette.WHITE
        self.renderer.drawText(header, xpos, startY, 26, headerColor)

        goals = self.goals.getGoals()
        columnCount = 2
        perColumn = (len(goals) + columnCount - 1) // columnCount
        displayWidth = self.renderer.getDisplaySize()[0]
        columnX = [displayWidth / 4, displayWidth * 3 / 4]
        rowSpacing = 26
        rowsStartY = startY + 34

        for i, goal in enumerate(goals):
            progress = self.goals.getProgress(goal)
            if goal.isCompleted():
                marker = "[X] "
                color = (120, 220, 120)
            else:
                marker = "[ ] "
                color = palette.GRAY
            line = marker + goal.getDescription()
            if goal.getTarget() > 1:
                line += " (" + str(progress) + "/" + str(goal.getTarget()) + ")"
            column = i // perColumn
            row = i % perColumn
            self.renderer.drawText(
                line, columnX[column], rowsStartY + row * rowSpacing, 18, color
            )

    def drawBackButton(self):
        x, y = self.renderer.getDisplaySize()
        width = x / 5
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = y / 2 - height / 2 + width
        self.renderer.drawButton(
            xpos,
            ypos,
            width,
            height,
            palette.WHITE,
            palette.BLACK,
            30,
            "Back",
            self.switchToOptionsScreen,
        )

    def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)

            self.renderer.clearScreen(palette.BLACK)
            self.drawStats()
            self.drawBackButton()
            self.renderer.present()

        self.changeScreen = False
        return self.nextScreen
