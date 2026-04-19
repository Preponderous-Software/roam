import datetime
import os
from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from stats.stats import Stats
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
    ):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.stats = stats
        self.keyBindings = keyBindings
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = False

    # @source https://stackoverflow.com/questions/63342477/how-to-take-screenshot-of-entire-display-pygame
    def captureScreen(self, name, pos, size):  # (pygame Surface, String, tuple, tuple)
        image = pygame.Surface(size)  # Create image surface
        image.blit(
            self.graphik.getGameDisplay(), (0, 0), (pos, size)
        )  # Blit portion of the display to the image
        pygame.image.save(image, name)  # Save the image to the disk**

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
            self.switchToOptionsScreen()
        elif key == self.keyBindings.getKey("screenshot"):
            screenshotsFolder = "screenshots"
            if not os.path.exists(screenshotsFolder):
                os.makedirs(screenshotsFolder)
            x, y = self.graphik.getGameDisplay().get_size()
            self.captureScreen(
                screenshotsFolder
                + "/screenshot-"
                + str(datetime.datetime.now()).replace(" ", "-").replace(":", ".")
                + ".png",
                (0, 0),
                (x, y),
            )

    def switchToOptionsScreen(self):
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawStats(self):
        x, y = self.graphik.getGameDisplay().get_size()

        self.graphik.drawText("Statistics", x / 2, 25, 36, (255, 255, 255))

        height = y / 10
        xpos = x / 2
        ypos = 70

        text = "Score: " + str(self.stats.getScore())
        self.graphik.drawText(text, xpos, ypos, 30, (255, 255, 255))

        text = "Rooms Explored: " + str(self.stats.getRoomsExplored())
        self.graphik.drawText(text, xpos, ypos + height, 30, (255, 255, 255))

        text = "Food Eaten: " + str(self.stats.getFoodEaten())
        self.graphik.drawText(text, xpos, ypos + height * 2, 30, (255, 255, 255))

        text = "Deaths: " + str(self.stats.getNumberOfDeaths())
        self.graphik.drawText(text, xpos, ypos + height * 3, 30, (255, 255, 255))

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
