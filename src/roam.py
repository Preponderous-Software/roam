import pygame
import sys
import logging
from client.api_client import RoamAPIClient
from config.config import Config
from player.player import Player
from lib.graphik.src.graphik import Graphik
from screen.configScreen import ConfigScreen
from screen.inventoryScreen import InventoryScreen
from screen.mainMenuScreen import MainMenuScreen
from screen.optionsScreen import OptionsScreen
from screen.screenType import ScreenType
from screen.statsScreen import StatsScreen
from stats.stats import Stats
from ui.status import Status
from screen.serverBackedWorldScreen import ServerBackedWorldScreen
from world.tickCounter import TickCounter

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Roam:
    def __init__(self, config: Config, server_url: str = "http://localhost:8080"):
        logger.info("=" * 60)
        logger.info("Initializing Roam client with server-backed architecture")
        logger.info(f"Server URL: {server_url}")
        logger.info(f"Save directory: {config.pathToSaveDirectory}")
        logger.info("=" * 60)
        
        pygame.init()
        pygame.display.set_icon(pygame.image.load("assets/images/player_down.png"))
        self.running = True
        self.config = config
        self.server_url = server_url
        
        # Initialize API client for server communication
        logger.debug("Creating RoamAPIClient instance")
        self.api_client = RoamAPIClient(server_url)
        self.session_id = None
        logger.info("API client initialized successfully")
        
        pygame.display.set_caption("Roam (Server-Backed)" + " (" + config.pathToSaveDirectory + ")")
        self.tickCounter = TickCounter(self.config)
        self.gameDisplay = self.initializeGameDisplay()
        self.graphik = Graphik(self.gameDisplay)
        self.status = Status(self.graphik, self.tickCounter)
        self.stats = Stats(self.config)
        
        # Player will be initialized from server when session starts
        self.player = None
        logger.debug("Player will be initialized from server on session start")
        
        self.worldScreen = None  # Will be initialized after session starts
        logger.debug("Initializing UI screens")
        self.optionsScreen = OptionsScreen(self.graphik, self.config, self.status)
        self.mainMenuScreen = MainMenuScreen(
            self.graphik, self.config, self.initializeWorldScreen
        )
        self.statsScreen = StatsScreen(
            self.graphik, self.config, self.status, self.stats
        )
        self.inventoryScreen = None  # Will be initialized after player is created
        self.configScreen = ConfigScreen(self.graphik, self.config, self.status)
        self.currentScreen = self.mainMenuScreen
        logger.info("Roam client initialization complete")

    def initializeGameDisplay(self):
        logger.debug(f"Initializing game display: {self.config.displayWidth}x{self.config.displayHeight}, fullscreen={self.config.fullscreen}")
        if self.config.fullscreen:
            return pygame.display.set_mode(
                (self.config.displayWidth, self.config.displayHeight), pygame.FULLSCREEN
            )
        else:
            return pygame.display.set_mode(
                (self.config.displayWidth, self.config.displayHeight), pygame.RESIZABLE
            )

    def initializeWorldScreen(self):
        """Initialize world screen and start server session."""
        logger.info("=" * 60)
        logger.info("Initializing world screen - starting server session")
        logger.info("=" * 60)
        
        try:
            # Start server session
            logger.debug("Calling API: init_session()")
            session_data = self.api_client.init_session()
            self.session_id = session_data['sessionId']
            logger.info(f"Session initialized successfully: {self.session_id}")
            logger.debug(f"Session data: currentTick={session_data.get('currentTick', 0)}")
            
            # Create player from server data
            player_data = session_data['player']
            logger.debug(f"Creating player from server data: energy={player_data.get('energy')}, direction={player_data.get('direction')}")
            self.player = Player(self.tickCounter.getTick())
            self._updatePlayerFromServerData(player_data)
            logger.info("Player initialized from server state")
            
            # Initialize screens that need player
            logger.debug("Initializing inventory screen")
            self.inventoryScreen = InventoryScreen(
                self.graphik, self.config, self.status, self.player.getInventory()
            )
            
            # Initialize world screen with API client
            logger.debug("Creating ServerBackedWorldScreen instance")
            self.worldScreen = ServerBackedWorldScreen(
                self.graphik,
                self.config,
                self.status,
                self.tickCounter,
                self.stats,
                self.player,
                self.api_client,
                self.session_id,
            )
            logger.debug("Calling worldScreen.initialize()")
            self.worldScreen.initialize()
            
            self.status.set("Connected to server - Session started")
            logger.info("World screen initialization complete")
        except Exception as e:
            logger.error(f"Failed to start session: {e}", exc_info=True)
            print(f"Failed to start session: {e}")
            self.status.set(f"Server connection failed: {e}")
            import traceback
            traceback.print_exc()
            # Return to main menu on failure
            logger.warning("Returning to main menu due to session initialization failure")
            self.nextScreen = ScreenType.MAIN_MENU_SCREEN
            self.changeScreen = True
    
    def _updatePlayerFromServerData(self, player_data):
        """Update local player object from server data."""
        if player_data:
            energy = player_data.get('energy', 100.0)
            logger.debug(f"Updating player energy: {energy}")
            self.player.setEnergy(energy)
            
            direction = player_data.get('direction', -1)
            if direction >= 0:
                logger.debug(f"Updating player direction: {direction}")
                self.player.setDirection(direction)

    def quitApplication(self):
        logger.info("Quitting application")
        pygame.quit()
        quit()

    def run(self):
        logger.info("Starting main game loop")
        while True:
            result = self.currentScreen.run()
            logger.debug(f"Screen returned: {result}")
            
            if result == ScreenType.MAIN_MENU_SCREEN:
                logger.info("Restart requested")
                return "restart"
            if result == ScreenType.WORLD_SCREEN:
                if self.worldScreen is None:
                    logger.debug("World screen not initialized, showing status")
                    self.status.set("Initializing...")
                    continue
                logger.debug("Switching to world screen")
                self.currentScreen = self.worldScreen
            elif result == ScreenType.OPTIONS_SCREEN:
                logger.debug("Switching to options screen")
                self.currentScreen = self.optionsScreen
            elif result == ScreenType.STATS_SCREEN:
                logger.debug("Switching to stats screen")
                self.currentScreen = self.statsScreen
            elif result == ScreenType.INVENTORY_SCREEN:
                if self.inventoryScreen is None or self.player is None:
                    logger.warning("Cannot open inventory - player not initialized")
                    self.status.set("Player not initialized")
                    continue
                logger.debug("Switching to inventory screen")
                self.currentScreen = self.inventoryScreen
                self.inventoryScreen.setInventory(self.player.getInventory())
            elif result == ScreenType.CONFIG_SCREEN:
                logger.debug("Switching to config screen")
                self.currentScreen = self.configScreen
            elif result == ScreenType.NONE:
                # Clean up session before quitting
                logger.info("Quit requested - cleaning up session")
                try:
                    if self.session_id:
                        logger.debug(f"Deleting session: {self.session_id}")
                        self.api_client.delete_session()
                        logger.info("Session ended successfully")
                        print("Session ended")
                except Exception as e:
                    logger.error(f"Error ending session: {e}")
                    print(f"Error ending session: {e}")
                self.quitApplication()
            else:
                logger.error(f"Unrecognized screen type: {result}")
                print("unrecognized screen: " + result)
                self.quitApplication()


