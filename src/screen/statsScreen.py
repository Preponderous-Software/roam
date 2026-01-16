import datetime
import logging
import os
from client.api_client import RoamAPIClient
from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from stats.stats import Stats
from ui.status import Status
import pygame

# Configure logger
logger = logging.getLogger(__name__)

# @author Daniel McCoy Stephenson
class StatsScreen:
    def __init__(self, graphik: Graphik, config: Config, status: Status, stats: Stats, api_client: RoamAPIClient = None):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.stats = stats  # Keep for backward compatibility
        self.api_client = api_client
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = False
        
        # Stats data from server
        self.rooms_explored = 0
        self.food_eaten = 0

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
        elif key == pygame.K_PRINTSCREEN:
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
    
    def fetchStatsFromServer(self):
        """Fetch stats from server if API client and session ID are available."""
        if self.api_client and self.api_client.session_id:
            # Validate session ID
            if not isinstance(self.api_client.session_id, str) or not self.api_client.session_id.strip():
                logger.warning("Invalid session ID, falling back to local stats")
                self._loadLocalStats()
                return
            
            try:
                player_data = self.api_client.get_player(self.api_client.session_id)
                self.rooms_explored = player_data.get('roomsExplored', 0)
                self.food_eaten = player_data.get('foodEaten', 0)
                logger.debug(f"Successfully fetched stats from server: rooms_explored={self.rooms_explored}, food_eaten={self.food_eaten}")
            except Exception as e:
                logger.error(f"Failed to fetch player stats from server (session={self.api_client.session_id}): {e}", exc_info=True)
                # Fall back to local stats
                self._loadLocalStats()
        else:
            # Use local stats if no API client or session
            logger.debug("No API client or session ID available, using local stats")
            self._loadLocalStats()
    
    def _loadLocalStats(self):
        """Load stats from local Stats object."""
        self.rooms_explored = self.stats.getRoomsExplored()
        self.food_eaten = self.stats.getFoodEaten()

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawStats(self):
        x, y = self.graphik.getGameDisplay().get_size()

        # aim for center of screen
        x / 5
        height = y / 10
        xpos = x / 2
        ypos = 0 + height / 2

        # draw rooms explored
        text = "rooms explored: " + str(self.rooms_explored)
        self.graphik.drawText(text, xpos, ypos, 30, (255, 255, 255))

        # draw food eaten
        self.xpos = xpos
        self.ypos = ypos + height
        text = "food eaten: " + str(self.food_eaten)
        self.graphik.drawText(text, xpos, ypos + height, 30, (255, 255, 255))

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
            "back",
            self.switchToOptionsScreen,
        )

    def run(self):
        # Fetch stats from server when screen is opened
        self.fetchStatsFromServer()
        
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
