import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import threading
from unittest.mock import MagicMock

import pygame

from config.keyBindings import KeyBindings
from rendering.keyCode import KeyCode


def _makeMapImageUpdater(test_config):
    """A real MapImageUpdater over a mock generator's paths would defeat the
    point, so give the screen a real generator behind a mock updater: the path
    helpers are exercised for real, the background stitching is not."""
    from mapimage.mapImageGenerator import MapImageGenerator

    generator = MapImageGenerator(test_config)
    updater = MagicMock()
    updater.getMapImagePath.side_effect = generator.getMapImagePath
    updater.getRoomImagePath.side_effect = generator.getRoomImagePath
    updater.getRoomImagesDirectoryPath.side_effect = (
        generator.getRoomImagesDirectoryPath
    )
    return updater


def _makeWorldScreen(test_config, tmp_path):
    from screen.worldScreen import WorldScreen

    test_config.pathToSaveDirectory = str(tmp_path)
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = test_config
    ws._cachedMiniMapImage = None
    ws._miniMapLastLoadTick = 0
    ws._miniMapCachedZ = 0
    ws._miniMapLoadFailed = False
    ws._miniMapViewZ = None
    ws.currentZ = 0
    ws.tickCounter = MagicMock()
    ws.tickCounter.getTick.return_value = 100  # >= 60 so a reload is due
    # Default the renderer to a failing load (tryLoadImage -> None); the failure
    # tests rely on this, the success test overrides ws.renderer.
    ws.renderer = MagicMock()
    ws.renderer.tryLoadImage.return_value = None
    ws.mapImageUpdater = _makeMapImageUpdater(test_config)
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


def _makeRoom(x, y, z=0):
    room = MagicMock()
    room.getX.return_value = x
    room.getY.return_value = y
    room.getZ.return_value = z
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


def test_text_minimap_rows_ignore_rooms_on_other_levels(test_config, tmp_path):
    # #557: visiting the cave room at (1, 0, -1) used to mark the surface room
    # at (1, 0) as explored, because the known-room set had no z filter.
    ws = _makeTextMinimapWorldScreen(test_config, tmp_path, direction=3)
    ws.map.getRooms.return_value = [_makeRoom(0, 0), _makeRoom(1, 0, z=-1)]

    rows = ws._buildTextMinimapRows()

    assert rows[2] == "..>.."


def test_text_minimap_rows_show_rooms_on_the_current_level_underground(
    test_config, tmp_path
):
    ws = _makeTextMinimapWorldScreen(test_config, tmp_path, direction=3)
    ws.currentZ = -1
    # The surface neighbour is hidden; the cave neighbour on this level shows.
    ws.map.getRooms.return_value = [
        _makeRoom(0, 0, z=-1),
        _makeRoom(1, 0),
        _makeRoom(0, 1, z=-1),
    ]

    rows = ws._buildTextMinimapRows()

    assert rows[2] == "..>.."
    assert rows[3] == "..#.."


def test_minimap_loads_the_current_levels_map_image(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path)
    ws.currentZ = -1
    ws._miniMapCachedZ = -1
    (tmp_path / "mapImage_z-1.png").write_text("not a valid png")

    ws.drawMiniMap()

    assert ws.renderer.tryLoadImage.call_args.args[0].endswith("mapImage_z-1.png")


def test_changing_level_drops_the_cached_minimap_image(test_config, tmp_path):
    # #557: without invalidation the surface map kept being drawn underground,
    # because the cached surface is only reloaded every 60 ticks.
    ws = _makeWorldScreen(test_config, tmp_path)
    ws._cachedMiniMapImage = "SURFACE"
    ws._miniMapLoadFailed = True
    ws._miniMapLastLoadTick = 100  # inside the reload window
    ws.currentZ = -1  # descended since the cache was filled

    # No mapImage_z-1.png exists yet, so the draw bails out; what matters is
    # that the stale surface frame was discarded rather than reused.
    ws.drawMiniMap()

    assert ws._cachedMiniMapImage is None
    assert ws._miniMapCachedZ == -1
    assert ws._miniMapLoadFailed is False


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


# --- Paging the minimap through levels the player is not standing on (#559) ---


def _makePagingWorldScreen(test_config, tmp_path, currentZ=0):
    """A world screen wired for the level-paging keys: real key bindings, a
    mock status bar, and the minimap switched on."""
    ws = _makeTextMinimapWorldScreen(test_config, tmp_path)
    ws.currentZ = currentZ
    ws._miniMapCachedZ = currentZ
    ws.keyBindings = KeyBindings()
    ws.status = MagicMock()
    ws.config.showMiniMap = True
    ws.map.getRooms.return_value = [_makeRoom(0, 0)]
    return ws


def test_display_level_follows_the_player_until_paged(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path, currentZ=-2)

    assert ws.getMiniMapDisplayZ() == -2


def test_paging_down_shows_the_level_below_without_moving_the_player(
    test_config, tmp_path
):
    ws = _makePagingWorldScreen(test_config, tmp_path)

    ws._handleUtilityKey(KeyCode.PAGEDOWN, ws.keyBindings)

    assert ws.getMiniMapDisplayZ() == -1
    assert ws.currentZ == 0
    assert "cave level 1" in ws.status.set.call_args.args[0]


