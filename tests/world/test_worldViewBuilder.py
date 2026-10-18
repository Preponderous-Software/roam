import threading
from unittest.mock import MagicMock

import pytest

from entity.campfire import Campfire
from entity.grass import Grass
from entity.living.chicken import Chicken
from entity.stone import Stone
from entity.torch import Torch
from player.player import Player
from rendering.worldView import (
    ActorView,
    CameraHint,
    LightView,
    RoomView,
    WorldView,
)
from rendering.worldViewSink import NullWorldViewSink, WorldViewSink
from screen.worldScreen import WorldScreen
from world.dayNightCycle import DayNightCycle
from world.room import Room
from world.worldViewBuilder import WorldViewBuilder

GRID = 5
_VIEW_TYPES = (WorldView, RoomView, ActorView, LightView, CameraHint)


def _config():
    config = MagicMock()
    config.dayNightCycleEnabled = True
    config.dayNightCycleLengthTicks = 1000
    config.cameraFollowPlayer = True
    return config


def _builder():
    config = _config()
    return WorldViewBuilder(DayNightCycle(config), config)


def _room(x, y, z=0):
    return Room("r", GRID, (1, 2, 3), x, y, MagicMock(), z)


def _put(room, entity, x, y):
    location = room.getGrid().getLocationByCoordinates(x, y)
    room.addEntityToLocation(entity, location)
    return location


def _map(rooms):
    fakeMap = MagicMock()
    fakeMap._lock = threading.Lock()
    fakeMap.getRooms.return_value = rooms
    return fakeMap


def _world():
    home = _room(0, 0)
    player = Player(0)
    _put(home, Grass(), 2, 2)
    _put(home, player, 2, 2)
    _put(home, Torch(), 1, 1)
    chicken = Chicken(0)
    _put(home, chicken, 3, 4)
    home.addLivingEntity(chicken)
    east = _room(1, 0)
    _put(east, Campfire(), 4, 0)
    far = _room(5, 5)
    return [home, east, far], home, player, chicken


def _assertOnlyCopies(value, path="view"):
    if isinstance(value, _VIEW_TYPES):
        for name in type(value).__slots__:
            _assertOnlyCopies(getattr(value, name), path + "." + name)
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            _assertOnlyCopies(item, path + "[" + str(index) + "]")
    else:
        assert value is None or isinstance(value, (bool, int, float, str)), path


def test_view_holds_only_primitives_and_tuples():
    rooms, _, player, _ = _world()

    worldView = _builder().build(_map(rooms), player, 10)

    _assertOnlyCopies(worldView)


def test_view_parts_cannot_be_reassigned():
    rooms, _, player, _ = _world()
    worldView = _builder().build(_map(rooms), player, 10)

    with pytest.raises(AttributeError):
        worldView._tick = 99
    with pytest.raises(AttributeError):
        worldView.getRooms()[0]._tiles = ()
    with pytest.raises(AttributeError):
        worldView.getPlayer().newField = 1


def test_rooms_tiles_and_radius():
    rooms, _, player, _ = _world()

    worldView = _builder().build(_map(rooms), player, 10, radiusRooms=1)

    keys = [roomView.getKey() for roomView in worldView.getRooms()]
    assert keys == [(0, 0, 0), (1, 0, 0)]
    home = worldView.getRooms()[0]
    assert len(home.getTiles()) == GRID * GRID
    assert home.getTiles()[2 * GRID + 2] == ("Grass",)  # player left out
    assert home.getTiles()[4 * GRID + 3] == ("Chicken",)
    assert home.getBiome() == "grassland"
    assert worldView.getGridSize() == GRID
    assert worldView.getCameraHint().getFocusTile() == (2, 2)
    assert worldView.getCameraHint().getVisibleRadiusRooms() == 1


def test_player_and_living_entities_are_actors():
    rooms, _, player, chicken = _world()
    player.setDirection(3)

    worldView = _builder().build(_map(rooms), player, 10)

    playerView = worldView.getPlayer()
    assert (playerView.getEntityClass(), playerView.getRoom()) == (
        "Player",
        (0, 0, 0),
    )
    assert (playerView.getTileX(), playerView.getTileY()) == (2, 2)
    assert playerView.getDirection() == "right"
    assert playerView.getSpriteKey() == "assets/images/player_right.png"
    [actor] = worldView.getActors()
    assert actor.getEntityId() == str(chicken.getID())
    assert (actor.getTileX(), actor.getTileY()) == (3, 4)


def test_lights_are_in_tile_coordinates():
    rooms, _, player, _ = _world()

    worldView = _builder().build(_map(rooms), player, 10)

    assert [
        (l.getRoom(), l.getTileX(), l.getTileY(), l.getRadiusTiles())
        for l in worldView.getLights()
    ] == [((0, 0, 0), 1, 1, 6), ((1, 0, 0), 4, 0, 8)]


