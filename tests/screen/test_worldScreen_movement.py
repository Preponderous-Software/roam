import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

import pytest

from config.config import Config
from entity.apple import Apple
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.oakWood import OakWood
from entity.stone import Stone
from player.player import Player
from screen.worldScreen import WorldScreen
from stats.stats import Stats
from ui.geometry import Rect
from world.map import Map
from world.room import Room
from world.tickCounter import TickCounter

# Characterization tests for the WorldScreen's player movement and room
# transitions: the direction-to-neighbour lookup, corner detection, which
# room a step off the grid leads to, where the player lands in it, loading or
# generating that room, the world border, and the per-step rules in
# movePlayer (crouching, solid tiles, pushable stone, bears, eating). They
# assert current behaviour only.

GRID = 5
MAX = GRID - 1
CENTRE = 2

UP = 0
LEFT = 1
DOWN = 2
RIGHT = 3

# A room away from the origin, so a coordinate change cannot be confused with
# a default of zero.
ROOM_X = 10
ROOM_Y = 20


class _FakeRoomFactory:
    """Stands in for RoomFactory: Map.generateNewRoom calls one of these
    depending on a random roll, and every one returns a fresh empty room."""

    def __init__(self):
        self.lastRoomTypeCreated = None
        self.created = []

    def _make(self, x, y, z):
        self.created.append((x, y, z))
        return _room(x, y, z)

    def createRoom(self, roomType, x, y, z):
        return self._make(x, y, z)

    def createRandomRoom(self, x, y, z):
        return self._make(x, y, z)

    def createCaveRoom(self, x, y, z):
        return self._make(x, y, z)


def _room(x=ROOM_X, y=ROOM_Y, z=0):
    return Room("test", GRID, (0, 0, 0), x, y, MagicMock(), z)


def _worldScreen(tmp_path, playerAt=(CENTRE, CENTRE), roomX=ROOM_X, roomY=ROOM_Y):
    config = Config()
    config.gridSize = GRID
    config.worldBorder = 0
    config.pathToSaveDirectory = str(tmp_path)
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.status = MagicMock()
    ws.stats = Stats(config)
    ws.tickCounter = TickCounter(config)
    ws.currentZ = 0
    ws.map = Map(GRID, MagicMock(), ws.tickCounter, config, _FakeRoomFactory())
    ws.currentRoom = ws.map.addRoom(_room(roomX, roomY))
    ws.player = Player(0)
    ws.currentRoom.addEntityToLocation(ws.player, _at(ws.currentRoom, *playerAt))
    ws.renderer = MagicMock()
    ws.renderer.getGameAreaRect.return_value = Rect(0, 0, 500, 500)
    ws.roomPreloader = MagicMock()
    ws.discoverEntitiesInRoom = MagicMock()
    ws.save = MagicMock()
    return ws


def _at(room, x, y):
    return room.getGrid().getLocationByCoordinates(x, y)


def _isInRoom(room, entity):
    # Room.isEntityPresent cannot be used: the vendored Grid.isEntityPresent
    # reads a missing self.grid attribute and raises AttributeError.
    grid = room.getGrid()
    return any(
        grid.getLocation(locationId).isEntityPresent(entity)
        for locationId in grid.getLocations()
    )


def _playerXY(ws):
    location = ws.getLocationOfPlayer()
    return (location.getX(), location.getY())


# --- getLocationDirection ----------------------------------------------------


@pytest.mark.parametrize(
    "direction, expected",
    [(UP, (2, 1)), (LEFT, (1, 2)), (DOWN, (2, 3)), (RIGHT, (3, 2))],
)
def test_location_direction_returns_the_neighbour(tmp_path, direction, expected):
    ws = _worldScreen(tmp_path)
    grid = ws.currentRoom.getGrid()

    neighbour = ws.getLocationDirection(direction, grid, _at(ws.currentRoom, 2, 2))

    assert (neighbour.getX(), neighbour.getY()) == expected


def test_location_direction_is_minus_one_off_the_grid(tmp_path):
    ws = _worldScreen(tmp_path)
    grid = ws.currentRoom.getGrid()

    assert ws.getLocationDirection(UP, grid, _at(ws.currentRoom, 2, 0)) == -1
    assert ws.getLocationDirection(RIGHT, grid, _at(ws.currentRoom, MAX, 2)) == -1


