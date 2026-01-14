from config.config import Config
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status
import pygame
import logging

logger = logging.getLogger(__name__)

# @author Daniel McCoy Stephenson
class OptionsScreen:
    def __init__(self, graphik: Graphik, config: Config, status: Status, api_client=None, session_id=None):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.api_client = api_client
        self.session_id = session_id
        self.running = True
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.leave_session_error = ""
    
    def setSessionInfo(self, api_client, session_id):
        """Update session information for leave session functionality."""
        self.api_client = api_client
        self.session_id = session_id

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
            self.switchToWorldScreen()

    def switchToWorldScreen(self):
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def switchToStatsScreen(self):
        self.nextScreen = ScreenType.STATS_SCREEN
        self.changeScreen = True

    def switchToInventoryScreen(self):
        self.nextScreen = ScreenType.INVENTORY_SCREEN
        self.changeScreen = True

    def switchToMainMenuScreen(self):
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = True

    def switchToConfigScreen(self):
        self.nextScreen = ScreenType.CONFIG_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        self.nextScreen = ScreenType.NONE
        self.changeScreen = True
    
    def leaveSession(self):
        """Leave the current multiplayer session."""
        if not self.api_client or not self.session_id:
            self.leave_session_error = "Not in a session"
            return
        
        try:
            self.api_client.leave_session(self.session_id)
            self.status.set("Left session successfully")
            # Return to main menu after leaving
            self.switchToMainMenuScreen()
        except Exception as e:
            error_str = str(e)
            if "403" in error_str or "owner" in error_str.lower():
                self.leave_session_error = "Session owner cannot leave"
            else:
                self.leave_session_error = f"Error: {error_str}"
            logger.error(f"Failed to leave session: {e}")

    def drawMenuButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 3
        height = y / 10
        # start at top of screen
        xpos = x / 2 - width / 2
        ypos = 0 + height / 2
        margin = 10
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "main menu",
            self.switchToMainMenuScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "stats",
            self.switchToStatsScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "inventory",
            self.switchToInventoryScreen,
        )
        ypos = ypos + height + margin
        
        # Add leave session button if in a multiplayer session
        if self.api_client and self.session_id:
            self.graphik.drawButton(
                xpos,
                ypos,
                width,
                height,
                (255, 150, 150),
                (0, 0, 0),
                30,
                "leave session",
                self.leaveSession,
            )
            
            # Show error if any
            if self.leave_session_error:
                error_y = ypos + height + 5
                self.graphik.drawText(self.leave_session_error, x / 2, error_y, 18, (255, 50, 50))
        
        self.drawBackButton()

    def drawBackButton(self):
        # draw in bottom right corner
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 3
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
            self.switchToWorldScreen,
        )

    def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return ScreenType.NONE
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawMenuButtons()
            pygame.display.update()

        self.changeScreen = False
        return self.nextScreen