def test_alt_paging_keys_are_reachable_from_a_terminal(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path)

    ws._handleUtilityKey(KeyCode.PERIOD, ws.keyBindings)
    assert ws.getMiniMapDisplayZ() == -1

    ws._handleUtilityKey(KeyCode.COMMA, ws.keyBindings)
    assert ws.getMiniMapDisplayZ() == 0

    ws._handleUtilityKey(KeyCode.PERIOD, ws.keyBindings)
    ws._handleUtilityKey(KeyCode.SLASH, ws.keyBindings)
    assert ws.getMiniMapDisplayZ() == 0


def test_paging_stops_at_the_surface(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path)

    ws._handleUtilityKey(KeyCode.PAGEUP, ws.keyBindings)

    assert ws.getMiniMapDisplayZ() == 0
    ws.status.set.assert_called_with("Map already at the surface")


def test_paging_stops_at_the_deepest_level(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path, currentZ=-3)

    ws._handleUtilityKey(KeyCode.PAGEDOWN, ws.keyBindings)

    assert ws.getMiniMapDisplayZ() == -3
    ws.status.set.assert_called_with("Map already at cave level 3")


def test_reset_key_returns_to_the_players_level_in_one_press(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path, currentZ=-3)
    ws._miniMapViewZ = 0

    ws._handleUtilityKey(KeyCode.HOME, ws.keyBindings)

    assert ws.getMiniMapDisplayZ() == -3
    assert ws._miniMapViewZ is None


def test_paging_keys_do_nothing_while_the_minimap_is_hidden(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path)
    ws.config.showMiniMap = False

    ws._handleUtilityKey(KeyCode.PAGEDOWN, ws.keyBindings)

    assert ws._miniMapViewZ is None
    ws.status.set.assert_called_with("Minimap is off")


def test_hiding_the_minimap_forgets_the_paged_level(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path)
    ws._miniMapViewZ = -2

    ws._handleUtilityKey(KeyCode.M, ws.keyBindings)

    assert ws.config.showMiniMap is False
    assert ws._miniMapViewZ is None


def _wireLevelChange(ws):
    ws.currentRoom = MagicMock()
    ws._loadOrGenerateRoom = MagicMock()
    ws._placePlayerAtCaveEntry = MagicMock()
    ws.initializeLocationWidthAndHeight = MagicMock()
    ws.roomPreloader = MagicMock()
    ws.discoverEntitiesInRoom = MagicMock()
    ws.save = MagicMock()


def test_descending_forgets_the_paged_level(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path)
    ws._miniMapViewZ = -3
    _wireLevelChange(ws)

    ws._descend()

    assert ws.currentZ == -1
    assert ws._miniMapViewZ is None
    assert ws.getMiniMapDisplayZ() == -1


def test_ascending_forgets_the_paged_level(test_config, tmp_path):
    ws = _makePagingWorldScreen(test_config, tmp_path, currentZ=-2)
    ws._miniMapViewZ = -3
    _wireLevelChange(ws)

    ws._ascend()

    assert ws.currentZ == -1
    assert ws._miniMapViewZ is None


def test_minimap_loads_the_paged_levels_map_image(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path)
    ws._miniMapViewZ = -2
    (tmp_path / "mapImage_z-2.png").write_text("not a valid png")

    ws.drawMiniMap()

    assert ws.renderer.tryLoadImage.call_args.args[0].endswith("mapImage_z-2.png")
    assert ws._miniMapCachedZ == -2


def test_paging_to_a_level_with_no_map_draws_an_unexplored_panel(test_config, tmp_path):
    ws = _makeWorldScreen(test_config, tmp_path)
    ws.keyBindings = KeyBindings()
    ws._miniMapViewZ = -2  # no mapImage_z-2.png on disk
    ws.minimapScaleFactor = 0.2
    ws.minimapX = 5
    ws.minimapY = 5
    ws.renderer.getGameAreaRect.return_value = MagicMock(width=100)
    ws.hudDragManager = MagicMock()
    ws.hudDragManager.getOffset.return_value = (0, 0)

    ws.drawMiniMap()

    drawnText = [
        call.args[0] for call in ws.renderer.drawTextLeftAligned.call_args_list
    ]
    assert any("unexplored" in text for text in drawnText)
    assert any("Viewing cave level 2" in text for text in drawnText)


def test_text_minimap_rows_show_the_paged_levels_rooms(test_config, tmp_path):
    ws = _makeTextMinimapWorldScreen(test_config, tmp_path, direction=3)
    ws._miniMapViewZ = -1
    ws.map.getRooms.return_value = [
        _makeRoom(0, 0),
        _makeRoom(1, 0),
        _makeRoom(0, 1, z=-1),
    ]

    rows = ws._buildTextMinimapRows()

    # The player is not on the paged-to level, so the center cell marks their
    # column rather than their facing, and only that level's rooms are known.
    assert rows[2] == "..+.."
    assert rows[3] == "..#.."


def test_text_minimap_labels_a_paged_level(test_config, tmp_path):
    ws = _makeTextMinimapWorldScreen(test_config, tmp_path)
    ws.keyBindings = KeyBindings()
    ws.renderer.supportsImageLoading.return_value = False
    ws._miniMapViewZ = -1
    ws.map.getRooms.return_value = [_makeRoom(0, 0, z=-1)]

    ws._drawTextMinimap()

    drawnText = [
        call.args[0] for call in ws.renderer.drawTextLeftAligned.call_args_list
    ]
    # Room label + the "not your level" caption + one line per grid row.
    assert len(drawnText) == 7
    assert "Viewing cave level 1 — / to return" in drawnText
