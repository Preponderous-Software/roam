from types import SimpleNamespace
from unittest.mock import MagicMock

from entity.apple import Apple
from entity.excrement import Excrement
from entity.grass import Grass
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from entity.living.npc import Npc
from entity.stone import Stone
from entity.woodFloor import WoodFloor
from src.world.room import Room


def createRoom():
    graphik = MagicMock()
    return Room("TestRoom", 3, (100, 200, 50), 0, 0, graphik)


def test_initialization():
    room = createRoom()

    assert room.getName() == "TestRoom"
    assert room.getBackgroundColor() == (100, 200, 50)
    assert room.getX() == 0
    assert room.getY() == 0
    assert room.getLivingEntities() == {}


def test_get_background_color():
    room = createRoom()

    assert room.getBackgroundColor() == (100, 200, 50)


def test_room_type_defaults_to_none():
    room = createRoom()

    assert room.getRoomType() is None


def test_set_room_type():
    room = createRoom()

    room.setRoomType("grassland")

    assert room.getRoomType() == "grassland"


def test_get_x():
    room = createRoom()

    assert room.getX() == 0


def test_get_y():
    room = createRoom()

    assert room.getY() == 0


def test_get_x_custom():
    graphik = MagicMock()
    room = Room("TestRoom", 3, (0, 0, 0), 5, 10, graphik)

    assert room.getX() == 5
    assert room.getY() == 10


def test_add_living_entity():
    room = createRoom()
    entity = MagicMock()
    entity.getID.return_value = "entity1"

    room.addLivingEntity(entity)

    assert "entity1" in room.getLivingEntities()
    assert room.getLivingEntities()["entity1"] == entity


def test_remove_living_entity():
    room = createRoom()
    entity = MagicMock()
    entity.getID.return_value = "entity1"

    room.addLivingEntity(entity)
    room.removeLivingEntity(entity)

    assert "entity1" not in room.getLivingEntities()


def test_remove_living_entity_not_found():
    room = createRoom()
    entity = MagicMock()
    entity.getID.return_value = "entity1"

    # should not raise, just prints a message
    room.removeLivingEntity(entity)

    assert len(room.getLivingEntities()) == 0


def test_remove_living_entity_by_id():
    room = createRoom()
    entity = MagicMock()
    entity.getID.return_value = "entity1"

    room.addLivingEntity(entity)
    room.removeLivingEntityById("entity1")

    assert "entity1" not in room.getLivingEntities()


def test_remove_living_entity_by_id_not_found():
    room = createRoom()

    # should not raise, just prints a message
    room.removeLivingEntityById("nonexistent")

    assert len(room.getLivingEntities()) == 0


def test_get_living_entities():
    room = createRoom()

    assert room.getLivingEntities() == {}


def test_set_living_entities():
    room = createRoom()
    livingEntities = {"id1": MagicMock(), "id2": MagicMock()}

    room.setLivingEntities(livingEntities)

    assert room.getLivingEntities() == livingEntities
    assert len(room.getLivingEntities()) == 2


def test_location_contains_solid_entity():
    room = createRoom()
    location = MagicMock()
    solidEntity = MagicMock()
    solidEntity.isSolid.return_value = True
    solidEntityId = "solid1"
    location.getEntities.return_value = {solidEntityId: solidEntity}
    location.getEntity.return_value = solidEntity

    assert room.locationContainsSolidEntity(location) == True


def test_location_does_not_contain_solid_entity():
    room = createRoom()
    location = MagicMock()
    nonSolidEntity = MagicMock()
    nonSolidEntity.isSolid.return_value = False
    entityId = "nonsolid1"
    location.getEntities.return_value = {entityId: nonSolidEntity}
    location.getEntity.return_value = nonSolidEntity

    assert room.locationContainsSolidEntity(location) == False


def test_location_contains_solid_entity_empty():
    room = createRoom()
    location = MagicMock()
    location.getEntities.return_value = {}

    assert room.locationContainsSolidEntity(location) == False


def test_location_contains_entity_of_type():
    room = createRoom()
    grass = Grass()
    location = MagicMock()
    location.getEntities.return_value = {grass.getID(): grass}
    location.getEntity.return_value = grass

    assert room.locationContainsEntityOfType(location, Grass) == True


