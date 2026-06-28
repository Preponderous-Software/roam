import pytest
from unittest.mock import MagicMock
from entity.caveEntrance import CaveEntrance
from entity.caveLadder import CaveLadder
from entity.caveFloor import CaveFloor
from entity.goldOre import GoldOre
from entity.coalOre import CoalOre
from entity.ironOre import IronOre
from entity.stone import Stone
from world.room import Room
from world.roomFactory import RoomFactory
from world.roomType import RoomType


def _make_factory(grid_size=17):
    renderer = MagicMock()
    renderer.supportsImageLoading.return_value = False
    renderer.loadImage.side_effect = lambda path: path[0]
    renderer.scaleImage.side_effect = lambda img, size: img
    tick_counter = MagicMock()
    tick_counter.getTick.return_value = 0
    return RoomFactory(grid_size, renderer, tick_counter)


def _entities_in_room(room):
    entities = []
    for loc_id in room.getGrid().getLocations():
        loc = room.getGrid().getLocation(loc_id)
        for ent_id in loc.getEntities():
            entities.append(loc.getEntity(ent_id))
    return entities


class TestRoomZ:
    def test_room_z_default_zero(self):
        renderer = MagicMock()
        room = Room("test", 5, (0, 0, 0), 0, 0, renderer)
        assert room.getZ() == 0

    def test_room_z_set(self):
        renderer = MagicMock()
        room = Room("test", 5, (0, 0, 0), 3, -2, renderer, z=-2)
        assert room.getZ() == -2

    def test_room_factory_passes_z(self):
        factory = _make_factory()
        room = factory.createEmptyRoom((0, 0, 0), 1, 2, z=-1)
        assert room.getZ() == -1


class TestCaveRoomGeneration:
    def test_cave_room_has_correct_z(self):
        factory = _make_factory()
        room = factory.createCaveRoom(0, 0, z=-1)
        assert room.getZ() == -1

    def test_cave_room_has_ladder(self):
        factory = _make_factory()
        room = factory.createCaveRoom(0, 0, z=-1)
        entities = _entities_in_room(room)
        ladders = [e for e in entities if isinstance(e, CaveLadder)]
        assert len(ladders) == 1

    def test_cave_room_has_cave_floor(self):
        factory = _make_factory()
        room = factory.createCaveRoom(0, 0, z=-1)
        entities = _entities_in_room(room)
        floors = [e for e in entities if isinstance(e, CaveFloor)]
        assert len(floors) > 0

    def test_cave_room_has_stone_walls(self):
        factory = _make_factory()
        room = factory.createCaveRoom(0, 0, z=-1)
        entities = _entities_in_room(room)
        stones = [e for e in entities if isinstance(e, Stone)]
        assert len(stones) > 0

    def test_cave_room_has_ore(self):
        # Run multiple times to account for randomness in ore spawning
        factory = _make_factory()
        found_ore = False
        for _ in range(10):
            room = factory.createCaveRoom(0, 0, z=-1)
            entities = _entities_in_room(room)
            if any(isinstance(e, (CoalOre, IronOre)) for e in entities):
                found_ore = True
                break
        assert found_ore

    def test_deep_cave_can_have_gold(self):
        factory = _make_factory()
        found_gold = False
        for _ in range(20):
            room = factory.createCaveRoom(0, 0, z=-3)
            entities = _entities_in_room(room)
            if any(isinstance(e, GoldOre) for e in entities):
                found_gold = True
                break
        assert found_gold

    def test_centre_is_accessible(self):
        factory = _make_factory(grid_size=17)
        room = factory.createCaveRoom(0, 0, z=-1)
        centre = 17 // 2
        loc = room.getGrid().getLocationByCoordinates(centre, centre)
        assert loc != -1
        entities_at_centre = list(loc.getEntities().values())
        solid_at_centre = any(e.isSolid() for e in entities_at_centre)
        assert not solid_at_centre

    def test_ladder_is_on_open_cell(self):
        factory = _make_factory()
        room = factory.createCaveRoom(0, 0, z=-1)
        entities = _entities_in_room(room)
        for loc_id in room.getGrid().getLocations():
            loc = room.getGrid().getLocation(loc_id)
            for ent_id in loc.getEntities():
                entity = loc.getEntity(ent_id)
                if isinstance(entity, CaveLadder):
                    other_entities = [
                        loc.getEntity(eid) for eid in loc.getEntities() if eid != ent_id
                    ]
                    assert not any(e.isSolid() for e in other_entities)
                    return
        pytest.fail("No ladder found")

    def test_no_deeper_entrance_at_max_depth(self):
        factory = _make_factory()
        for _ in range(20):
            room = factory.createCaveRoom(0, 0, z=-3)
            entities = _entities_in_room(room)
            entrances = [e for e in entities if isinstance(e, CaveEntrance)]
            assert len(entrances) == 0

    def test_cave_background_is_dark(self):
        factory = _make_factory()
        room = factory.createCaveRoom(0, 0, z=-1)
        bg = room.getBackgroundColor()
        assert all(c < 50 for c in bg)


class TestRoomTypeConstant:
    def test_cave_room_type_exists(self):
        assert RoomType.CAVE == "cave"


class TestSurfaceRoomsCaveEntrance:
    def test_mountain_room_entity_types_valid(self):
        factory = _make_factory()
        # mountain rooms should not crash and contain expected entities
        room = factory.createMountainRoom(0, 0)
        entities = _entities_in_room(room)
        assert len(entities) > 0
