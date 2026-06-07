from types import SimpleNamespace
from unittest.mock import MagicMock

from entity.apple import Apple
from entity.excrement import Excrement
from entity.grass import Grass
from entity.living.chicken import Chicken
from entity.stone import Stone
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