def test_location_does_not_contain_entity_of_type():
    room = createRoom()
    stone = Stone()
    location = MagicMock()
    location.getEntities.return_value = {stone.getID(): stone}
    location.getEntity.return_value = stone

    assert room.locationContainsEntityOfType(location, Grass) == False


def test_location_contains_entity_of_type_empty():
    room = createRoom()
    location = MagicMock()
    location.getEntities.return_value = {}

    assert room.locationContainsEntityOfType(location, Grass) == False


def test_add_entity_to_room():
    room = createRoom()
    apple = Apple()

    room.addEntity(apple)

    assert room.getNumEntities() > 0


def test_grid_has_locations():
    room = createRoom()

    grid = room.getGrid()
    assert grid.getSize() == 9  # 3x3 grid


def test_move_living_entities_moves_and_feeds_when_food_is_present(monkeypatch):
    room = createRoom()
    entity = MagicMock()
    entity.getID.return_value = "entity1"
    entity.getLocationID.return_value = "location1"
    entity.needsEnergy.return_value = True
    entity.canEat.return_value = True

    currentLocation = MagicMock()
    newLocation = MagicMock()
    newLocation.getID.return_value = "location2"
    targetEntity = Apple()
    newLocationEntities = {"entity1": entity, "food1": targetEntity}
    newLocation.getEntities.return_value = newLocationEntities
    newLocation.getEntity.side_effect = lambda entityId: newLocationEntities[entityId]

    room.setLivingEntities({"entity1": entity})
    room.getGrid().getLocation = MagicMock(return_value=currentLocation)
    room.getRandomAdjacentLocation = MagicMock(return_value=newLocation)
    room.locationContainsSolidEntity = MagicMock(return_value=False)
    room.removeEntity = MagicMock()
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    entitiesToMoveToNewRoom = room.moveLivingEntities(100)

    assert entitiesToMoveToNewRoom == []
    currentLocation.removeEntity.assert_called_once_with(entity)
    newLocation.addEntity.assert_called_once_with(entity)
    entity.setLocationID.assert_called_once_with("location2")
    entity.removeEnergy.assert_called_once_with(1)
    room.removeEntity.assert_called_once_with(targetEntity)
    entity.addEnergy.assert_called_once_with(10)


def test_reproduce_living_entities_respects_reproduction_cooldown():
    room = createRoom()
    location = room.getGrid().getLocation(list(room.getGrid().getLocations().keys())[0])
    firstChicken = Chicken(0)
    secondChicken = Chicken(0)
    firstChicken.setEnergy(80)
    secondChicken.setEnergy(80)
    firstChicken.setLocationID(location.getID())
    secondChicken.setLocationID(location.getID())
    firstChicken.setTickLastReproduced(9_500)
    secondChicken.setTickLastReproduced(9_500)
    room.addEntityToLocation(firstChicken, location)
    room.addEntityToLocation(secondChicken, location)
    room.addLivingEntity(firstChicken)
    room.addLivingEntity(secondChicken)

    room.reproduceLivingEntities(10_000)

    assert len(room.getLivingEntities()) == 2
    chickenCount = 0
    for entity in location.getEntities().values():
        if isinstance(entity, Chicken):
            chickenCount += 1
    assert chickenCount == 2


def _firstLocation(room):
    grid = room.getGrid()
    return grid.getLocation(list(grid.getLocations().keys())[0])


def _entitiesOfType(location, entityType):
    return [
        entity
        for entity in location.getEntities().values()
        if isinstance(entity, entityType)
    ]


def _totalExcrement(room):
    grid = room.getGrid()
    return sum(
        len(_entitiesOfType(grid.getLocation(locationId), Excrement))
        for locationId in grid.getLocations()
    )


def test_tick_excrement_spawns_excrement_for_living_entity(monkeypatch):
    room = createRoom()
    location = _firstLocation(room)
    entity = MagicMock()
    entity.getID.return_value = "e1"
    entity.getLocationID.return_value = location.getID()
    room.addLivingEntity(entity)
    # randrange returns 1, so "> 1" is False -> the entity produces excrement.
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.tickExcrement(0, SimpleNamespace(excrementDecayTicks=100))

    assert len(_entitiesOfType(location, Excrement)) == 1


