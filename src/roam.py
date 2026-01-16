import pygame
import sys
import logging
from client.api_client import RoamAPIClient
from config.config import Config
from player.player import Player
from lib.graphik.src.graphik import Graphik
from screen.configScreen import ConfigScreen
from screen.inventoryScreen import InventoryScreen
from screen.loginScreen import LoginScreen
from screen.mainMenuScreen import MainMenuScreen
from screen.optionsScreen import OptionsScreen
from screen.screenType import ScreenType
from screen.statsScreen import StatsScreen
from stats.stats import Stats
from ui.status import Status
from screen.serverBackedWorldScreen import ServerBackedWorldScreen
from world.tickCounter import TickCounter

# Import item classes for inventory restoration (used in serverBackedWorldScreen)
from entity.apple import Apple
from entity.banana import Banana
from entity.stone import Stone
from entity.coalOre import CoalOre
from entity.ironOre import IronOre
from entity.oakWood import OakWood
from entity.jungleWood import JungleWood
from entity.grass import Grass
from entity.leaves import Leaves

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

        pygame.display.set_caption(
            "Roam (Server-Backed)" + " (" + config.pathToSaveDirectory + ")"
        )
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
        self.loginScreen = LoginScreen(
            self.graphik, self.config, self.status, self.api_client
        )
        self.optionsScreen = OptionsScreen(self.graphik, self.config, self.status)
        self.mainMenuScreen = MainMenuScreen(
            self.graphik, self.config, self.initializeWorldScreen
        )
        self.statsScreen = StatsScreen(
            self.graphik, self.config, self.status, self.stats
        )
        self.inventoryScreen = None  # Will be initialized after player is created
        self.configScreen = ConfigScreen(self.graphik, self.config, self.status)

        # Start with login screen if not authenticated, otherwise main menu
        if not self.api_client.is_authenticated():
            self.currentScreen = self.loginScreen
            logger.info("Starting with login screen (not authenticated)")
        else:
            self.currentScreen = self.mainMenuScreen
            logger.info("Starting with main menu (already authenticated)")

        logger.info("Roam client initialization complete")

    def initializeGameDisplay(self):
        logger.debug(
            f"Initializing game display: {self.config.displayWidth}x{self.config.displayHeight}, fullscreen={self.config.fullscreen}"
        )
        if self.config.fullscreen:
            return pygame.display.set_mode(
                (self.config.displayWidth, self.config.displayHeight), pygame.FULLSCREEN
            )
        else:
            return pygame.display.set_mode(
                (self.config.displayWidth, self.config.displayHeight), pygame.RESIZABLE
            )

    def initializeWorldScreen(self):
        """Initialize world screen and start/resume server session."""
        logger.info("=" * 60)
        logger.info("Initializing world screen - starting/resuming server session")
        logger.info("=" * 60)

        try:
            # Get current authenticated username
            username = (
                self.api_client.access_token and self._extract_username_from_token()
            )
            if not username:
                # Fallback - create new session
                username = "unknown"
                logger.warning("Could not extract username from token")

            # Try to resume existing session or create new one
            session_file = f"{self.config.pathToSaveDirectory}/session_{username}.txt"
            existing_session_id = None

            # Check for saved session ID
            try:
                import os

                if os.path.exists(session_file):
                    with open(session_file, "r") as f:
                        existing_session_id = f.read().strip()
                    logger.info(
                        f"Found existing session ID for {username}: {existing_session_id}"
                    )
            except Exception as e:
                logger.warning(f"Could not read session file: {e}")

            # Try to load existing session
            session_data = None
            if existing_session_id:
                try:
                    logger.debug(f"Attempting to load session: {existing_session_id}")
                    session_data = self.api_client.load_session(existing_session_id)
                    self.session_id = existing_session_id
                    logger.info(
                        f"✓ Successfully loaded existing session: {self.session_id}"
                    )
                    logger.info(
                        f"  Session data: currentTick={session_data.get('currentTick', 0)}"
                    )
                except Exception as e:
                    logger.warning(f"Could not load existing session: {e}")
                    logger.info("Will create new session instead")

            # Create new session if loading failed or no saved session
            if not session_data:
                logger.debug("Calling API: init_session()")
                session_data = self.api_client.init_session()
                self.session_id = session_data["sessionId"]
                logger.info(f"✓ New session created: {self.session_id}")
                logger.debug(
                    f"  Session data: currentTick={session_data.get('currentTick', 0)}"
                )

                # Save the new session ID for future use
                try:
                    import os

                    os.makedirs(os.path.dirname(session_file), exist_ok=True)
                    with open(session_file, "w") as f:
                        f.write(self.session_id)
                    logger.debug(f"Saved session ID to {session_file}")
                except Exception as e:
                    logger.warning(f"Could not save session ID: {e}")

            # Create player from server data
            player_data = session_data["player"]
            logger.debug(
                f"Creating player from server data: energy={player_data.get('energy')}, direction={player_data.get('direction')}"
            )
            self.player = Player(self.tickCounter.getTick())
            self._updatePlayerFromServerData(player_data)
            logger.info("Player initialized from server state")

            # Initialize screens that need player
            logger.debug("Initializing inventory screen")
            self.inventoryScreen = InventoryScreen(
                self.graphik,
                self.config,
                self.status,
                self.player.getInventory(),
                self.api_client,
                self.session_id,
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
            logger.warning(
                "Returning to main menu due to session initialization failure"
            )
            self.nextScreen = ScreenType.MAIN_MENU_SCREEN
            self.changeScreen = True

    def _updatePlayerFromServerData(self, player_data):
        """Update local player object from server data."""
        if player_data:
            # Update energy
            energy = player_data.get("energy", 100.0)
            logger.debug(f"Updating player energy: {energy}")
            self.player.setEnergy(energy)

            # Update direction
            direction = player_data.get("direction", -1)
            if direction >= 0:
                logger.debug(f"Updating player direction: {direction}")
                self.player.setDirection(direction)

            # Log position (position is tracked server-side, not on local player object)
            room_x = player_data.get("roomX", 0)
            room_y = player_data.get("roomY", 0)
            tile_x = player_data.get("tileX", 0)
            tile_y = player_data.get("tileY", 0)
            logger.debug(
                f"Player position from server: Room({room_x}, {room_y}), Tile({tile_x}, {tile_y})"
            )

            # Update inventory
            inventory_data = player_data.get("inventory", {})
            if inventory_data:
                logger.debug(
                    f"Updating player inventory: {inventory_data.get('numItems', 0)} items"
                )
                # Clear current inventory
                self.player.getInventory().clear()

                # Restore items from server
                slots = inventory_data.get("slots", [])
                for slot in slots:
                    if not slot.get("empty", True):
                        item_name = slot.get("itemName")
                        num_items = slot.get("numItems", 1)
                        # Create item objects and add to inventory
                        for _ in range(num_items):
                            item = self._createItemFromName(item_name)
                            if item:
                                self.player.getInventory().placeIntoFirstAvailableInventorySlot(
                                    item
                                )
                            else:
                                logger.warning(f"Unknown item type: {item_name}")

                # Set selected slot index
                selected_index = inventory_data.get("selectedInventorySlotIndex", 0)
                self.player.getInventory().setSelectedInventorySlotIndex(selected_index)

    def _createItemFromName(self, item_name):
        """Create an item object from its name string."""
        # Map item names to their classes
        item_classes = {
            "Apple": Apple,
            "Banana": Banana,
            "Stone": Stone,
            "CoalOre": CoalOre,
            "IronOre": IronOre,
            "OakWood": OakWood,
            "JungleWood": JungleWood,
            "Grass": Grass,
            "Leaves": Leaves,
        }

        item_class = item_classes.get(item_name)
        if item_class:
            return item_class()
        return None

    def _extract_username_from_token(self):
        """Extract username from JWT access token."""
        try:
            if not self.api_client.access_token:
                return None

            # JWT tokens are in format: header.payload.signature
            # Payload is base64 encoded JSON
            import base64
            import json

            parts = self.api_client.access_token.split(".")
            if len(parts) != 3:
                return None

            # Decode payload (add padding if needed)
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            decoded = base64.b64decode(payload)
            data = json.loads(decoded)

            # JWT subject contains the username
            return data.get("sub")
        except Exception as e:
            logger.warning(f"Could not extract username from token: {e}")
            return None

    def _saveCurrentSession(self):
        """Save the current session to the database."""
        if self.session_id and self.api_client.is_authenticated():
            try:
                logger.info(f"Saving session: {self.session_id}")
                self.api_client.save_session(self.session_id)
                logger.info("Session saved successfully")
            except Exception as e:
                logger.error(f"Error saving session: {e}")

    def quitApplication(self):
        logger.info("Quitting application")
        pygame.quit()
        quit()

    def run(self):
        logger.info("Starting main game loop")
        while True:
            result = self.currentScreen.run()
            logger.debug(f"Screen returned: {result}")

            if result == ScreenType.LOGIN_SCREEN:
                logger.debug("Switching to login screen")
                # Save session before logging out
                self._saveCurrentSession()
                self.currentScreen = self.loginScreen
            elif result == ScreenType.MAIN_MENU_SCREEN:
                logger.info("Main menu requested - saving session")
                # Save session before returning to main menu
                self._saveCurrentSession()
                return "restart"
            elif result == ScreenType.WORLD_SCREEN:
                # Initialize world screen if needed and authenticated
                if not self.api_client.is_authenticated():
                    logger.warning("Cannot access world screen - not authenticated")
                    self.status.set("Please login first")
                    self.currentScreen = self.loginScreen
                    continue

                if self.worldScreen is None:
                    logger.debug("Initializing world screen")
                    self.status.set("Initializing...")
                    self.initializeWorldScreen()
                    if self.worldScreen is None:
                        # Initialization failed, return to login
                        self.currentScreen = self.loginScreen
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
                # Save session before quitting to persist game state
                logger.info("Quit requested - saving session")
                self._saveCurrentSession()
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
    if parsed.scheme not in ["http", "https"]:
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
    # Save session before restarting to persist game state
    logger.info("Restart requested - saving previous session")
    try:
        if getattr(roam, "session_id", None):
            logger.debug(f"Saving session before restart: {roam.session_id}")
            roam.api_client.save_session()
            logger.info("Previous session saved")
            print("Session saved")
    except Exception as e:
        logger.error(f"Error saving session during restart: {e}")
        print(f"Error saving session: {e}")
    logger.info("Creating new Roam instance for restart")
    roam = Roam(config, server_url)

logger.info("Application exiting normally")
