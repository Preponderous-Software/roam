"""Room revision counters (RFC 0017 Open Question 3).

Every way an entity stack can change must move the room's revision, because
WorldViewBuilder reuses its cached view of a room until the revision moves. A
missed path would leave a 3D view showing stale tiles.
"""

import random
import threading
from unittest.mock import MagicMock

import pytest

from entity.grass import Grass
from entity.living.chicken import Chicken
from entity.stone import Stone
from entity.torch import Torch
from player.player import Player
from world.dayNightCycle import DayNightCycle
from world.room import Room
from world.roomFactory import RoomFactory
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.roomType import RoomType
from world.trackedLocation import TrackedLocation
from world.worldViewBuilder import WorldViewBuilder

GRID = 5


def _room(x=0, y=0):
    return Room("r", GRID, (1, 2, 3), x, y, MagicMock())


def _at(room, x, y):
    return room.getGrid().getLocationByCoordinates(x, y)


def _addViaRoom(room, entity):
    room.addEntity(entity)


def _addViaRoomToLocation(room, entity):
    room.addEntityToLocation(entity, _at(room, 1, 1))


def _addViaGrid(room, entity):
    room.getGrid().addEntity(entity)


def _addViaGridToLocation(room, entity):
    room.getGrid().addEntityToLocation(entity, _at(room, 2, 2))


def _addViaLocation(room, entity):
    _at(room, 3, 3).addEntity(entity)


ADD_PATHS = [
    _addViaRoom,
    _addViaRoomToLocation,
    _addViaGrid,
    _addViaGridToLocation,
    _addViaLocation,
]


@pytest.mark.parametrize("add", ADD_PATHS, ids=lambda f: f.__name__)
def test_every_add_path_bumps_the_revision(add):
    room = _room()
    before = room.getRevision()

    add(room, Stone())

    assert room.getRevision() != before


def test_every_remove_path_bumps_the_revision():
    room = _room()
    stones = [Stone() for _ in range(3)]
    for stone in stones:
        room.addEntityToLocation(stone, _at(room, 0, 0))

    revisions = [room.getRevision()]
    room.removeEntity(stones[0])  # Environment -> Grid -> Location
    revisions.append(room.getRevision())
    room.getGrid().removeEntity(stones[1])
    revisions.append(room.getRevision())
    _at(room, 0, 0).removeEntity(stones[2])  # direct, as worldScreen does
    revisions.append(room.getRevision())

    assert len(set(revisions)) == 4


def test_set_entities_bumps_the_revision():
    room = _room()
    before = room.getRevision()

    _at(room, 4, 4).setEntities({})

    assert room.getRevision() != before


def test_living_entity_moves_bump_the_revision(monkeypatch):
    room = _room()
    chicken = Chicken(0)
    room.addEntityToLocation(chicken, _at(room, 2, 2))
    room.addLivingEntity(chicken)
    before = room.getRevision()
    monkeypatch.setattr(random, "randrange", lambda *args: 1)  # always move

    room.moveLivingEntities(0)

    assert room.getRevision() != before


def test_set_grid_tracks_the_new_locations():
    room = _room()
    other = _room()
    before = room.getRevision()

    room.setGrid(other.getGrid())
    afterSet = room.getRevision()
    _at(room, 0, 0).addEntity(Grass())

    assert afterSet != before
    assert room.getRevision() != afterSet
    assert all(
        isinstance(location, TrackedLocation)
        for location in room.getGrid().getLocations().values()
    )