def test_location_direction_is_minus_one_when_standing_still(tmp_path):
    ws = _worldScreen(tmp_path)
    grid = ws.currentRoom.getGrid()

    assert ws.getLocationDirection(-1, grid, _at(ws.currentRoom, 2, 2)) == -1


def test_location_direction_is_none_for_an_unknown_direction(tmp_path):
    ws = _worldScreen(tmp_path)
    grid = ws.currentRoom.getGrid()

    assert ws.getLocationDirection(7, grid, _at(ws.currentRoom, 2, 2)) is None


# --- isCorner ----------------------------------------------------------------


@pytest.mark.parametrize("x, y", [(0, 0), (MAX, 0), (0, MAX), (MAX, MAX)])
def test_each_grid_corner_is_a_corner(tmp_path, x, y):
    ws = _worldScreen(tmp_path)

    assert ws.isCorner(_at(ws.currentRoom, x, y)) is True


@pytest.mark.parametrize("x, y", [(0, 2), (MAX, 2), (2, 0), (2, MAX), (2, 2)])
def test_edges_and_the_centre_are_not_corners(tmp_path, x, y):
    ws = _worldScreen(tmp_path)

    assert ws.isCorner(_at(ws.currentRoom, x, y)) is False


# --- getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection ---------------


@pytest.mark.parametrize(
    "playerAt, expected",
    [
        ((MAX, 2), (ROOM_X + 1, ROOM_Y)),
        ((0, 2), (ROOM_X - 1, ROOM_Y)),
        ((2, MAX), (ROOM_X, ROOM_Y + 1)),
        ((2, 0), (ROOM_X, ROOM_Y - 1)),
    ],
)
def test_an_edge_leads_to_the_room_on_that_side(tmp_path, playerAt, expected):
    ws = _worldScreen(tmp_path, playerAt=playerAt)

    assert ws.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection() == expected


def test_an_edge_ignores_the_facing_direction(tmp_path):
    # Away from a corner only the position counts, so facing into the room
    # on the left edge still leads to the room on the left.
    ws = _worldScreen(tmp_path, playerAt=(0, 2))
    ws.player.setDirection(RIGHT)

    assert ws.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection() == (
        ROOM_X - 1,
        ROOM_Y,
    )


@pytest.mark.parametrize(
    "corner, direction, expected",
    [
        ((0, 0), UP, (ROOM_X, ROOM_Y - 1)),
        ((0, 0), LEFT, (ROOM_X - 1, ROOM_Y)),
        ((MAX, 0), UP, (ROOM_X, ROOM_Y - 1)),
        ((MAX, 0), RIGHT, (ROOM_X + 1, ROOM_Y)),
        ((0, MAX), DOWN, (ROOM_X, ROOM_Y + 1)),
        ((0, MAX), LEFT, (ROOM_X - 1, ROOM_Y)),
        ((MAX, MAX), DOWN, (ROOM_X, ROOM_Y + 1)),
        ((MAX, MAX), RIGHT, (ROOM_X + 1, ROOM_Y)),
    ],
)
def test_a_corner_follows_the_facing_direction(tmp_path, corner, direction, expected):
    ws = _worldScreen(tmp_path, playerAt=corner)
    ws.player.setDirection(direction)

    assert ws.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection() == expected


def test_a_corner_facing_inward_stays_in_the_same_room(tmp_path):
    ws = _worldScreen(tmp_path, playerAt=(0, 0))
    ws.player.setDirection(DOWN)

    assert ws.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection() == (
        ROOM_X,
        ROOM_Y,
    )


def test_the_centre_stays_in_the_same_room(tmp_path):
    ws = _worldScreen(tmp_path)

    assert ws.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection() == (
        ROOM_X,
        ROOM_Y,
    )


# --- getCoordinatesForNewRoomBasedOnLivingEntityLocation ---------------------


