from mapimage.mapImagePaths import (
    getMapImageFilename,
    getRoomImageFilename,
    parseRoomImageFilename,
)


def test_surface_map_image_keeps_the_legacy_name():
    # Saves made before per-level maps existed hold a flat mapImage.png, which
    # must keep working as the surface map.
    assert getMapImageFilename(0) == "mapImage.png"
    assert getMapImageFilename() == "mapImage.png"


def test_cave_levels_get_their_own_map_image():
    assert getMapImageFilename(-1) == "mapImage_z-1.png"
    assert getMapImageFilename(-3) == "mapImage_z-3.png"


def test_surface_room_image_keeps_the_legacy_name():
    assert getRoomImageFilename(0, 0) == "0_0.png"
    assert getRoomImageFilename(-1, 2, 0) == "-1_2.png"


def test_cave_room_image_carries_the_level():
    assert getRoomImageFilename(0, 0, -1) == "0_0_-1.png"
    assert getRoomImageFilename(-1, 2, -3) == "-1_2_-3.png"


def test_round_trip_through_the_parser():
    for x, y, z in [(0, 0, 0), (-1, 2, 0), (3, -4, -1), (-5, -6, -3)]:
        assert parseRoomImageFilename(getRoomImageFilename(x, y, z)) == (x, y, z)


def test_unsuffixed_names_parse_as_surface():
    assert parseRoomImageFilename("2_-3.png") == (2, -3, 0)


def test_non_room_filenames_are_rejected():
    assert parseRoomImageFilename("mapImage.png") is None
    assert parseRoomImageFilename("0_0_-1_extra.png") is None
    assert parseRoomImageFilename("a_b.png") is None
    assert parseRoomImageFilename("0_0_x.png") is None
