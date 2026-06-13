import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

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
