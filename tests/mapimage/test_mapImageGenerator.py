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
