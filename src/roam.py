import pygame
from api.api_server import RoamAPIServer
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
from screen.worldScreen import WorldScreen
from world.tickCounter import TickCounter


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Roam:
    def __init__(self, config: Config):
        pygame.init()
        pygame.display.set_icon(pygame.image.load("assets/images/player_down.png"))
        self.running = True
        self.config = config
        pygame.display.set_caption("Roam" + " (" + config.pathToSaveDirectory + ")")
        self.tickCounter = TickCounter(self.config)
        self.gameDisplay = self.initializeGameDisplay()
        self.graphik = Graphik(self.gameDisplay)
        self.status = Status(self.graphik, self.tickCounter)
        self.stats = Stats(self.config)
        self.player = Player(self.tickCounter.getTick())
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
        
        # Initialize API server but don't start it yet
        self.apiServer = None

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
        
        # Start API server when world screen is initialized
        if self.apiServer is None:
            self.apiServer = RoamAPIServer(self.worldScreen, self.player)
            if self.apiServer.start():
                print("REST API server started successfully")
            else:
                print("Failed to start REST API server")

    def quitApplication(self):
        # Stop API server if running
        if self.apiServer and self.apiServer.is_running():
            self.apiServer.stop()
        pygame.quit()
        quit()

    def run(self):
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
roam = Roam(config)
while True:
    result = roam.run()
    if result != "restart":
        break
    roam = Roam(config)