pygame.init()
config = Config()

# Check for server URL argument
server_url = "http://localhost:8080"
if len(sys.argv) > 1:
    server_url = sys.argv[1]

# Validate server URL format
from urllib.parse import urlparse

try:
    parsed = urlparse(server_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL format")
    if parsed.scheme not in ['http', 'https']:
        raise ValueError("Only HTTP and HTTPS protocols are supported")
    logger.info(f"Server URL validated: {server_url}")
except Exception as e:
    logger.error(f"Invalid server URL: {server_url} - {e}")
    print("=" * 60)
    print("ERROR: Invalid server URL")
    print("=" * 60)
    print(f"URL: {server_url}")
    print(f"Error: {e}")
    print()
    print("Usage: python3 roam.py [server_url]")
    print("Example: python3 roam.py http://localhost:8080")
    print("=" * 60)
    sys.exit(1)

print("=" * 60)
print("Roam - Server-Backed Client")
print("=" * 60)
print(f"Server URL: {server_url}")
print("Make sure the Spring Boot server is running!")
print("=" * 60)
print()

logger.info("Creating Roam instance")
roam = Roam(config, server_url)
while True:
    logger.info("Starting game run cycle")
    result = roam.run()
    if result != "restart":
        logger.info("Game loop ended without restart")
        break
    # Clean up session before restarting
    logger.info("Restart requested - cleaning up previous session")
    try:
        if getattr(roam, "session_id", None):
            logger.debug(f"Cleaning up session before restart: {roam.session_id}")
            roam.api_client.delete_session()
            logger.info("Previous session cleaned up")
            print("Session ended")
    except Exception as e:
        logger.error(f"Error ending session during restart: {e}")
        print(f"Error ending session: {e}")
    logger.info("Creating new Roam instance for restart")
    roam = Roam(config, server_url)

logger.info("Application exiting normally")
