import json
from unittest.mock import MagicMock
from uuid import uuid4

import jsonschema
import pytest
from entity.apple import Apple
from entity.banana import Banana
from entity.bearMeat import BearMeat
from entity.bed import Bed
from entity.campfire import Campfire
from entity.chest import Chest
from entity.chickenMeat import ChickenMeat
from entity.coalOre import CoalOre
from entity.excrement import Excrement
from entity.fence import Fence
from entity.grass import Grass
from entity.gravestone import Gravestone
from entity.ironOre import IronOre
from entity.jungleWood import JungleWood
from entity.leaves import Leaves
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.deer import Deer
from entity.living.rabbit import Rabbit
from entity.living.snake import Snake
from entity.living.wolf import Wolf
from entity.matureCrop import MatureCrop
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.stoneBed import StoneBed
from entity.stoneFloor import StoneFloor
from entity.wheat import Wheat
from entity.wheatSeed import WheatSeed
from entity.woodFloor import WoodFloor
from entity.youngCrop import YoungCrop
from world import roomJsonReaderWriter as roomJsonReaderWriterModule
from world.room import Room
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.roomType import RoomType


def createRoomJsonReaderWriter(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    test_config.gridSize = 3
    return resolve(RoomJsonReaderWriter)


def createEntityJson(entityClass):
    entityJson = {
        "id": str(uuid4()),
        "entityClass": entityClass,
        "name": entityClass,
        "environmentId": str(uuid4()),
        "gridId": str(uuid4()),
        "locationId": str(uuid4()),
    }
    if entityClass in ["Apple", "Banana", "ChickenMeat", "BearMeat", "Wheat"]:
        entityJson["energy"] = 25
    if entityClass in ["Bear", "Chicken", "Deer", "Rabbit", "Snake", "Wolf"]:
        entityJson["energy"] = 80
        entityJson["tickCreated"] = 100
        entityJson["tickLastReproduced"] = 200
        entityJson["imagePath"] = "assets/images/test.png"
    if entityClass == "Excrement":
        entityJson["tickCreated"] = 100
    if entityClass in ["YoungCrop", "MatureCrop"]:
        entityJson["tickPlanted"] = 100
    return entityJson


@pytest.mark.parametrize(
    "entityClass, expectedType",
    [
        ("Apple", Apple),
        ("CoalOre", CoalOre),
        ("Grass", Grass),
        ("IronOre", IronOre),
        ("JungleWood", JungleWood),
        ("Leaves", Leaves),
        ("OakWood", OakWood),
        ("Stone", Stone),
        ("Banana", Banana),
        ("ChickenMeat", ChickenMeat),
        ("BearMeat", BearMeat),
        ("WoodFloor", WoodFloor),
        ("Bed", Bed),
        ("StoneFloor", StoneFloor),
        ("StoneBed", StoneBed),
        ("Fence", Fence),
        ("Campfire", Campfire),
        ("Bear", Bear),
        ("Chicken", Chicken),
        ("Deer", Deer),
        ("Rabbit", Rabbit),
        ("Snake", Snake),
        ("Wolf", Wolf),
        ("Excrement", Excrement),
        ("WheatSeed", WheatSeed),
        ("Wheat", Wheat),
        ("YoungCrop", YoungCrop),
        ("MatureCrop", MatureCrop),
        ("Gravestone", Gravestone),
        ("Chest", Chest),
    ],
)
def test_generate_entity_from_json_supports_all_known_entity_classes(
    entityClass, expectedType, resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)

    entity = roomJsonReaderWriter.generateEntityFromJson(createEntityJson(entityClass))

    assert isinstance(entity, expectedType)


def test_generate_entity_from_json_returns_none_for_player_entity(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)

    entity = roomJsonReaderWriter.generateEntityFromJson(createEntityJson("Player"))

    assert entity is None


def test_generate_entity_from_json_raises_value_error_for_unknown_entity_class(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)

    with pytest.raises(ValueError, match="Unknown entity class: UnknownEntity"):
        roomJsonReaderWriter.generateEntityFromJson(createEntityJson("UnknownEntity"))


def test_generate_room_from_json_parses_background_color_string(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    roomJson = {
        "backgroundColor": "(15, 30, 45)",
        "x": 4,
        "y": 7,
        "name": "Room 4-7",
        "id": str(uuid4()),
        "grid": {
            "id": str(uuid4()),
            "columns": 3,
            "rows": 3,
            "locations": [],
        },
    }

    room = roomJsonReaderWriter.generateRoomFromJson(roomJson)

    assert room.getBackgroundColor() == (15, 30, 45)


def createLegacyRoomJson():
    # A room file as written before roomType was persisted: no roomType key.
    stoneJson = createEntityJson("Stone")
    stoneJson["creationDate"] = "2026-01-01 00:00:00"
    return {
        "backgroundColor": "(15, 30, 45)",
        "x": 4,
        "y": 7,
        "z": -1,
        "name": "Room 4-7",
        "id": str(uuid4()),
        "livingEntityIds": [],
        "grid": {
            "id": str(uuid4()),
            "columns": 3,
            "rows": 3,
            "locations": [
                {
                    "id": str(uuid4()),
                    "x": 0,
                    "y": 0,
                    "entities": [stoneJson],
                }
            ],
        },
        "creationDate": "2026-01-01 00:00:00",
    }


def test_room_from_legacy_save_loads_with_no_room_type(resolve, test_config, tmp_path):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    roomJson = createLegacyRoomJson()

    jsonschema.validate(roomJson, roomJsonReaderWriter.roomSchema)
    room = roomJsonReaderWriter.generateRoomFromJson(roomJson)

    assert room.getRoomType() is None
    assert (room.getX(), room.getY(), room.getZ()) == (4, 7, -1)
    assert str(room.getGrid().getID()) == roomJson["grid"]["id"]
    entities = [
        entity
        for location in room.getGrid().getLocations().values()
        for entity in location.getEntities().values()
    ]
    assert [type(entity) for entity in entities] == [Stone]


def test_room_from_legacy_save_resaves_without_inventing_room_type(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    room = roomJsonReaderWriter.generateRoomFromJson(createLegacyRoomJson())

    roomJson = roomJsonReaderWriter.generateJsonForRoom(room)

    assert "roomType" not in roomJson


@pytest.mark.parametrize(
    "roomType",
    [
        RoomType.EMPTY,
        RoomType.GRASSLAND,
        RoomType.FOREST,
        RoomType.JUNGLE,
        RoomType.MOUNTAIN,
        RoomType.CAVE,
    ],
)
def test_room_type_round_trips_through_save(roomType, resolve, test_config, tmp_path):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    room = Room("Room 2-3", 3, (1, 2, 3), 2, 3, MagicMock())
    room.setRoomType(roomType)

    # generateJsonForRoom validates against schemas/room.json itself.
    roomJson = roomJsonReaderWriter.generateJsonForRoom(room)
    restored = roomJsonReaderWriter.generateRoomFromJson(roomJson)

    assert roomJson["roomType"] == roomType
    assert restored.getRoomType() == roomType


def test_room_with_unrecognised_room_type_still_loads(resolve, test_config, tmp_path):
    # A save written by a later version may carry a type this build lacks.
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    roomJson = createLegacyRoomJson()
    roomJson["roomType"] = "volcano"

    jsonschema.validate(roomJson, roomJsonReaderWriter.roomSchema)
    room = roomJsonReaderWriter.generateRoomFromJson(roomJson)

    assert room.getRoomType() == "volcano"


def test_room_loader_ignores_unknown_keys(resolve, test_config, tmp_path):
    # What an older build sees when it opens a file written by a newer one.
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    roomJson = createLegacyRoomJson()
    roomJson["someFutureField"] = {"anything": 1}

    room = roomJsonReaderWriter.generateRoomFromJson(roomJson)

    assert room.getName() == "Room 4-7"


def test_player_location_schema_accepts_room_z():
    with open("schemas/playerLocation.json", encoding="utf-8") as schemaFile:
        schema = json.load(schemaFile)

    jsonschema.validate(
        {"roomX": 0, "roomY": 0, "roomZ": -2, "locationId": "abc"}, schema
    )
    jsonschema.validate({"roomX": 0, "roomY": 0, "locationId": "abc"}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"roomX": 0, "roomY": 0, "roomZ": "deep"}, schema)


def test_young_crop_preserves_tick_planted(resolve, test_config, tmp_path):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    entityJson = createEntityJson("YoungCrop")
    entityJson["tickPlanted"] = 500

    entity = roomJsonReaderWriter.generateEntityFromJson(entityJson)

    assert isinstance(entity, YoungCrop)
    assert entity.getTickPlanted() == 500


def test_mature_crop_preserves_tick_planted(resolve, test_config, tmp_path):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    entityJson = createEntityJson("MatureCrop")
    entityJson["tickPlanted"] = 750

    entity = roomJsonReaderWriter.generateEntityFromJson(entityJson)

    assert isinstance(entity, MatureCrop)
    assert entity.getTickPlanted() == 750


def test_generate_json_for_young_crop_includes_tick_planted(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    crop = YoungCrop(300)

    entityJson = roomJsonReaderWriter.generateJsonForEntity(crop)

    assert entityJson["entityClass"] == "YoungCrop"
    assert entityJson["tickPlanted"] == 300


def test_generate_json_for_mature_crop_includes_tick_planted(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    crop = MatureCrop(400)

    entityJson = roomJsonReaderWriter.generateJsonForEntity(crop)

    assert entityJson["entityClass"] == "MatureCrop"
    assert entityJson["tickPlanted"] == 400


def test_generate_json_for_gravestone_includes_stored_inventory(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    gravestone = Gravestone()
    gravestone.setEnvironmentID(uuid4())
    gravestone.setGridID(uuid4())
    gravestone.setLocationID(str(uuid4()))
    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())

    entityJson = roomJsonReaderWriter.generateJsonForEntity(gravestone)

    assert entityJson["entityClass"] == "Gravestone"
    assert "storedInventory" in entityJson
    slots = entityJson["storedInventory"]["inventorySlots"]
    total_items = sum(len(s["slotContents"]) for s in slots)
    assert total_items == 1


def test_generate_entity_from_json_restores_gravestone_stored_inventory(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)

    apple = Apple()
    gravestoneJson = {
        "id": str(uuid4()),
        "entityClass": "Gravestone",
        "name": "Gravestone",
        "creationDate": "2026-01-01",
        "environmentId": str(uuid4()),
        "gridId": str(uuid4()),
        "locationId": str(uuid4()),
        "storedInventory": {
            "inventorySlots": [
                {
                    "slotIndex": 0,
                    "slotContents": [
                        {
                            "entityId": str(apple.getID()),
                            "entityClass": "Apple",
                            "name": "Apple",
                            "assetPath": "assets/images/apple.png",
                            "energy": 25,
                        }
                    ],
                }
            ]
        },
    }

    entity = roomJsonReaderWriter.generateEntityFromJson(gravestoneJson)

    assert isinstance(entity, Gravestone)
    assert entity.getStoredInventory().getNumItems() == 1


def test_gravestone_round_trip_preserves_stored_items(resolve, test_config, tmp_path):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    gravestone = Gravestone()
    gravestone.setEnvironmentID(uuid4())
    gravestone.setGridID(uuid4())
    gravestone.setLocationID(str(uuid4()))
    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(OakWood())

    entityJson = roomJsonReaderWriter.generateJsonForEntity(gravestone)
    restored = roomJsonReaderWriter.generateEntityFromJson(entityJson)

    assert isinstance(restored, Gravestone)
    assert restored.getStoredInventory().getNumItems() == 2


def test_generate_json_for_chest_includes_stored_inventory(
    resolve, test_config, tmp_path
):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    chest = Chest()
    chest.setEnvironmentID(uuid4())
    chest.setGridID(uuid4())
    chest.setLocationID(str(uuid4()))
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())

    entityJson = roomJsonReaderWriter.generateJsonForEntity(chest)

    assert entityJson["entityClass"] == "Chest"
    assert "storedInventory" in entityJson
    slots = entityJson["storedInventory"]["inventorySlots"]
    total_items = sum(len(s["slotContents"]) for s in slots)
    assert total_items == 1


def test_chest_round_trip_preserves_stored_items(resolve, test_config, tmp_path):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    chest = Chest()
    chest.setEnvironmentID(uuid4())
    chest.setGridID(uuid4())
    chest.setLocationID(str(uuid4()))
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(Apple())
    chest.getStoredInventory().placeIntoFirstAvailableInventorySlot(OakWood())

    entityJson = roomJsonReaderWriter.generateJsonForEntity(chest)
    restored = roomJsonReaderWriter.generateEntityFromJson(entityJson)

    assert isinstance(restored, Chest)
    assert restored.getStoredInventory().getNumItems() == 2


def test_chest_round_trip_preserves_stored_slot_positions(
    resolve, test_config, tmp_path
):
    # A chest packed with gaps must come back packed the same way, not
    # re-collapsed onto the first free slots.
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    chest = Chest()
    chest.setEnvironmentID(uuid4())
    chest.setGridID(uuid4())
    chest.setLocationID(str(uuid4()))
    # Arranged through the slots directly rather than via placeIntoSlot, so the
    # assertion measures the restore path alone.
    chest.getStoredInventory().getInventorySlots()[5].add(Apple())
    chest.getStoredInventory().getInventorySlots()[12].add(OakWood())

    entityJson = roomJsonReaderWriter.generateJsonForEntity(chest)
    restored = roomJsonReaderWriter.generateEntityFromJson(entityJson)

    slots = restored.getStoredInventory().getInventorySlots()
    occupied = {index for index, slot in enumerate(slots) if not slot.isEmpty()}
    assert occupied == {5, 12}
    assert isinstance(slots[5].getContents()[0], Apple)
    assert isinstance(slots[12].getContents()[0], OakWood)


def test_stored_inventory_restore_failure_logs_structured_fields(
    resolve, test_config, tmp_path, monkeypatch
):
    # structlog is configured without PositionalArgumentsFormatter, so a
    # printf-style message would be emitted with its %s placeholders intact.
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)

    class RefusingInventory:
        def placeIntoSlot(self, index, item):
            return False

        def placeIntoFirstAvailableInventorySlot(self, item):
            return False

    class RecordingLogger:
        def __init__(self):
            self.calls = []

        def error(self, event, *args, **kwargs):
            self.calls.append({"event": event, "args": args, "kwargs": kwargs})

    recordingLogger = RecordingLogger()
    monkeypatch.setattr(roomJsonReaderWriterModule, "_logger", recordingLogger)

    apple = Apple()
    roomJsonReaderWriter._restoreStoredInventory(
        RefusingInventory(),
        {
            "inventorySlots": [
                {
                    "slotIndex": 6,
                    "slotContents": [
                        {
                            "entityId": str(apple.getID()),
                            "entityClass": "Apple",
                            "name": "Apple",
                            "assetPath": "assets/images/apple.png",
                            "energy": 25,
                        }
                    ],
                }
            ]
        },
    )

    assert len(recordingLogger.calls) == 1
    recorded = recordingLogger.calls[0]
    assert "%s" not in recorded["event"]
    assert recorded["args"] == ()
    assert recorded["kwargs"]["entityClass"] == "Apple"
    assert recorded["kwargs"]["entityId"] == str(apple.getID())
    assert recorded["kwargs"]["slotIndex"] == 6
