import json
import os
import sys

import pygame
from appPaths import prepareWorkingDirectory
from bootstrap import createContainer
from config.config import Config
from config.keyBindings import KeyBindings
from inventory.inventory import Inventory
from gameLogging.logger import getLogger
from player.player import Player
from lib.graphik.src.graphik import Graphik
from screen.configScreen import ConfigScreen
from screen.controlsScreen import ControlsScreen
from screen.codexScreen import CodexScreen
from screen.inventoryScreen import InventoryScreen
from screen.mainMenuScreen import MainMenuScreen
from screen.optionsScreen import OptionsScreen
from screen.saveSelectionScreen import SaveSelectionScreen
from screen.screenType import ScreenType
from screen.statsScreen import StatsScreen
from stats.stats import Stats
from ui.status import Status
from screen.worldScreen import WorldScreen
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Roam:
    def __init__(self, config: Config):
        pygame.init()
        pygame.display.set_icon(pygame.image.load("assets/images/player_down.png"))
        self.config = config
        self.gameDisplay = self.initializeGameDisplay()
        self._initializeDependencies()
        _logger.info("game initialized", savePath=config.pathToSaveDirectory)

    def restart(self):
        """Reset all state for a new game session.

        Re-initializes the pygame display with the current config dimensions
        and clears cached singleton instances so all services are freshly
        constructed via the DI container.
        """
        self.gameDisplay = self.initializeGameDisplay()
        self._initializeDependencies()

    def _initializeDependencies(self):
        """Wire up the DI container and resolve all services and screens."""
        self.running = True
        pygame.display.set_caption(
            "Roam" + " (" + self.config.pathToSaveDirectory + ")"
        )

        # Create the DI container and register runtime dependencies.
        self.container = createContainer(self.config)
        self.tickCounter = self.container.resolve(TickCounter)
        self.container.registerInstance(Graphik, Graphik(self.gameDisplay))
        self.graphik = self.container.resolve(Graphik)
        self.status = self.container.resolve(Status)
        self.stats = self.container.resolve(Stats)
        self.player = self.container.resolve(Player)

        # Register KeyBindings: load overrides from config.yml.
        keyBindings = KeyBindings()
        keyBindings.loadFromConfig(Config.readConfigFile())
        self.container.registerInstance(KeyBindings, keyBindings)

        # Register the player inventory so InventoryScreen can auto-wire.
        self.container.registerInstance(Inventory, self.player.getInventory())

        # Resolve screens that can be fully auto-wired.
        self.worldScreen = self.container.resolve(WorldScreen)
        self.optionsScreen = self.container.resolve(OptionsScreen)
        self.mainMenuScreen = self.container.resolve(MainMenuScreen)
        self.statsScreen = self.container.resolve(StatsScreen)
        self.inventoryScreen = self.container.resolve(InventoryScreen)
        self.configScreen = self.container.resolve(ConfigScreen)
        self.controlsScreen = self.container.resolve(ControlsScreen)
        self.codexScreen = self.container.resolve(CodexScreen)

        # SaveSelectionScreen needs a callback that cannot be auto-wired.
        self.container.register(
            SaveSelectionScreen,
            lambda: SaveSelectionScreen(
                self.container.resolve(Graphik),
                self.container.resolve(Config),
                self.initializeWorldScreen,
            ),
        )
        self.saveSelectionScreen = self.container.resolve(SaveSelectionScreen)
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
        w, h = self.gameDisplay.get_size()
        self.config.saveWindowSize(w, h)
        pygame.quit()
        quit()

    def run(self):
        while True:
            result = self.currentScreen.run()
            if result == ScreenType.MAIN_MENU_SCREEN:
                # Preserve current window dimensions so the restart
                # does not shrink a maximized/resized window.
                w, h = self.gameDisplay.get_size()
                self.config.displayWidth = w
                self.config.displayHeight = h
                self.config.saveWindowSize(w, h)
                _logger.info("returning to main menu")
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
            elif result == ScreenType.CONTROLS_SCREEN:
                self.currentScreen = self.controlsScreen
            elif result == ScreenType.CODEX_SCREEN:
                if self.currentScreen == self.optionsScreen:
                    self.codexScreen.setReturnScreen(ScreenType.OPTIONS_SCREEN)
                else:
                    self.codexScreen.setReturnScreen(ScreenType.WORLD_SCREEN)
                self.currentScreen = self.codexScreen
            elif result == ScreenType.SAVE_SELECTION_SCREEN:
                self.currentScreen = self.saveSelectionScreen
            elif result == ScreenType.NONE:
                _logger.info("shutting down")
                self.quitApplication()
                return
            else:
                _logger.error("unrecognized screen", screen=result)
                self.quitApplication()
                return
            _logger.info("screen transition", screen=str(result))


def runSelfTest():
    # Verify a frozen build can locate its bundled data (assets, schemas,
    # config). CI runs the packaged executable with --selftest to confirm the
    # bundle is complete without launching the interactive game loop.
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    try:
        pygame.init()
        pygame.image.load("assets/images/player_down.png")
        with open("schemas/tick.json") as f:
            json.load(f)
        Config()  # reads config.yml
        _logger.info("selftest passed")
        print("Roam selftest: OK")
        return 0
    except Exception as exc:
        _logger.error("selftest failed", error=str(exc))
        print("Roam selftest: FAILED -", exc)
        return 1


# Frozen executables start in an arbitrary working directory; make relative
# asset/schema paths resolve against the bundle. No-op when run from source.
prepareWorkingDirectory()

if "--selftest" in sys.argv:
    sys.exit(runSelfTest())

pygame.init()
config = Config()
roam = Roam(config)
while True:
    result = roam.run()
    if result != "restart":
        break
    roam.restart()
