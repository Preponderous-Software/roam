import sys
import pygame
from config.config import Config
from player.player import Player
from lib.graphik.src.graphik import Graphik
from screen.configScreen import ConfigScreen
from screen.inventoryScreen import InventoryScreen
from screen.mainMenuScreen import MainMenuScreen
from screen.optionsScreen import OptionsScreen
from screen.screenType import ScreenType
from screen.statsScreen import StatsScreen
from screen.textWorldScreen import TextWorldScreen
from stats.stats import Stats
from ui.status import Status
from screen.worldScreen import WorldScreen
from world.tickCounter import TickCounter


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Roam:
    def __init__(self, config: Config):
        self.config = config
        self.running = True
        self.tickCounter = TickCounter(self.config)
        self.stats = Stats(self.config)
        self.player = Player(self.tickCounter.getTick())
        
        # Initialize UI based on mode
        if self.config.uiMode == "text":
            # Text mode - don't initialize pygame
            self.gameDisplay = None
            self.graphik = None
            self.status = None
            self.worldScreen = TextWorldScreen(
                self.config,
                self.tickCounter,
                self.stats,
                self.player,
            )
            self.currentScreen = self.worldScreen
        else:
            # Pygame mode - initialize pygame and all screens
            pygame.init()
            pygame.display.set_icon(pygame.image.load("assets/images/player_down.png"))
            pygame.display.set_caption("Roam" + " (" + config.pathToSaveDirectory + ")")
            self.gameDisplay = self.initializeGameDisplay()
            self.graphik = Graphik(self.gameDisplay)
            self.status = Status(self.graphik, self.tickCounter)
            self.worldScreen = WorldScreen(
                self.graphik,
                self.config,
                self.status,
                self.tickCounter,
                self.stats,
                self.player,
            )
            self.optionsScreen = OptionsScreen(self.graphik, self.config, self.status)
            self.mainMenuScreen = MainMenuScreen(
                self.graphik, self.config, self.initializeWorldScreen
            )
            self.statsScreen = StatsScreen(
                self.graphik, self.config, self.status, self.stats
            )
            self.inventoryScreen = InventoryScreen(
                self.graphik, self.config, self.status, self.player.getInventory()
            )
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
        self.worldScreen.initialize()

    def quitApplication(self):
        pygame.quit()
        quit()

    def run(self):
        # Text mode - directly run world screen
        if self.config.uiMode == "text":
            self.worldScreen.initialize()
            return self.worldScreen.run()
        
        # Pygame mode - use screen management
        while True:
            result = self.currentScreen.run()
            if result == ScreenType.MAIN_MENU_SCREEN:
                return "restart"
            if result == ScreenType.WORLD_SCREEN:
                self.currentScreen = self.worldScreen
            elif result == ScreenType.OPTIONS_SCREEN:
                self.currentScreen = self.optionsScreen
            elif result == ScreenType.STATS_SCREEN:
                self.currentScreen = self.statsScreen
            elif result == ScreenType.INVENTORY_SCREEN:
                self.currentScreen = self.inventoryScreen
                self.inventoryScreen.setInventory(self.player.getInventory())
            elif result == ScreenType.CONFIG_SCREEN:
                self.currentScreen = self.configScreen
            elif result == ScreenType.NONE:
                self.quitApplication()
            else:
                print("unrecognized screen: " + result)
                self.quitApplication()


pygame.init()
config = Config()

# Parse command-line arguments for UI mode
if len(sys.argv) > 1:
    if sys.argv[1] == "--text" or sys.argv[1] == "-t":
        config.uiMode = "text"
        print("Starting Roam in text mode...")
    elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print("Roam - A procedurally-generated 2D exploration game")
        print()
        print("Usage: python src/roam.py [OPTIONS]")
        print()
        print("Options:")
        print("  --text, -t    Use text-based UI instead of pygame")
        print("  --help, -h    Show this help message")
        print()
        sys.exit(0)

roam = Roam(config)
while True:
    result = roam.run()
    if result != "restart":
        break
    roam = Roam(config)