def test_tick_excrement_does_not_spawn_when_chance_misses(monkeypatch):
    room = createRoom()
    location = _firstLocation(room)
    entity = MagicMock()
    entity.getID.return_value = "e1"
    entity.getLocationID.return_value = location.getID()
    room.addLivingEntity(entity)
    # randrange returns 2, so "> 1" is True -> the spawn branch is skipped.
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 2)

    room.tickExcrement(0, SimpleNamespace(excrementDecayTicks=100))

    assert _entitiesOfType(location, Excrement) == []


def test_tick_excrement_skips_entity_with_no_location(monkeypatch):
    room = createRoom()
    entity = MagicMock()
    entity.getID.return_value = "e1"
    entity.getLocationID.return_value = "-1"
    room.addLivingEntity(entity)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.tickExcrement(0, SimpleNamespace(excrementDecayTicks=100))

    assert _totalExcrement(room) == 0


def test_tick_excrement_handles_missing_location(monkeypatch):
    room = createRoom()
    entity = MagicMock()
    entity.getID.return_value = "e1"
    entity.getLocationID.return_value = "nonexistent-location"
    room.addLivingEntity(entity)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    # getGrid().getLocation raises KeyError for the bogus id; tickExcrement
    # must swallow it rather than crash.
    room.tickExcrement(0, SimpleNamespace(excrementDecayTicks=100))

    assert _totalExcrement(room) == 0


def test_tick_excrement_does_not_decay_before_threshold():
    room = createRoom()
    location = _firstLocation(room)
    room.addEntityToLocation(Excrement(0), location)

    # tick - tickCreated = 10 < 100, so the excrement is left in place.
    room.tickExcrement(10, SimpleNamespace(excrementDecayTicks=100))

    assert len(_entitiesOfType(location, Excrement)) == 1
    assert _entitiesOfType(location, Grass) == []


def test_tick_excrement_decays_into_grass():
    room = createRoom()
    location = _firstLocation(room)
    room.addEntityToLocation(Excrement(0), location)

    # tick - tickCreated = 10 >= 5 and the location is otherwise empty, so the
    # excrement decays into grass.
    room.tickExcrement(10, SimpleNamespace(excrementDecayTicks=5))

    assert _entitiesOfType(location, Excrement) == []
    assert len(_entitiesOfType(location, Grass)) == 1


def test_tick_excrement_does_not_place_grass_over_existing_grass():
    room = createRoom()
    location = _firstLocation(room)
    room.addEntityToLocation(Grass(), location)
    room.addEntityToLocation(Excrement(0), location)

    room.tickExcrement(10, SimpleNamespace(excrementDecayTicks=5))

    # The excrement is removed, but no second grass is placed on top.
    assert _entitiesOfType(location, Excrement) == []
    assert len(_entitiesOfType(location, Grass)) == 1


def test_tick_excrement_does_not_place_grass_over_solid_entity():
    room = createRoom()
    location = _firstLocation(room)
    room.addEntityToLocation(Stone(), location)
    room.addEntityToLocation(Excrement(0), location)

    room.tickExcrement(10, SimpleNamespace(excrementDecayTicks=5))

    assert _entitiesOfType(location, Excrement) == []
    assert _entitiesOfType(location, Grass) == []
    assert len(_entitiesOfType(location, Stone)) == 1


def test_tick_excrement_does_not_place_grass_over_floor():
    room = createRoom()
    location = _firstLocation(room)
    room.addEntityToLocation(WoodFloor(), location)
    room.addEntityToLocation(Excrement(0), location)

    room.tickExcrement(10, SimpleNamespace(excrementDecayTicks=5))

    assert _entitiesOfType(location, Excrement) == []
    assert _entitiesOfType(location, Grass) == []
    assert len(_entitiesOfType(location, WoodFloor)) == 1


# --- drawing ---


def _locationAt(room, x, y):
    return room.getGrid().getLocationByCoordinates(x, y)


def _drawnRectPositions(renderer):
    return {(c.args[0], c.args[1]) for c in renderer.drawRectangle.call_args_list}


