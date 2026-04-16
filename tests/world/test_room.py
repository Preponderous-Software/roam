from unittest.mock import MagicMock

from src.world.room import Room
from src.entity.stone import Stone
from src.entity.grass import Grass
from src.entity.apple import Apple


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