@pytest.mark.parametrize(
    "entityAt, expected",
    [
        ((2, MAX), (ROOM_X, ROOM_Y + 1)),
        ((2, 0), (ROOM_X, ROOM_Y - 1)),
        ((2, 2), (ROOM_X, ROOM_Y)),
    ],
)
def test_living_entity_vertical_edges_and_centre(tmp_path, entityAt, expected):
    ws = _worldScreen(tmp_path)
    chicken = Chicken(0)
    ws.currentRoom.addEntityToLocation(chicken, _at(ws.currentRoom, *entityAt))

    assert ws.getCoordinatesForNewRoomBasedOnLivingEntityLocation(chicken) == expected


# --- _calculateTargetLocationForRoomTransition -------------------------------


@pytest.mark.parametrize(
    "playerAt, expected",
    [
        ((0, 2), (MAX, 2)),
        ((MAX, 2), (0, 2)),
        ((2, 0), (2, MAX)),
        ((2, MAX), (2, 0)),
    ],
)
def test_an_edge_lands_on_the_opposite_edge(tmp_path, playerAt, expected):
    ws = _worldScreen(tmp_path, playerAt=playerAt)

    target = ws._calculateTargetLocationForRoomTransition(ws.getLocationOfPlayer())

    assert (target.getX(), target.getY()) == expected


@pytest.mark.parametrize(
    "corner, direction, expected",
    [
        ((0, 0), UP, (0, MAX)),
        ((0, 0), LEFT, (MAX, 0)),
        ((MAX, 0), UP, (MAX, MAX)),
        ((MAX, 0), RIGHT, (0, 0)),
        ((0, MAX), DOWN, (0, 0)),
        ((0, MAX), LEFT, (MAX, MAX)),
        ((MAX, MAX), DOWN, (MAX, 0)),
        ((MAX, MAX), RIGHT, (0, MAX)),
    ],
)
def test_a_corner_lands_across_the_facing_direction_only(
    tmp_path, corner, direction, expected
):
    ws = _worldScreen(tmp_path, playerAt=corner)
    ws.player.setDirection(direction)

    target = ws._calculateTargetLocationForRoomTransition(ws.getLocationOfPlayer())

    assert (target.getX(), target.getY()) == expected


# --- _loadOrGenerateRoom -----------------------------------------------------


def test_a_generated_room_counts_as_a_discovery(tmp_path):
    ws = _worldScreen(tmp_path)

    room = ws._loadOrGenerateRoom(ROOM_X + 1, ROOM_Y)

    assert (room.getX(), room.getY(), room.getZ()) == (ROOM_X + 1, ROOM_Y, 0)
    ws.status.set.assert_called_once_with("New area discovered")
    assert ws.stats.getScore() == 1
    assert ws.stats.getRoomsExplored() == 1


def test_a_room_already_in_memory_changes_nothing(tmp_path):
    ws = _worldScreen(tmp_path)

    room = ws._loadOrGenerateRoom(ROOM_X, ROOM_Y)

    assert room is ws.currentRoom
    ws.status.set.assert_not_called()
    assert ws.stats.getScore() == 0
    assert ws.stats.getRoomsExplored() == 0


def test_a_generated_room_counts_only_once(tmp_path):
    ws = _worldScreen(tmp_path)
    ws._loadOrGenerateRoom(ROOM_X + 1, ROOM_Y)

    ws._loadOrGenerateRoom(ROOM_X + 1, ROOM_Y)

    assert ws.stats.getRoomsExplored() == 1


def test_a_room_read_from_disk_reports_area_loaded(tmp_path):
    ws = _worldScreen(tmp_path)
    loaded = _room(ROOM_X + 1, ROOM_Y)
    ws.map = MagicMock()
    ws.map.hasRoom.return_value = False
    ws.map.getRoom.return_value = loaded
    ws.map.consumeIsNewRoom.return_value = False

    room = ws._loadOrGenerateRoom(ROOM_X + 1, ROOM_Y)

    assert room is loaded
    ws.map.generateNewRoom.assert_not_called()
    ws.status.set.assert_called_once_with("Area loaded")
    assert ws.stats.getRoomsExplored() == 0


