"""Characterization tests for the DI wiring in ``src/bootstrap.py``.

``tests/di/test_container.py`` proves the container's generic behaviour
(lifetimes, auto-wiring, ``resetSingletons``). These tests pin down what
``createContainer`` actually registers on top of it — which types are
transient, which primitives each factory pulls out of ``Config``, and what
survives a restart — because the rest of the game (and the "Restart Safety"
section of ``.github/copilot-instructions.md``) relies on those choices.

The autouse ``test_di_container`` fixture in ``tests/conftest.py`` has already
called ``createContainer(test_config)`` and registered a ``Renderer`` by the
time each test runs, so the module-level container is in the state ``Roam``
sees right after ``_initializeDependencies()``.
"""

from unittest.mock import MagicMock

from appContainer import container
from bootstrap import createContainer
from config.config import Config
from di import Container
from gameLogging.logger import LoggerFactory
from player.player import Player
from rendering.renderer import Renderer
from world.map import Map
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.roomPreloader import RoomPreloader
from world.tickCounter import TickCounter


def _makeConfig(gridSize):
    config = MagicMock(spec=Config)
    config.gridSize = gridSize
    config.npcEnabled = False
    return config


# ---------------------------------------------------------------------------
# What createContainer hands back and registers outright
# ---------------------------------------------------------------------------


def test_create_container_returns_the_module_level_container(test_config):
    assert createContainer(test_config) is container


def test_container_is_registered_as_itself(resolve):
    assert resolve(Container) is container


def test_config_resolves_to_the_instance_passed_in(resolve, test_config):
    assert resolve(Config) is test_config


def test_logger_factory_is_a_singleton(resolve):
    first = resolve(LoggerFactory)
    assert isinstance(first, LoggerFactory)
    assert resolve(LoggerFactory) is first


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------


def test_player_is_created_with_the_tick_counter_current_tick(resolve):
    resolve(TickCounter).tick = 42
    assert resolve(Player).getTickCreated() == 42


def test_player_is_a_singleton(resolve):
    assert resolve(Player) is resolve(Player)


# ---------------------------------------------------------------------------
# Transient world services
# ---------------------------------------------------------------------------


def test_room_factory_is_transient(resolve):
    assert resolve(RoomFactory) is not resolve(RoomFactory)


def test_room_factory_is_wired_from_config_renderer_and_tick_counter(
    resolve, test_config
):
    roomFactory = resolve(RoomFactory)
    assert roomFactory.gridSize == test_config.gridSize
    assert roomFactory.renderer is resolve(Renderer)
    assert roomFactory.tickCounter is resolve(TickCounter)


def test_room_json_reader_writer_is_transient(resolve):
    assert resolve(RoomJsonReaderWriter) is not resolve(RoomJsonReaderWriter)


def test_room_json_reader_writer_is_wired_from_config_renderer_and_tick_counter(
    resolve, test_config
):
    readerWriter = resolve(RoomJsonReaderWriter)
    assert readerWriter.gridSize == test_config.gridSize
    assert readerWriter.renderer is resolve(Renderer)
    assert readerWriter.tickCounter is resolve(TickCounter)
    assert readerWriter.config is test_config


def test_map_is_transient(resolve):
    assert resolve(Map) is not resolve(Map)


def test_map_is_wired_from_config_renderer_and_tick_counter(resolve, test_config):
    gameMap = resolve(Map)
    assert gameMap.gridSize == test_config.gridSize
    assert gameMap.renderer is resolve(Renderer)
    assert gameMap.tickCounter is resolve(TickCounter)
    assert gameMap.config is test_config


def test_map_receives_a_container_built_room_factory(resolve):
    gameMap = resolve(Map)
    assert isinstance(gameMap.roomFactory, RoomFactory)
    assert gameMap.roomFactory.gridSize == gameMap.gridSize


def test_each_map_gets_its_own_room_factory(resolve):
    assert resolve(Map).roomFactory is not resolve(Map).roomFactory


def test_map_room_json_reader_writer_factory_yields_a_fresh_writer_per_call(resolve):
    factory = resolve(Map)._roomJsonReaderWriterFactory
    first = factory()
    assert isinstance(first, RoomJsonReaderWriter)
    assert factory() is not first


# ---------------------------------------------------------------------------
# RoomPreloader
# ---------------------------------------------------------------------------


def test_room_preloader_is_a_singleton(resolve):
    assert resolve(RoomPreloader) is resolve(RoomPreloader)


def test_room_preloader_is_wired_from_config_renderer_and_tick_counter(
    resolve, test_config
):
    preloader = resolve(RoomPreloader)
    assert preloader.gridSize == test_config.gridSize
    assert preloader.renderer is resolve(Renderer)
    assert preloader.tickCounter is resolve(TickCounter)
    assert preloader.config is test_config


def test_room_preloader_room_json_reader_writer_factory_yields_a_fresh_writer_per_call(
    resolve,
):
    factory = resolve(RoomPreloader)._roomJsonReaderWriterFactory
    first = factory()
    assert isinstance(first, RoomJsonReaderWriter)
    assert factory() is not first


# ---------------------------------------------------------------------------
# Restart safety — a second createContainer call is what Roam.restart() does
# ---------------------------------------------------------------------------


def test_recreating_the_container_swaps_in_the_new_config(resolve):
    newConfig = _makeConfig(gridSize=5)
    createContainer(newConfig)
    assert resolve(Config) is newConfig
    assert resolve(RoomFactory).gridSize == 5


def test_recreating_the_container_drops_component_singletons(resolve, test_config):
    # TickCounter is registered by @component at import time, so createContainer
    # never re-registers it; only its resetSingletons() call drops the cache.
    previous = resolve(TickCounter)
    createContainer(test_config)
    assert resolve(TickCounter) is not previous


def test_recreating_the_container_drops_factory_registered_singletons(
    resolve, test_config
):
    # Player and RoomPreloader are re-registered by createContainer itself, which
    # replaces the registration (and its cached instance) outright.
    previousPlayer = resolve(Player)
    previousPreloader = resolve(RoomPreloader)
    createContainer(test_config)
    assert resolve(Player) is not previousPlayer
    assert resolve(RoomPreloader) is not previousPreloader


def test_recreating_the_container_replaces_the_logger_factory(resolve, test_config):
    previous = resolve(LoggerFactory)
    createContainer(test_config)
    assert resolve(LoggerFactory) is not previous


def test_recreating_the_container_preserves_explicit_instance_registrations(
    resolve, test_config
):
    renderer = resolve(Renderer)
    createContainer(test_config)
    assert resolve(Renderer) is renderer


def test_recreated_player_reads_the_new_tick_counter(resolve, test_config):
    resolve(TickCounter).tick = 7
    assert resolve(Player).getTickCreated() == 7
    createContainer(test_config)
    resolve(TickCounter).tick = 99
    assert resolve(Player).getTickCreated() == 99
