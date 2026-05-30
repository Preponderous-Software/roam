from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from screen.screenshotHelper import takeScreenshot
from stats.stats import Stats
from goals.goals import Goals
from ui.status import Status
import pygame


# @author Daniel McCoy Stephenson
@component
class StatsScreen:
    def __init__(
        self,
        graphik: Graphik,
        config: Config,
        status: Status,
        stats: Stats,
        keyBindings: KeyBindings,
        goals: Goals,
    ):
        self.graphik = graphik
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
            takeScreenshot(self.graphik.getGameDisplay())

    def switchToOptionsScreen(self):
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawStats(self):
        x, y = self.graphik.getGameDisplay().get_size()

        self.graphik.drawText("Statistics", x / 2, 25, 36, (255, 255, 255))

        lineSpacing = y / 10
        xpos = x / 2
        ypos = 70

        text = "Score: " + str(self.stats.getScore())
        self.graphik.drawText(text, xpos, ypos, 30, (255, 255, 255))
        self.graphik.drawText(
            "(+1 per new area or meal, -10% per death)",
            xpos,
            ypos + 24,
            16,
            (170, 170, 170),
        )

        text = "Rooms Explored: " + str(self.stats.getRoomsExplored())
        self.graphik.drawText(text, xpos, ypos + lineSpacing, 30, (255, 255, 255))

        text = "Food Eaten: " + str(self.stats.getFoodEaten())
        self.graphik.drawText(text, xpos, ypos + lineSpacing * 2, 30, (255, 255, 255))

        text = "Deaths: " + str(self.stats.getNumberOfDeaths())
        self.graphik.drawText(text, xpos, ypos + lineSpacing * 3, 30, (255, 255, 255))

        self.drawGoals(xpos, ypos + lineSpacing * 3 + 60)

    def drawGoals(self, xpos, startY):
        header = (
            "Goals ("
            + str(self.goals.getCompletedCount())
            + "/"
            + str(self.goals.getTotalCount())
            + ")"
        )
        self.graphik.drawText(header, xpos, startY, 26, (255, 255, 255))

        goals = self.goals.getGoals()
        columnCount = 2
        perColumn = (len(goals) + columnCount - 1) // columnCount
        displayWidth = self.graphik.getGameDisplay().get_size()[0]
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
                color = (200, 200, 200)
            line = (
                marker
                + goal.getDescription()
                + " ("
                + str(progress)
                + "/"
                + str(goal.getTarget())
                + ")"
            )
            column = i // perColumn
            row = i % perColumn
            self.graphik.drawText(
                line, columnX[column], rowsStartY + row * rowSpacing, 18, color
            )

    def drawBackButton(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 5
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = y / 2 - height / 2 + width
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
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

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawStats()
            self.drawBackButton()
            pygame.display.update()

        self.changeScreen = False
        return self.nextScreen
