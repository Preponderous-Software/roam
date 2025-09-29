from src.world.roomType import RoomType


def test_room_type_constants():
    """Test that RoomType constants are defined correctly"""
    assert RoomType.EMPTY == "empty"
    assert RoomType.GRASSLAND == "grassland"
    assert RoomType.FOREST == "forest"
    assert RoomType.JUNGLE == "jungle"
    assert RoomType.MOUNTAIN == "mountain"


def test_room_type_uniqueness():
    """Test that all room type constants are unique"""
    room_types = [
        RoomType.EMPTY,
        RoomType.GRASSLAND,
        RoomType.FOREST,
        RoomType.JUNGLE,
        RoomType.MOUNTAIN
    ]
    
    # Check that all values are unique
    assert len(room_types) == len(set(room_types))
    
    # Check that all are strings
    for room_type in room_types:
        assert isinstance(room_type, str)
        assert len(room_type) > 0