def test_draw_fills_every_location_with_overlap(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer

    room.draw(10, 10)

    # Each tile is drawn 1px up/left of its cell and 2px larger, so that
    # neighbouring tiles overlap and no seam shows between them.
    assert renderer.drawRectangle.call_count == 9
    for c in renderer.drawRectangle.call_args_list:
        assert c.args[2:] == (12, 12, (100, 200, 50))
    assert _drawnRectPositions(renderer) == {
        (x * 10 - 1, y * 10 - 1) for x in range(3) for y in range(3)
    }
    renderer.drawImage.assert_not_called()


def test_draw_with_offset_translates_every_location(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer

    room.drawWithOffset(10, 10, 100, 50)

    assert renderer.drawRectangle.call_count == 9
    for c in renderer.drawRectangle.call_args_list:
        assert c.args[2:4] == (12, 12)
    assert _drawnRectPositions(renderer) == {
        (100 + x * 10 - 1, 50 + y * 10 - 1) for x in range(3) for y in range(3)
    }


def test_draw_with_offset_skips_columns_past_clip_width(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer

    # Column x=2 starts at 19px, beyond the 10px clip, so it is skipped.
    room.drawWithOffset(10, 10, 0, 0, clipWidth=10)

    assert _drawnRectPositions(renderer) == {
        (x * 10 - 1, y * 10 - 1) for x in range(2) for y in range(3)
    }


def test_draw_with_offset_skips_columns_left_of_origin(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer

    # With a -25px offset, columns x=0 and x=1 end before 0 and are skipped.
    room.drawWithOffset(10, 10, -25, 0, clipWidth=100)

    assert _drawnRectPositions(renderer) == {(-6, y * 10 - 1) for y in range(3)}


def test_draw_with_offset_skips_rows_outside_clip_height(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer

    room.drawWithOffset(10, 10, 0, 0, clipWidth=100, clipHeight=10)

    assert _drawnRectPositions(renderer) == {
        (x * 10 - 1, y * 10 - 1) for x in range(3) for y in range(2)
    }


def test_draw_location_draws_background_only_when_empty(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer

    room.drawLocation(_locationAt(room, 0, 0), 5, 6, 12, 12)

    renderer.drawRectangle.assert_called_once_with(5, 6, 12, 12, (100, 200, 50))
    renderer.loadImage.assert_not_called()
    renderer.drawImage.assert_not_called()


def test_draw_location_draws_most_recently_added_entity(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer
    location = _locationAt(room, 0, 0)
    room.addEntityToLocation(Grass(), location)
    room.addEntityToLocation(Stone(), location)

    room.drawLocation(location, 5, 6, 12, 12)

    renderer.loadImage.assert_called_once_with("assets/images/stone.png")
    renderer.scaleImage.assert_called_once_with(
        renderer.loadImage.return_value, (12, 12)
    )
    renderer.drawImage.assert_called_once_with(renderer.scaleImage.return_value, (5, 6))


def test_draw_location_reuses_cached_scaled_image(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer
    location = _locationAt(room, 0, 0)
    room.addEntityToLocation(Stone(), location)

    room.drawLocation(location, 0, 0, 12, 12)
    room.drawLocation(location, 20, 20, 12, 12)

    renderer.loadImage.assert_called_once()
    renderer.scaleImage.assert_called_once()
    assert renderer.drawImage.call_count == 2


def test_draw_location_rescales_for_a_different_size(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    room = createRoom()
    renderer = room.renderer
    location = _locationAt(room, 0, 0)
    room.addEntityToLocation(Stone(), location)

    room.drawLocation(location, 0, 0, 12, 12)
    room.drawLocation(location, 0, 0, 22, 22)

    assert renderer.scaleImage.call_count == 2
    assert set(Room._scaledImageCache) == {
        ("assets/images/stone.png", 12, 12),
        ("assets/images/stone.png", 22, 22),
    }


def test_draw_location_evicts_oldest_cache_entry_when_full(monkeypatch):
    monkeypatch.setattr(Room, "_scaledImageCache", {})
    monkeypatch.setattr("src.world.room._IMAGE_CACHE_MAX", 1)
    room = createRoom()
    grassLocation = _locationAt(room, 0, 0)
    stoneLocation = _locationAt(room, 1, 0)
    room.addEntityToLocation(Grass(), grassLocation)
    room.addEntityToLocation(Stone(), stoneLocation)

    room.drawLocation(grassLocation, 0, 0, 12, 12)
    room.drawLocation(stoneLocation, 0, 0, 12, 12)

    assert list(Room._scaledImageCache) == [("assets/images/stone.png", 12, 12)]


# --- adjacency ---


def test_get_random_adjacent_location_maps_each_direction(monkeypatch):
    room = createRoom()
    center = _locationAt(room, 1, 1)
    expected = {
        0: _locationAt(room, 1, 0),  # up
        1: _locationAt(room, 2, 1),  # right
        2: _locationAt(room, 1, 2),  # down
        3: _locationAt(room, 0, 1),  # left
    }

    for directionIndex, expectedLocation in expected.items():
        monkeypatch.setattr(
            "src.world.room.random.randrange",
            lambda _start, _stop, d=directionIndex: d,
        )
        assert room.getRandomAdjacentLocation(center) is expectedLocation


def test_get_random_adjacent_location_returns_minus_one_off_grid(monkeypatch):
    room = createRoom()
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 0)

    assert room.getRandomAdjacentLocation(_locationAt(room, 0, 0)) == -1


# --- movement ---


def _patchMovementRandom(monkeypatch, moveRoll, direction):
    # randrange(1, 101) is the 1% move roll; randrange(0, 4) picks a direction.
    def fakeRandrange(start, _stop):
        return moveRoll if start == 1 else direction

    monkeypatch.setattr("src.world.room.random.randrange", fakeRandrange)


def _placeLivingEntity(room, entity, location):
    room.addEntityToLocation(entity, location)
    room.addLivingEntity(entity)


def test_move_living_entities_moves_entity_and_costs_one_energy(monkeypatch):
    room = createRoom()
    start = _locationAt(room, 1, 1)
    chicken = Chicken(0)
    chicken.setEnergy(20)
    _placeLivingEntity(room, chicken, start)
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    result = room.moveLivingEntities(0)

    destination = _locationAt(room, 2, 1)
    assert result == []
    assert not start.isEntityPresent(chicken)
    assert destination.isEntityPresent(chicken)
    assert chicken.getLocationID() == destination.getID()
    assert chicken.getEnergy() == 19


def test_move_living_entities_skips_when_move_roll_misses(monkeypatch):
    room = createRoom()
    start = _locationAt(room, 1, 1)
    chicken = Chicken(0)
    chicken.setEnergy(20)
    _placeLivingEntity(room, chicken, start)
    _patchMovementRandom(monkeypatch, moveRoll=2, direction=1)

    assert room.moveLivingEntities(0) == []
    assert start.isEntityPresent(chicken)
    assert chicken.getEnergy() == 20


def test_move_living_entities_skips_npcs(monkeypatch):
    room = createRoom()
    start = _locationAt(room, 1, 1)
    npc = Npc("Villager", 0)
    _placeLivingEntity(room, npc, start)
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    assert room.moveLivingEntities(0) == []
    assert start.isEntityPresent(npc)
    assert npc.getEnergy() == 100


def test_move_living_entities_skips_entity_without_location(monkeypatch):
    room = createRoom()
    chicken = Chicken(0)
    room.addLivingEntity(chicken)
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    assert chicken.getLocationID() == -1
    assert room.moveLivingEntities(0) == []


def test_move_living_entities_skips_entity_with_unknown_location(monkeypatch):
    room = createRoom()
    chicken = Chicken(0)
    chicken.setEnergy(20)
    chicken.setLocationID("nonexistent-location")
    room.addLivingEntity(chicken)
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    assert room.moveLivingEntities(0) == []
    assert chicken.getEnergy() == 20


def test_move_living_entities_returns_entity_walking_off_the_grid(monkeypatch):
    room = createRoom()
    edge = _locationAt(room, 1, 0)
    chicken = Chicken(0)
    chicken.setEnergy(20)
    _placeLivingEntity(room, chicken, edge)
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=0)  # up

    result = room.moveLivingEntities(0)

    # The caller moves it to the neighbouring room; this room leaves it put.
    assert result == [chicken]
    assert edge.isEntityPresent(chicken)
    assert chicken.getEnergy() == 20


def test_move_living_entities_does_not_enter_solid_location(monkeypatch):
    room = createRoom()
    start = _locationAt(room, 1, 1)
    room.addEntityToLocation(Stone(), _locationAt(room, 2, 1))
    chicken = Chicken(0)
    chicken.setEnergy(20)
    _placeLivingEntity(room, chicken, start)
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    assert room.moveLivingEntities(0) == []
    assert start.isEntityPresent(chicken)
    assert chicken.getEnergy() == 20


# --- feeding after a move ---


def test_hungry_entity_eats_non_living_food_at_destination(monkeypatch):
    room = createRoom()
    chicken = Chicken(0)
    chicken.setEnergy(5)
    grass = Grass()
    room.addEntityToLocation(grass, _locationAt(room, 2, 1))
    _placeLivingEntity(room, chicken, _locationAt(room, 1, 1))
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    room.moveLivingEntities(0)

    assert not _locationAt(room, 2, 1).isEntityPresent(grass)
    assert chicken.getEnergy() == 5 - 1 + 10


def test_well_fed_entity_does_not_eat_food_at_destination(monkeypatch):
    room = createRoom()
    chicken = Chicken(0)
    chicken.setEnergy(100)
    grass = Grass()
    room.addEntityToLocation(grass, _locationAt(room, 2, 1))
    _placeLivingEntity(room, chicken, _locationAt(room, 1, 1))
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    room.moveLivingEntities(0)

    assert _locationAt(room, 2, 1).isEntityPresent(grass)
    assert chicken.getEnergy() == 99


def test_hungry_entity_ignores_inedible_entity_at_destination(monkeypatch):
    room = createRoom()
    chicken = Chicken(0)
    chicken.setEnergy(5)
    apple = Apple()
    room.addEntityToLocation(apple, _locationAt(room, 2, 1))
    _placeLivingEntity(room, chicken, _locationAt(room, 1, 1))
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    room.moveLivingEntities(0)

    assert _locationAt(room, 2, 1).isEntityPresent(apple)
    assert chicken.getEnergy() == 4


def test_hungry_predator_kills_living_prey_but_gains_no_energy(monkeypatch):
    room = createRoom()
    bear = Bear(0)
    bear.setEnergy(5)
    chicken = Chicken(0)
    chicken.setEnergy(20)
    room.addEntityToLocation(chicken, _locationAt(room, 2, 1))
    _placeLivingEntity(room, bear, _locationAt(room, 1, 1))
    _patchMovementRandom(monkeypatch, moveRoll=1, direction=1)

    room.moveLivingEntities(0)

    # Characterizes current behavior: the prey is killed before its energy
    # is read, so the predator is credited with 0 rather than 20.
    assert chicken.getEnergy() == 0
    assert chicken.isDead()
    assert bear.getEnergy() == 4


# --- reproduction ---


def _placeReadyPair(room, first, second, energy=80):
    location = _firstLocation(room)
    first.setEnergy(energy)
    second.setEnergy(energy)
    _placeLivingEntity(room, first, location)
    _placeLivingEntity(room, second, location)
    return location


def test_reproduce_living_entities_creates_one_offspring(monkeypatch):
    room = createRoom()
    first = Chicken(0)
    second = Chicken(0)
    location = _placeReadyPair(room, first, second)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.reproduceLivingEntities(10_000)

    # The second parent is on cooldown by the time it is iterated, so the
    # pair yields exactly one offspring.
    chickens = _entitiesOfType(location, Chicken)
    assert len(chickens) == 3
    assert len(room.getLivingEntities()) == 3
    offspring = [c for c in chickens if c is not first and c is not second][0]
    assert offspring.getTickCreated() == 10_000
    assert offspring.getID() in room.getLivingEntities()
    assert first.getEnergy() == 40
    assert second.getEnergy() == 40
    assert offspring.getEnergy() == (40 + 40) / 2 * 0.1
    assert first.getTickLastReproduced() == 10_000
    assert second.getTickLastReproduced() == 10_000
    cooldownImage = "assets/images/chickenOnReproductionCooldown.png"
    assert first.getImagePath() == cooldownImage
    assert second.getImagePath() == cooldownImage


def test_reproduce_living_entities_resets_image_when_chance_misses(monkeypatch):
    room = createRoom()
    first = Chicken(0)
    second = Chicken(0)
    location = _placeReadyPair(room, first, second)
    first.setImagePath("assets/images/chickenOnReproductionCooldown.png")
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 2)

    room.reproduceLivingEntities(10_000)

    assert len(_entitiesOfType(location, Chicken)) == 2
    assert first.getImagePath() == "assets/images/chicken.png"
    assert first.getEnergy() == 80


def test_reproduce_living_entities_requires_minimum_age(monkeypatch):
    room = createRoom()
    first = Chicken(0)
    second = Chicken(0)
    location = _placeReadyPair(room, first, second)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    # 30 * 60 * 5 = 9000 ticks is the minimum age; 8999 is one short.
    room.reproduceLivingEntities(8_999)

    assert len(_entitiesOfType(location, Chicken)) == 2
    assert first.getEnergy() == 80


def test_reproduce_living_entities_requires_adult_partner(monkeypatch):
    room = createRoom()
    adult = Chicken(0)
    juvenile = Chicken(5_000)
    location = _placeReadyPair(room, adult, juvenile)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.reproduceLivingEntities(10_000)

    assert len(_entitiesOfType(location, Chicken)) == 2
    assert adult.getEnergy() == 80
    assert juvenile.getEnergy() == 80


def test_reproduce_living_entities_ignores_non_living_entities(monkeypatch):
    room = createRoom()
    chicken = Chicken(0)
    chicken.setEnergy(80)
    location = _firstLocation(room)
    room.addEntityToLocation(Grass(), location)
    _placeLivingEntity(room, chicken, location)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.reproduceLivingEntities(10_000)

    assert len(location.getEntities()) == 2
    assert chicken.getEnergy() == 80


def test_reproduce_living_entities_requires_same_species(monkeypatch):
    room = createRoom()
    chicken = Chicken(0)
    bear = Bear(0)
    location = _placeReadyPair(room, chicken, bear)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.reproduceLivingEntities(10_000)

    assert len(location.getEntities()) == 2
    assert chicken.getEnergy() == 80
    assert bear.getEnergy() == 80


def test_reproduce_living_entities_requires_well_fed_partner(monkeypatch):
    room = createRoom()
    first = Chicken(0)
    second = Chicken(0)
    location = _placeReadyPair(room, first, second)
    second.setEnergy(1)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.reproduceLivingEntities(10_000)

    # The hungry chicken is rejected as a partner, but an initiator's own
    # energy is never checked, so it still breeds with the well-fed one.
    assert len(_entitiesOfType(location, Chicken)) == 3
    assert first.getTickLastReproduced() == 10_000


def test_reproduce_living_entities_skips_npcs(monkeypatch):
    room = createRoom()
    first = Npc("Villager", 0)
    second = Npc("Villager", 0)
    location = _placeReadyPair(room, first, second)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.reproduceLivingEntities(10_000)

    assert len(location.getEntities()) == 2
    assert first.getEnergy() == 80
    assert second.getEnergy() == 80


def test_reproduce_living_entities_halves_energy_even_without_offspring(
    monkeypatch,
):
    room = createRoom()
    first = LivingEntity("Thing", "assets/images/thing.png", 50, [], 0)
    second = LivingEntity("Thing", "assets/images/thing.png", 50, [], 0)
    location = _placeReadyPair(room, first, second, energy=50)
    monkeypatch.setattr("src.world.room.random.randrange", lambda _start, _stop: 1)

    room.reproduceLivingEntities(10_000)

    # The base LivingEntity.createOffspring returns None: both attempts
    # (each entity initiating once) spend energy, but nothing is spawned
    # and neither parent is put on cooldown.
    assert len(location.getEntities()) == 2
    assert first.getEnergy() == 12.5
    assert second.getEnergy() == 12.5
    assert first.getTickLastReproduced() is None
    assert second.getTickLastReproduced() is None