def test_a_room_loaded_from_a_save_is_tracked(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    test_config.gridSize = GRID
    room = _room()
    room.addEntityToLocation(Grass(), _at(room, 0, 0))
    writer = resolve(RoomJsonReaderWriter)
    path = test_config.getRoomFilePath(0, 0, 0)
    writer.saveRoom(room, path)

    loaded = writer.loadRoom(path)
    before = loaded.getRevision()
    _at(loaded, 1, 0).addEntity(Stone())

    assert loaded.getRevision() != before


def test_reading_does_not_bump_the_revision():
    room = _room()
    room.addEntityToLocation(Torch(), _at(room, 1, 1))
    before = room.getRevision()

    for location in room.getGrid().getLocations().values():
        location.getEntities()
        location.getNumEntities()
    room.getNumEntities()

    assert room.getRevision() == before


def test_revisions_are_never_shared_between_rooms():
    rooms = [_room(x, 0) for x in range(10)]
    for room in rooms:
        room.addEntity(Stone())

    assert len({room.getRevision() for room in rooms}) == len(rooms)


# --- a cached view is never stale ------------------------------------------


def _builder():
    config = MagicMock()
    config.dayNightCycleEnabled = True
    config.dayNightCycleLengthTicks = 1000
    config.cameraFollowPlayer = True
    return WorldViewBuilder(DayNightCycle(config), config)


def _map(rooms):
    fakeMap = MagicMock()
    fakeMap._lock = threading.Lock()
    fakeMap.getRooms.return_value = rooms
    return fakeMap


def _tilesByRoom(worldView):
    return {roomView.getKey(): roomView.getTiles() for roomView in worldView.getRooms()}


def test_cached_views_always_match_a_fresh_build():
    random.seed(11)
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = 0
    factory = RoomFactory(GRID, MagicMock(), tickCounter)
    rooms = [
        factory.createRoom(RoomType.FOREST, x, y)
        for x in (-1, 0, 1)
        for y in (-1, 0, 1)
    ]
    player = Player(0)
    home = rooms[4]
    home.addEntityToLocation(player, _at(home, 2, 2))
    cachedBuilder = _builder()
    worldMap = _map(rooms)

    for step in range(300):
        room = random.choice(rooms)
        location = _at(room, random.randrange(GRID), random.randrange(GRID))
        entities = [e for e in location.getEntities().values() if e is not player]
        action = random.randrange(4)
        if action == 0 or not entities:
            location.addEntity(Stone())
        elif action == 1:
            location.removeEntity(random.choice(entities))
        elif action == 2:
            room.removeEntity(random.choice(entities))
        else:
            room.addEntity(Torch())
        cached = cachedBuilder.build(worldMap, player, step)
        fresh = _builder().build(worldMap, player, step)

        assert _tilesByRoom(cached) == _tilesByRoom(fresh), "step " + str(step)
        assert [
            (l.getRoom(), l.getTileX(), l.getTileY()) for l in cached.getLights()
        ] == [(l.getRoom(), l.getTileX(), l.getTileY()) for l in fresh.getLights()]


def test_unchanged_rooms_reuse_their_cached_view_and_changed_ones_do_not():
    rooms = [_room(x, 0) for x in range(3)]
    player = Player(0)
    rooms[0].addEntityToLocation(player, _at(rooms[0], 0, 0))
    builder = _builder()
    first = builder.build(_map(rooms), player, 0, 2).getRooms()

    _at(rooms[2], 1, 1).addEntity(Stone())
    second = builder.build(_map(rooms), player, 1, 2).getRooms()

    assert second[0] is first[0]
    assert second[1] is first[1]
    assert second[2] is not first[2]
    assert second[2].getTiles()[1 * GRID + 1] == ("Stone",)


def test_a_replaced_room_object_is_never_served_from_cache():
    # Same coordinates, different Room (as when a room is reloaded). Even if
    # the new object's revision happened to equal the cached one, the cache
    # must not serve the old room's tiles.
    player = Player(0)
    original = _room(0, 0)
    original.addEntityToLocation(player, _at(original, 0, 0))
    builder = _builder()
    builder.build(_map([original]), player, 0)
    replacement = _room(0, 0)
    _at(replacement, 4, 4).addEntity(Stone())
    replacement.addEntityToLocation(player, _at(replacement, 0, 0))
    replacement.revision = original.getRevision()

    view = builder.build(_map([replacement]), player, 1)

    assert view.getRooms()[0].getTiles()[4 * GRID + 4] == ("Stone",)


def test_room_type_change_rebuilds_the_biome():
    player = Player(0)
    room = _room()
    room.addEntityToLocation(player, _at(room, 0, 0))
    builder = _builder()
    builder.build(_map([room]), player, 0)

    room.setRoomType(RoomType.MOUNTAIN)
    view = builder.build(_map([room]), player, 1)

    assert view.getRooms()[0].getBiome() == RoomType.MOUNTAIN


# --- the change log: re-read only the locations that changed -----------------


def test_changed_locations_since_lists_only_later_changes():
    room = _room()
    first, second = _at(room, 0, 0), _at(room, 1, 0)
    first.addEntity(Stone())
    mark = room.getRevision()
    second.addEntity(Stone())
    first.addEntity(Grass())

    assert room.getChangedLocationsSince(mark) == [second, first]
    assert room.getChangedLocationsSince(room.getRevision()) == []


def test_change_log_overflow_and_set_grid_force_a_full_read():
    room = _room()
    mark = room.getRevision()
    for _ in range(100):  # more than the log keeps
        _at(room, 2, 2).addEntity(Stone())

    assert room.getChangedLocationsSince(mark) is None
    recent = room.getRevision()
    room.setGrid(_room().getGrid())
    assert room.getChangedLocationsSince(recent) is None


def test_many_changes_between_builds_are_never_missed():
    player = Player(0)
    room = _room()
    room.addEntityToLocation(player, _at(room, 0, 0))
    builder = _builder()
    builder.build(_map([room]), player, 0)
    for step in range(150):  # overflows the change log
        _at(room, step % GRID, (step // GRID) % GRID).addEntity(Stone())

    cached = builder.build(_map([room]), player, 1)
    fresh = _builder().build(_map([room]), player, 1)

    assert cached.getRooms()[0].getTiles() == fresh.getRooms()[0].getTiles()


def test_biome_follows_incremental_changes_for_rooms_without_a_room_type():
    player = Player(0)
    room = _room()
    room.addEntityToLocation(player, _at(room, 0, 0))
    grass = Grass()
    _at(room, 1, 1).addEntity(grass)
    builder = _builder()
    assert builder.build(_map([room]), player, 0).getRooms()[0].getBiome() == (
        RoomType.GRASSLAND
    )

    _at(room, 1, 1).removeEntity(grass)
    _at(room, 2, 2).addEntity(Stone())

    assert builder.build(_map([room]), player, 1).getRooms()[0].getBiome() == (
        RoomType.MOUNTAIN
    )


def test_unchanged_actors_reuse_their_view_and_moved_ones_do_not():
    player = Player(0)
    room = _room()
    room.addEntityToLocation(player, _at(room, 0, 0))
    chicken = Chicken(0)
    room.addEntityToLocation(chicken, _at(room, 2, 2))
    room.addLivingEntity(chicken)
    builder = _builder()
    [first] = builder.build(_map([room]), player, 0).getActors()
    [second] = builder.build(_map([room]), player, 1).getActors()

    _at(room, 2, 2).removeEntity(chicken)
    _at(room, 3, 2).addEntity(chicken)
    [third] = builder.build(_map([room]), player, 2).getActors()

    assert second is first
    assert (third.getTileX(), third.getTileY()) == (3, 2)
