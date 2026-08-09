from unittest.mock import MagicMock, patch

from mapimage.mapImageGenerator import MapImageGenerator

# (numRoomsInEachDirection * 2 + 1) * roomSizeInPixels = (5 * 2 + 1) * 100
MAP_SIZE = 1100
# Center offset used by pasteRoomImagesAtCorrectCoordinates:
# int(MAP_SIZE / 2) - int(roomSize / 2) = 550 - 50
CENTER_OFFSET = 500


def _createGenerator(test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    generator = MapImageGenerator(test_config)
    # Replace the real PIL canvas with a mock so paste calls can be asserted
    # without compositing real images.
    generator.mapImage = MagicMock()
    return generator


def _paste(generator, filenames):
    # Image.open is used as a context manager; mock it so no real room image
    # files are required and the resized result is a recognizable sentinel.
    with patch("mapimage.mapImageGenerator.Image.open") as mockOpen:
        contextImage = mockOpen.return_value.__enter__.return_value
        contextImage.resize.return_value = "RESIZED"
        generator.pasteRoomImagesAtCorrectCoordinates(filenames)


def test_map_image_size_in_pixels(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    assert generator.mapImageSizeInPixels == MAP_SIZE


def test_origin_room_pasted_at_center(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    _paste(generator, ["0_0.png"])

    generator.mapImage.paste.assert_called_once_with(
        "RESIZED", (CENTER_OFFSET, CENTER_OFFSET)
    )


def test_offset_room_coordinates(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    _paste(generator, ["1_2.png"])

    # picX = 500 + 1 * 100, picY = 500 + 2 * 100
    generator.mapImage.paste.assert_called_once_with("RESIZED", (600, 700))


def test_negative_room_coordinates_within_bounds(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    _paste(generator, ["-1_-1.png"])

    # picX = 500 - 100, picY = 500 - 100; still inside the map.
    generator.mapImage.paste.assert_called_once_with("RESIZED", (400, 400))


def test_room_at_high_boundary_is_pasted(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    # picX = 500 + 5 * 100 = 1000, which is < MAP_SIZE, so it is in bounds.
    _paste(generator, ["5_0.png"])

    generator.mapImage.paste.assert_called_once_with("RESIZED", (1000, CENTER_OFFSET))


def test_room_past_high_boundary_is_skipped(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    # picX = 500 + 6 * 100 = 1100, which is not < MAP_SIZE -> out of bounds.
    _paste(generator, ["6_0.png"])

    generator.mapImage.paste.assert_not_called()


def test_room_past_low_boundary_is_skipped(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    # picX = 500 - 6 * 100 = -100, which is < 0 -> out of bounds.
    _paste(generator, ["-6_0.png"])

    generator.mapImage.paste.assert_not_called()


def test_cave_room_pastes_at_its_own_coordinates(test_config, tmp_path):
    # The level suffix must not be mistaken for a coordinate: 0_0_-1 is the
    # room at the origin one level down, not a room at (0, 0) shifted by -1.
    generator = _createGenerator(test_config, tmp_path)

    _paste(generator, ["0_0_-1.png"])

    generator.mapImage.paste.assert_called_once_with(
        "RESIZED", (CENTER_OFFSET, CENTER_OFFSET)
    )


def test_unparseable_filenames_are_skipped(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    _paste(generator, ["notaroom.png"])

    generator.mapImage.paste.assert_not_called()


def _writeRoomImageFiles(tmp_path, filenames):
    roompngs = tmp_path / "roompngs"
    roompngs.mkdir(exist_ok=True)
    for filename in filenames:
        (roompngs / filename).write_bytes(b"")
    return roompngs


def test_get_room_images_returns_only_the_requested_level(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)
    _writeRoomImageFiles(tmp_path, ["0_0.png", "1_1.png", "0_0_-1.png", "0_0_-2.png"])

    assert sorted(generator.getRoomImages()) == ["0_0.png", "1_1.png"]
    assert generator.getRoomImages(-1) == ["0_0_-1.png"]
    assert generator.getRoomImages(-2) == ["0_0_-2.png"]


def test_get_levels_with_room_images(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)
    _writeRoomImageFiles(tmp_path, ["0_0.png", "0_0_-2.png", "1_1_-2.png"])

    assert generator.getLevelsWithRoomImages() == [-2, 0]


def test_get_levels_with_room_images_without_a_directory(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    assert generator.getLevelsWithRoomImages() == []


def test_clear_room_images_for_one_level_leaves_the_others(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)
    roompngs = _writeRoomImageFiles(tmp_path, ["0_0.png", "0_0_-1.png"])

    generator.clearRoomImages(-1)

    assert sorted(path.name for path in roompngs.iterdir()) == ["0_0.png"]


def test_clear_room_images_without_a_level_clears_everything(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)
    roompngs = _writeRoomImageFiles(tmp_path, ["0_0.png", "0_0_-1.png"])

    generator.clearRoomImages()

    assert list(roompngs.iterdir()) == []


def test_map_image_path_is_per_level(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    assert generator.getMapImagePath().endswith("/mapImage.png")
    assert generator.getMapImagePath(-1).endswith("/mapImage_z-1.png")


def test_room_image_path_is_per_level(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    assert generator.getRoomImagePath(1, 2).endswith("/roompngs/1_2.png")
    assert generator.getRoomImagePath(1, 2, -1).endswith("/roompngs/1_2_-1.png")


def test_get_existing_map_image_loads_and_returns_copy(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)

    with patch("mapimage.mapImageGenerator.Image.open") as mockOpen:
        contextImage = mockOpen.return_value.__enter__.return_value
        contextImage.copy.return_value = "COPIED"

        result = generator.getExistingMapImage()

    assert result == "COPIED"
    contextImage.load.assert_called_once_with()
    contextImage.copy.assert_called_once_with()


def test_get_existing_map_image_recreates_and_logs_error(test_config, tmp_path):
    generator = _createGenerator(test_config, tmp_path)
    error = OSError("bad png")

    with (
        patch("mapimage.mapImageGenerator.Image.open", side_effect=error),
        patch.object(generator, "createNewMapImage", return_value="NEW") as mockCreate,
        patch("mapimage.mapImageGenerator._logger.warning") as mockWarning,
    ):
        result = generator.getExistingMapImage()

    assert result == "NEW"
    mockCreate.assert_called_once_with()
    mockWarning.assert_called_once_with(
        "map image unreadable, recreating",
        path=generator.getMapImagePath(),
        error=str(error),
    )
