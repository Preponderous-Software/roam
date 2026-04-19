"""Centralized dependency registration for the Roam application.

All dependency wiring is defined here so that the rest of the application
resolves its services through the DI container instead of constructing them
manually.
"""

from di import Container

from config.config import Config
from lib.graphik.src.graphik import Graphik
from mapimage.mapImageUpdater import MapImageUpdater
from player.player import Player
from screen.configScreen import ConfigScreen
from screen.inventoryScreen import InventoryScreen
from screen.mainMenuScreen import MainMenuScreen
from screen.optionsScreen import OptionsScreen
from screen.statsScreen import StatsScreen
from screen.worldScreen import WorldScreen
from stats.stats import Stats
from ui.energyBar import EnergyBar
from ui.hudDragManager import HudDragManager
from ui.status import Status
from world.map import Map
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.tickCounter import TickCounter


def createContainer(config):
    """Create and configure the DI container with all application dependencies."""
    container = Container()
    container.registerInstance(Container, container)
    container.registerInstance(Config, config)

    # Core services — auto-wired via type hints on their constructors.
    container.register(TickCounter, TickCounter)
    container.register(Stats, Stats)
    container.register(Status, Status)
    container.register(MapImageUpdater, MapImageUpdater)

    # UI components
    container.register(EnergyBar, EnergyBar)
    container.register(HudDragManager, HudDragManager)

    # Player requires a tick value from TickCounter, so use a factory.
    container.register(
        Player, lambda: Player(container.resolve(TickCounter).getTick())
    )

    # Services that need the gridSize primitive from Config.
    container.register(
        RoomJsonReaderWriter,
        lambda: RoomJsonReaderWriter(
            container.resolve(Config).gridSize,
            container.resolve(Graphik),
            container.resolve(TickCounter),
            container.resolve(Config),
        ),
        lifetime="transient",
    )
    container.register(
        RoomFactory,
        lambda: RoomFactory(
            container.resolve(Config).gridSize,
            container.resolve(Graphik),
            container.resolve(TickCounter),
        ),
        lifetime="transient",
    )
    container.register(
        Map,
        lambda: Map(
            container.resolve(Config).gridSize,
            container.resolve(Graphik),
            container.resolve(TickCounter),
            container.resolve(Config),
            container,
        ),
        lifetime="transient",
    )

    # Screens — auto-wired via type hints.
    container.register(WorldScreen, WorldScreen)
    container.register(OptionsScreen, OptionsScreen)
    container.register(MainMenuScreen, MainMenuScreen)
    container.register(StatsScreen, StatsScreen)
    container.register(ConfigScreen, ConfigScreen)
    container.register(InventoryScreen, InventoryScreen)

    return container
