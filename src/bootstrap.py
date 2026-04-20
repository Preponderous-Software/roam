"""Centralized dependency registration for the Roam application.

All dependency wiring is defined here so that the rest of the application
resolves its services through the DI container instead of constructing them
manually.  Classes decorated with ``@component`` are registered at import
time; this module adds factory-based and instance registrations.
"""

from appContainer import container
from di import Container

from config.config import Config
from lib.graphik.src.graphik import Graphik
from gameLogging.logger import LoggerFactory
from player.player import Player
from world.map import Map
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.roomPreloader import RoomPreloader
from world.tickCounter import TickCounter


def createContainer(config):
    """Configure the shared DI container with instance and factory registrations.

    Clears cached singletons first so that each ``Roam`` restart gets
    fresh instances rather than stale objects from the previous run.
    """
    container.resetSingletons()
    container.registerInstance(Container, container)
    container.registerInstance(Config, config)

    # Logger factory as a singleton service.
    container.registerInstance(LoggerFactory, LoggerFactory())

    # Player requires a tick value from TickCounter, so use a factory.
    container.register(Player, lambda: Player(container.resolve(TickCounter).getTick()))

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
            roomFactory=container.resolve(RoomFactory),
            roomJsonReaderWriterFactory=lambda: container.resolve(RoomJsonReaderWriter),
        ),
        lifetime="transient",
    )
    container.register(
        RoomPreloader,
        lambda: RoomPreloader(
            container.resolve(Config).gridSize,
            container.resolve(Graphik),
            container.resolve(TickCounter),
            container.resolve(Config),
            roomJsonReaderWriterFactory=lambda: container.resolve(RoomJsonReaderWriter),
        ),
    )

    return container
