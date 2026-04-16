from src.world.roomType import RoomType


def test_empty():
    assert RoomType.EMPTY == "empty"


def test_grassland():
    assert RoomType.GRASSLAND == "grassland"


def test_forest():
    assert RoomType.FOREST == "forest"


def test_jungle():
    assert RoomType.JUNGLE == "jungle"


def test_mountain():
    assert RoomType.MOUNTAIN == "mountain"