def test_load_without_stats_reports_nothing(tmp_path):
    ws = _worldScreen(tmp_path)

    ws._loadOrGenerateRoom(ROOM_X + 1, ROOM_Y, updateStats=False)

    ws.status.set.assert_not_called()
    assert ws.stats.getRoomsExplored() == 0


def test_load_defaults_to_the_current_level(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.currentZ = -2

    room = ws._loadOrGenerateRoom(ROOM_X, ROOM_Y)

    assert room.getZ() == -2
    assert ws.map.roomFactory.created == [(ROOM_X, ROOM_Y, -2)]


# --- changeRooms -------------------------------------------------------------


def test_change_rooms_moves_the_player_into_the_next_room(tmp_path):
    ws = _worldScreen(tmp_path, playerAt=(MAX, 2))
    oldRoom = ws.currentRoom

    ws.changeRooms()

    assert (ws.currentRoom.getX(), ws.currentRoom.getY()) == (ROOM_X + 1, ROOM_Y)
    assert not _isInRoom(oldRoom, ws.player)
    assert _isInRoom(ws.currentRoom, ws.player)
    assert _playerXY(ws) == (0, 2)
    ws.status.set.assert_called_once_with("New area discovered")
    ws.roomPreloader.preloadNearbyRooms.assert_called_once_with(
        ROOM_X + 1, ROOM_Y, ws.map, 0
    )
    ws.discoverEntitiesInRoom.assert_called_once_with()


def test_change_rooms_sizes_tiles_from_the_game_area(tmp_path):
    ws = _worldScreen(tmp_path, playerAt=(MAX, 2))

    ws.changeRooms()

    assert ws.locationWidth == 500 / GRID
    assert ws.locationHeight == 500 / GRID


def test_change_rooms_reuses_a_room_already_visited(tmp_path):
    ws = _worldScreen(tmp_path, playerAt=(0, 2))
    left = ws.map.addRoom(_room(ROOM_X - 1, ROOM_Y))

    ws.changeRooms()

    assert ws.currentRoom is left
    assert ws.map.roomFactory.created == []
    ws.status.set.assert_not_called()


def test_change_rooms_stops_at_the_world_border(tmp_path):
    ws = _worldScreen(tmp_path, playerAt=(MAX, 2), roomX=1, roomY=0)
    ws.config.worldBorder = 1
    oldRoom = ws.currentRoom

    ws.changeRooms()

    assert ws.currentRoom is oldRoom
    assert _playerXY(ws) == (MAX, 2)
    ws.status.set.assert_called_once_with("Reached world border")
    ws.roomPreloader.preloadNearbyRooms.assert_not_called()
    assert ws.map.roomFactory.created == []


def test_change_rooms_allows_the_room_on_the_border(tmp_path):
    ws = _worldScreen(tmp_path, playerAt=(MAX, 2), roomX=0, roomY=0)
    ws.config.worldBorder = 1

    ws.changeRooms()

    assert (ws.currentRoom.getX(), ws.currentRoom.getY()) == (1, 0)


def test_change_rooms_checks_the_border_on_both_axes(tmp_path):
    ws = _worldScreen(tmp_path, playerAt=(2, 0), roomX=0, roomY=-1)
    ws.config.worldBorder = 1

    ws.changeRooms()

    assert (ws.currentRoom.getX(), ws.currentRoom.getY()) == (0, -1)
    ws.status.set.assert_called_once_with("Reached world border")


# --- movePlayer --------------------------------------------------------------


def test_move_steps_onto_an_empty_tile_and_costs_energy(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.config.playerMovementEnergyCost = 2
    for _ in range(7):
        ws.tickCounter.incrementTick()

    ws.movePlayer(RIGHT)

    assert _playerXY(ws) == (3, 2)
    assert ws.player.getEnergy() == 98
    assert ws.player.getTickLastMoved() == 7


def test_a_crouching_player_does_not_move(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.player.setCrouching(True)

    ws.movePlayer(RIGHT)

    assert _playerXY(ws) == (2, 2)
    assert ws.player.getEnergy() == 100
    assert ws.player.getTickLastMoved() == -1


def test_a_solid_tile_blocks_the_step(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.currentRoom.addEntityToLocation(OakWood(), _at(ws.currentRoom, 3, 2))

    ws.movePlayer(RIGHT)

    assert _playerXY(ws) == (2, 2)
    assert ws.player.getEnergy() == 100


def test_a_pushable_stone_is_pushed_and_the_player_follows(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.config.pushableStone = True
    stone = Stone()
    ws.currentRoom.addEntityToLocation(stone, _at(ws.currentRoom, 3, 2))

    ws.movePlayer(RIGHT)

    assert _playerXY(ws) == (3, 2)
    assert _at(ws.currentRoom, 4, 2).isEntityPresent(stone)


def test_a_stone_against_a_solid_tile_blocks_the_step(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.config.pushableStone = True
    stone = Stone()
    ws.currentRoom.addEntityToLocation(stone, _at(ws.currentRoom, 3, 2))
    ws.currentRoom.addEntityToLocation(OakWood(), _at(ws.currentRoom, 4, 2))

    ws.movePlayer(RIGHT)

    assert _playerXY(ws) == (2, 2)
    assert _at(ws.currentRoom, 3, 2).isEntityPresent(stone)


def test_a_stone_sharing_a_tile_with_wood_still_blocks_after_the_push(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.config.pushableStone = True
    stone = Stone()
    ws.currentRoom.addEntityToLocation(stone, _at(ws.currentRoom, 3, 2))
    ws.currentRoom.addEntityToLocation(OakWood(), _at(ws.currentRoom, 3, 2))

    ws.movePlayer(RIGHT)

    assert _at(ws.currentRoom, 4, 2).isEntityPresent(stone)
    assert _playerXY(ws) == (2, 2)


def test_stone_is_not_pushed_when_pushing_is_off(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.config.pushableStone = False
    stone = Stone()
    ws.currentRoom.addEntityToLocation(stone, _at(ws.currentRoom, 3, 2))

    ws.movePlayer(RIGHT)

    assert _playerXY(ws) == (2, 2)
    assert _at(ws.currentRoom, 3, 2).isEntityPresent(stone)


def test_stepping_onto_a_bear_kills_the_player(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.currentRoom.addEntityToLocation(Bear(0), _at(ws.currentRoom, 3, 2))

    ws.movePlayer(RIGHT)

    assert ws.player.isDead()
    assert _playerXY(ws) == (2, 2)
    ws.status.set.assert_called_once_with("Killed by Bear")


def test_a_hungry_player_eats_food_on_the_tile(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.config.playerMovementEnergyCost = 1
    ws.player.setEnergy(40)
    apple = Apple()
    apple.setEnergy(8)
    ws.currentRoom.addEntityToLocation(apple, _at(ws.currentRoom, 3, 2))

    ws.movePlayer(RIGHT)

    assert not _at(ws.currentRoom, 3, 2).isEntityPresent(apple)
    assert ws.player.getEnergy() == 40 + 8 - 1
    assert ws.stats.getFoodEaten() == 1
    assert ws.stats.getScore() == 1
    ws.status.set.assert_called_once_with("Ate Apple")
    assert _playerXY(ws) == (3, 2)


def test_a_fed_player_walks_over_food(tmp_path):
    ws = _worldScreen(tmp_path)
    ws.config.playerMovementEnergyCost = 1
    apple = Apple()
    ws.currentRoom.addEntityToLocation(apple, _at(ws.currentRoom, 3, 2))

    ws.movePlayer(RIGHT)

    assert _at(ws.currentRoom, 3, 2).isEntityPresent(apple)
    assert ws.player.getEnergy() == 99
    assert ws.stats.getFoodEaten() == 0
    ws.status.set.assert_not_called()


def test_stepping_off_the_grid_changes_rooms_and_saves(tmp_path):
    ws = _worldScreen(tmp_path, playerAt=(MAX, 2))
    ws.player.setDirection(RIGHT)

    ws.movePlayer(RIGHT)

    assert (ws.currentRoom.getX(), ws.currentRoom.getY()) == (ROOM_X + 1, ROOM_Y)
    assert _playerXY(ws) == (0, 2)
    ws.save.assert_called_once_with()
    assert ws.player.getEnergy() == 100
