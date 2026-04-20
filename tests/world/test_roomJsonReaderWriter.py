from uuid import uuid4
import pytest
from entity.apple import Apple
from entity.banana import Banana
from entity.bearMeat import BearMeat
from entity.bed import Bed
from entity.campfire import Campfire
from entity.chickenMeat import ChickenMeat
from entity.coalOre import CoalOre
from entity.excrement import Excrement
from entity.fence import Fence
from entity.grass import Grass
from entity.ironOre import IronOre
from entity.jungleWood import JungleWood
from entity.leaves import Leaves
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.matureCrop import MatureCrop
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.stoneBed import StoneBed
from entity.stoneFloor import StoneFloor
from entity.wheat import Wheat
from entity.wheatSeed import WheatSeed
from entity.woodFloor import WoodFloor
from entity.youngCrop import YoungCrop
from world.roomJsonReaderWriter import RoomJsonReaderWriter


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
    if entityClass in ["Bear", "Chicken"]:
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
        ("Excrement", Excrement),
        ("WheatSeed", WheatSeed),
        ("Wheat", Wheat),
        ("YoungCrop", YoungCrop),
        ("MatureCrop", MatureCrop),
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


def test_generate_json_for_young_crop_includes_tick_planted(resolve, test_config, tmp_path):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    crop = YoungCrop(300)

    entityJson = roomJsonReaderWriter.generateJsonForEntity(crop)

    assert entityJson["entityClass"] == "YoungCrop"
    assert entityJson["tickPlanted"] == 300


def test_generate_json_for_mature_crop_includes_tick_planted(resolve, test_config, tmp_path):
    roomJsonReaderWriter = createRoomJsonReaderWriter(resolve, test_config, tmp_path)
    crop = MatureCrop(400)

    entityJson = roomJsonReaderWriter.generateJsonForEntity(crop)

    assert entityJson["entityClass"] == "MatureCrop"
    assert entityJson["tickPlanted"] == 400
