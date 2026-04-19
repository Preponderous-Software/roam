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
from player.player import Player
from world.map import Map
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.tickCounter import TickCounter


def createContainer(config):
    """Configure the shared DI container with instance and factory registrations."""
    container.registerInstance(Container, container)
    container.registerInstance(Config, config)

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
        ),
        lifetime="transient",
    )

    return container