def test_lights_match_the_2d_overlay_collector():
    rooms, home, player, _ = _world()
    worldScreen = WorldScreen.__new__(WorldScreen)
    worldScreen.locationWidth = 40
    worldScreen.locationHeight = 30
    pixelSources = []

    worldScreen._collectLightSourcesFromRoom(home, 100, 50, pixelSources)
    worldView = _builder().build(_map(rooms), player, 10)

    homeLights = [l for l in worldView.getLights() if l.getRoom() == (0, 0, 0)]
    assert pixelSources == [
        (100 + l.getTileX() * 40 + 20, 50 + l.getTileY() * 30 + 15, l.getRadiusTiles())
        for l in homeLights
    ]
    assert pixelSources == [(100 + 40 + 20, 50 + 30 + 15, 6)]


def test_revision_is_stable_until_a_stack_changes():
    rooms, home, player, _ = _world()
    builder = _builder()

    first = builder.build(_map(rooms), player, 1).getRooms()[0]
    second = builder.build(_map(rooms), player, 2).getRooms()[0]
    # A direct Location mutation (as worldScreen does) bypasses Room.
    location = home.getGrid().getLocationByCoordinates(0, 3)
    stone = Stone()
    location.addEntity(stone)
    third = builder.build(_map(rooms), player, 3).getRooms()[0]
    location.removeEntity(stone)
    fourth = builder.build(_map(rooms), player, 4).getRooms()[0]

    assert second is first  # unchanged room: the cached view is reused
    assert third.getRevision() != first.getRevision()
    assert third.getTiles()[3 * GRID + 0] == ("Stone",)
    assert fourth.getRevision() not in (first.getRevision(), third.getRevision())
    assert fourth.getTiles() == first.getTiles()


def test_no_view_when_the_player_is_not_in_a_loaded_room():
    rooms, _, player, _ = _world()

    assert _builder().build(_map(rooms[1:]), player, 1) is None


def test_day_night_fields():
    rooms, _, player, _ = _world()

    worldView = _builder().build(_map(rooms), player, 500)

    assert worldView.isDayNightEnabled() is True
    assert worldView.getOverlayOpacity() == 200
    assert worldView.getPhase() == "night"
    assert worldView.getCycleLengthTicks() == 1000


# --- publishing from WorldScreen -------------------------------------------


class _WantingSink(WorldViewSink):
    def __init__(self, radius):
        self.radius = radius
        self.published = []

    def wantsWorldView(self):
        return True

    def getWantedRadiusRooms(self):
        return self.radius

    def publish(self, worldView):
        self.published.append(worldView)


def _publishingScreen(sinks):
    worldScreen = WorldScreen.__new__(WorldScreen)
    worldScreen.worldViewSinks = tuple(sinks)
    worldScreen.worldViewBuilder = MagicMock()
    worldScreen.map = MagicMock()
    worldScreen.player = MagicMock()
    worldScreen.tickCounter = MagicMock()
    worldScreen.tickCounter.getTick.return_value = 7
    return worldScreen


def test_2d_frontends_never_build_a_view():
    worldScreen = _publishingScreen([NullWorldViewSink(), NullWorldViewSink()])

    for _ in range(100):
        worldScreen._publishWorldView()

    worldScreen.worldViewBuilder.build.assert_not_called()


def test_a_wanting_sink_gets_one_view_at_the_largest_wanted_radius():
    near, far = _WantingSink(1), _WantingSink(3)
    worldScreen = _publishingScreen([NullWorldViewSink(), near, far])

    worldScreen._publishWorldView()

    worldScreen.worldViewBuilder.build.assert_called_once_with(
        worldScreen.map, worldScreen.player, 7, 3
    )
    view = worldScreen.worldViewBuilder.build.return_value
    assert near.published == [view]
    assert far.published == [view]


def test_nothing_is_published_without_a_view():
    sink = _WantingSink(1)
    worldScreen = _publishingScreen([sink])
    worldScreen.worldViewBuilder.build.return_value = None

    worldScreen._publishWorldView()

    assert sink.published == []


def test_default_sink_is_null(resolve):
    sink = resolve(WorldViewSink)

    assert isinstance(sink, NullWorldViewSink)
    assert sink.wantsWorldView() is False


def test_world_screen_publishes_after_logic_and_before_drawing():
    worldScreen = WorldScreen.__new__(WorldScreen)
    calls = MagicMock()
    for name in (
        "_updateGoals",
        "_updateAchievements",
        "handleMouseOver",
        "handlePlayerActions",
        "removeEnergyAndCheckForPlayerDeath",
        "checkForLivingEntityDeaths",
        "_setFacingTileHint",
        "_publishWorldView",
        "draw",
    ):
        setattr(worldScreen, name, getattr(calls, name))
    worldScreen.pausedByFocusLoss = False
    worldScreen.deathRespawnTicksRemaining = 0
    worldScreen.currentRoom = MagicMock()
    worldScreen.renderer = MagicMock()
    worldScreen.status = MagicMock()
    worldScreen.tickCounter = MagicMock()
    worldScreen.config = MagicMock()
    worldScreen.config.limitTps = False
    worldScreen.config.showMiniMap = False

    worldScreen._updateGameState()

    order = [call[0] for call in calls.mock_calls]
    assert order.index("_publishWorldView") > order.index("_setFacingTileHint")
    assert order.index("_publishWorldView") < order.index("draw")
    assert order.count("_publishWorldView") == 1
