import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from unittest.mock import MagicMock


def _makeWorldScreen(test_config, tmp_path, x=0, y=0, z=0):
    from mapimage.mapImageGenerator import MapImageGenerator
    from screen.worldScreen import WorldScreen

    test_config.pathToSaveDirectory = str(tmp_path)
    # A real generator behind a mock updater: the capture paths are built by
    # the production code that owns the roompngs layout, without starting the
    # updater's background stitching.
    generator = MapImageGenerator(test_config)
    ws = WorldScreen.__new__(WorldScreen)
    ws.mapImageUpdater = MagicMock()
    ws.mapImageUpdater.getRoomImagePath.side_effect = generator.getRoomImagePath
    ws.mapImageUpdater.getRoomImagesDirectoryPath.side_effect = (
        generator.getRoomImagesDirectoryPath
    )
    ws.config = test_config
    ws.currentZ = z
    ws.currentRoom = MagicMock()
    ws.currentRoom.getX.return_value = x
    ws.currentRoom.getY.return_value = y
    ws.player = MagicMock()
    ws.renderer = MagicMock()
    ws.locationWidth = 10
    ws.locationHeight = 10
    ws._pngSavePending = set()
    ws._saveExecutor = MagicMock()
    return ws


def test_surface_capture_keeps_the_legacy_path(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path, x=1, y=2)

    assert ws.getCurrentRoomImagePath() == str(tmp_path) + "/roompngs/1_2.png"


def test_cave_capture_path_carries_the_level(test_config, tmp_path):
    # #557: the cave room at (1, 2, -1) used to write over the surface room's
    # capture at (1, 2), so the stitched map mixed stone and grass.
    ws = _makeWorldScreen(test_config, tmp_path, x=1, y=2, z=-1)

    assert ws.getCurrentRoomImagePath() == str(tmp_path) + "/roompngs/1_2_-1.png"


def test_surface_capture_does_not_count_as_the_cave_capture(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path, x=1, y=2, z=-1)
    (tmp_path / "roompngs").mkdir()
    (tmp_path / "roompngs" / "1_2.png").write_bytes(b"")

    assert ws.isCurrentRoomSavedAsPNG() is False

    (tmp_path / "roompngs" / "1_2_-1.png").write_bytes(b"")

    assert ws.isCurrentRoomSavedAsPNG() is True


def test_pending_capture_on_one_level_does_not_suppress_another(test_config, tmp_path):
    # #557: the pending-write guard keyed on (x, y) alone, so a queued surface
    # write could suppress the cave write at the same coordinates.
    ws = _makeWorldScreen(test_config, tmp_path, x=1, y=2, z=-1)
    ws._pngSavePending.add((1, 2, 0))  # surface capture already queued

    ws.saveCurrentRoomAsPNG()

    assert (1, 2, -1) in ws._pngSavePending
    ws._saveExecutor.submit.assert_called_once()
    submittedPath = ws._saveExecutor.submit.call_args.args[2]
    assert submittedPath.endswith("/roompngs/1_2_-1.png")


def test_capture_is_skipped_while_the_same_level_is_pending(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path, x=1, y=2, z=-1)
    ws._pngSavePending.add((1, 2, -1))

    ws.saveCurrentRoomAsPNG()

    ws._saveExecutor.submit.assert_not_called()
