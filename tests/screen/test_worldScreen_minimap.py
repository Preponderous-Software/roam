import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import threading
from unittest.mock import MagicMock

import pygame


def _makeWorldScreen(test_config, tmp_path):
    from screen.worldScreen import WorldScreen

    test_config.pathToSaveDirectory = str(tmp_path)
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = test_config
    ws._cachedMiniMapImage = None
    ws._miniMapLastLoadTick = 0
    ws._miniMapLoadFailed = False
    ws.tickCounter = MagicMock()
    ws.tickCounter.getTick.return_value = 100  # >= 60 so a reload is due
    # Default the renderer to a failing load (tryLoadImage -> None); the failure
    # tests rely on this, the success test overrides ws.renderer.
    ws.renderer = MagicMock()
    ws.renderer.tryLoadImage.return_value = None
    return ws


def _writeCorruptMiniMap(tmp_path):
    (tmp_path / "mapImage.png").write_text("this is not a valid png")


def test_corrupt_minimap_image_is_logged_and_does_not_crash(
    test_config, tmp_path, monkeypatch
):
    ws = _makeWorldScreen(test_config, tmp_path)
    _writeCorruptMiniMap(tmp_path)

    mockLogger = MagicMock()
    monkeypatch.setattr("screen.worldScreen._logger", mockLogger)

    # No cached frame -> the method must return cleanly (not raise) and record
    # the failure exactly once (the bug was that this was swallowed silently).
    result = ws.drawMiniMap()

    assert result is None
    assert ws._miniMapLoadFailed is True
    mockLogger.warning.assert_called_once()
    assert mockLogger.warning.call_args.kwargs["path"].endswith("mapImage.png")


def test_repeated_minimap_load_failure_logs_only_once(
    test_config, tmp_path, monkeypatch
):
    ws = _makeWorldScreen(test_config, tmp_path)
    _writeCorruptMiniMap(tmp_path)

    mockLogger = MagicMock()
    monkeypatch.setattr("screen.worldScreen._logger", mockLogger)

    ws.drawMiniMap()
    ws.drawMiniMap()  # second reload still fails, but must not re-log

    assert mockLogger.warning.call_count == 1


def test_successful_load_resets_failure_flag(test_config, tmp_path, monkeypatch):
    ws = _makeWorldScreen(test_config, tmp_path)
    ws._miniMapLoadFailed = True  # simulate a prior failure streak

    # Write a genuinely loadable image so pygame.image.load succeeds.
    surface = pygame.Surface((4, 4))
    pygame.image.save(surface, str(tmp_path / "mapImage.png"))

    # Stub the post-load drawing so the test stays focused on the flag lifecycle.
    monkeypatch.setattr(
        pygame.transform,
        "scale",
        lambda image, size: MagicMock(get_width=lambda: 10, get_height=lambda: 10),
    )
    ws.minimapScaleFactor = 0.2
    ws.minimapX = 5
    ws.minimapY = 5
    ws.renderer = MagicMock()
    ws.renderer.getGameAreaRect.return_value = MagicMock(width=100)
    ws.hudDragManager = MagicMock()
    ws.hudDragManager.getOffset.return_value = (0, 0)

    ws.drawMiniMap()

    assert ws._miniMapLoadFailed is False


def _makeRoom(x, y):
    room = MagicMock()
    room.getX.return_value = x
    room.getY.return_value = y
    return room


def _makeTextMinimapWorldScreen(test_config, tmp_path, direction=0):
    ws = _makeWorldScreen(test_config, tmp_path)
    ws.currentRoom = _makeRoom(0, 0)
    ws.player = MagicMock()
    ws.player.getDirection.return_value = direction
    ws.map = MagicMock()
    ws.minimapX = 5
    ws.minimapY = 5
    ws.config.dayNightCycleEnabled = False
    ws.dayNightCycle = MagicMock()
    ws.hudDragManager = MagicMock()
    ws.hudDragManager.getOffset.return_value = (0, 0)
    return ws


def test_text_minimap_rows_center_shows_facing_arrow(test_config, tmp_path):
    ws = _makeTextMinimapWorldScreen(test_config, tmp_path, direction=0)
    ws.map.getRooms.return_value = [_makeRoom(0, 0)]

    rows = ws._buildTextMinimapRows()

    # 5x5 grid (radius 2) with the current room at the center showing the
    # up-facing arrow and every other cell unknown.
    assert rows == ["....."] * 2 + ["..^.."] + ["....."] * 2


def test_text_minimap_rows_mark_known_rooms(test_config, tmp_path):
    ws = _makeTextMinimapWorldScreen(test_config, tmp_path, direction=3)
    # Current room plus a known neighbor to the east (x+1).
    ws.map.getRooms.return_value = [_makeRoom(0, 0), _makeRoom(1, 0)]

    rows = ws._buildTextMinimapRows()

    # Center row: current room '>' at center, '#' for the known east neighbor.
    assert rows[2] == "..>#."


def test_draw_text_minimap_renders_label_and_each_grid_row(test_config, tmp_path):
    ws = _makeTextMinimapWorldScreen(test_config, tmp_path)
    ws.map.getRooms.return_value = [_makeRoom(0, 0)]

    ws._drawTextMinimap()

    # One label line + one line per grid row (5) were drawn.
    assert ws.renderer.drawTextLeftAligned.call_count == 6
    ws.renderer.drawRectangle.assert_called_once()


def test_doSave_skips_map_image_update_in_text_mode(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path)
    ws.renderer.supportsImageLoading.return_value = False
    ws.config.showMiniMap = True
    ws.mapImageUpdater = MagicMock()
    ws.stats = MagicMock()
    ws.tickCounter = MagicMock()
    ws.savePlayerLocationToFile = MagicMock()
    ws.savePlayerAttributesToFile = MagicMock()
    ws.savePlayerInventoryToFile = MagicMock()
    ws._saveLock = threading.Lock()
    ws._saveInProgress = True

    ws._doSave(None, str(tmp_path / "room.json"))

    ws.mapImageUpdater.updateMapImage.assert_not_called()


def test_doSave_updates_map_image_in_image_mode(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path)
    ws.renderer.supportsImageLoading.return_value = True
    ws.config.showMiniMap = True
    ws.mapImageUpdater = MagicMock()
    ws.stats = MagicMock()
    ws.tickCounter = MagicMock()
    ws.savePlayerLocationToFile = MagicMock()
    ws.savePlayerAttributesToFile = MagicMock()
    ws.savePlayerInventoryToFile = MagicMock()
    ws._saveLock = threading.Lock()
    ws._saveInProgress = True

    ws._doSave(None, str(tmp_path / "room.json"))

    ws.mapImageUpdater.updateMapImage.assert_called_once()
