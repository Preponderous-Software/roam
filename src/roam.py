import pygame
import sys
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


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Roam:
    def __init__(self, config: Config, server_url: str = "http://localhost:8080"):
        pygame.init()
        pygame.display.set_icon(pygame.image.load("assets/images/player_down.png"))
        self.running = True
        self.config = config
        self.server_url = server_url
        
        # Initialize API client for server communication
        self.api_client = RoamAPIClient(server_url)
        self.session_id = None
        
        pygame.display.set_caption("Roam (Server-Backed)" + " (" + config.pathToSaveDirectory + ")")
        self.tickCounter = TickCounter(self.config)
        self.gameDisplay = self.initializeGameDisplay()
        self.graphik = Graphik(self.gameDisplay)
        self.status = Status(self.graphik, self.tickCounter)
        self.stats = Stats(self.config)
        
        # Player will be initialized from server when session starts
        self.player = None
        
        self.worldScreen = None  # Will be initialized after session starts
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

    def initializeGameDisplay(self):
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
        try:
            # Start server session
            session_data = self.api_client.init_session()
            self.session_id = session_data['sessionId']
            
            # Create player from server data
            player_data = session_data['player']
            self.player = Player(self.tickCounter.getTick())
            self._updatePlayerFromServerData(player_data)
            
            # Initialize screens that need player
            self.inventoryScreen = InventoryScreen(
                self.graphik, self.config, self.status, self.player.getInventory()
            )
            
            # Initialize world screen with API client
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
            self.worldScreen.initialize()
            
            self.status.set("Connected to server - Session started")
        except Exception as e:
            print(f"Failed to start session: {e}")
            self.status.set(f"Server connection failed: {e}")
            import traceback
            traceback.print_exc()
            # Return to main menu on failure
            self.nextScreen = ScreenType.MAIN_MENU_SCREEN
            self.changeScreen = True
    
    def _updatePlayerFromServerData(self, player_data):
        """Update local player object from server data."""
        if player_data:
            self.player.setEnergy(player_data.get('energy', 100.0))
            direction = player_data.get('direction', -1)
            if direction >= 0:
                self.player.setDirection(direction)

    def quitApplication(self):
        pygame.quit()
        quit()

    def run(self):
        while True:
            result = self.currentScreen.run()
            if result == ScreenType.MAIN_MENU_SCREEN:
                return "restart"
            if result == ScreenType.WORLD_SCREEN:
                if self.worldScreen is None:
                    self.status.set("Initializing...")
                    continue
                self.currentScreen = self.worldScreen
            elif result == ScreenType.OPTIONS_SCREEN:
                self.currentScreen = self.optionsScreen
            elif result == ScreenType.STATS_SCREEN:
                self.currentScreen = self.statsScreen
            elif result == ScreenType.INVENTORY_SCREEN:
                if self.inventoryScreen is None or self.player is None:
                    self.status.set("Player not initialized")
                    continue
                self.currentScreen = self.inventoryScreen
                self.inventoryScreen.setInventory(self.player.getInventory())
            elif result == ScreenType.CONFIG_SCREEN:
                self.currentScreen = self.configScreen
            elif result == ScreenType.NONE:
                # Clean up session before quitting
                try:
                    if self.session_id:
                        self.api_client.delete_session()
                        print("Session ended")
                except Exception as e:
                    print(f"Error ending session: {e}")
                self.quitApplication()
            else:
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
except Exception as e:
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

roam = Roam(config, server_url)
while True:
    result = roam.run()
    if result != "restart":
        break
    # Clean up session before restarting
    try:
        if getattr(roam, "session_id", None):
            roam.api_client.delete_session()
            print("Session ended")
    except Exception as e:
        print(f"Error ending session: {e}")
    roam = Roam(config, server_url)
