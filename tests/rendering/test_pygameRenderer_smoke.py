import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from unittest.mock import MagicMock

import pygame
import pytest

from lib.graphik.src.graphik import Graphik
from rendering import pygameRenderer as pygameRendererModule
from rendering.pygameRenderer import PygameRenderer
from screen.mainMenuScreen import MainMenuScreen
from ui import palette

DISPLAY_SIZE = (800, 600)


@pytest.fixture
def renderer():
    pygame.init()
    pygame.font.init()
    display = pygame.display.set_mode(DISPLAY_SIZE)
    yield PygameRenderer(Graphik(display))
    pygame.quit()


def test_display_queries_reflect_the_real_surface(renderer):
    assert renderer.getDisplaySize() == DISPLAY_SIZE
    assert renderer.getDisplayWidth() == DISPLAY_SIZE[0]
    assert renderer.getDisplayHeight() == DISPLAY_SIZE[1]


def test_load_image_loads_a_real_asset_and_caches_by_path(renderer):
    image = renderer.loadImage("assets/images/player_down.png")
    assert image.get_width() > 0 and image.get_height() > 0
    # Same path returns the cached surface instance.
    assert renderer.loadImage("assets/images/player_down.png") is image


def test_load_image_returns_a_placeholder_for_a_missing_asset(renderer):
    placeholder = renderer.loadImage("assets/images/does-not-exist.png")
    assert placeholder.get_size() == (32, 32)
    assert placeholder.get_at((0, 0))[:3] == palette.DEBUG_MAGENTA


def test_scale_image_resizes(renderer):
    image = renderer.loadImage("assets/images/player_down.png")
    scaled = renderer.scaleImage(image, (24, 24))
    assert scaled.get_size() == (24, 24)


def test_all_draw_operations_run_against_a_real_surface(renderer):
    # Drives every drawing/lifecycle method offscreen (SDL dummy). Catches
    # wrapper bugs and surface-API misuse that the logic-only screen tests miss.
    renderer.clearScreen(palette.BLACK)
    renderer.drawRectangle(10, 10, 50, 50, palette.RED)
    renderer.drawText("smoke", 100, 100, 18, palette.WHITE)
    renderer.drawTextLeftAligned("left", 20, 120, 18, palette.WHITE)
    renderer.drawTranslucentOverlay((0, 0, 0, 120))
    renderer.drawButton(
        10, 10, 80, 30, palette.WHITE, palette.BLACK, 16, "Ok", lambda: None
    )
    sprite = pygame.Surface((16, 16))
    renderer.drawImage(sprite, (20, 20))
    renderer.drawImage(sprite, pygame.Rect(30, 30, 16, 16))
    renderer.setClipRegion(pygame.Rect(0, 0, 40, 40))
    renderer.setClipRegion(None)
    renderer.setCaption("Roam smoke")
    assert renderer.getGameAreaRect() is not None
    renderer.present()


def test_create_save_and_load_image_round_trip(renderer, tmp_path):
    # createSurface -> saveImage -> tryLoadImage round-trips a surface to disk
    # and back (the room-PNG / minimap path).
    surface = renderer.createSurface((8, 8))
    assert surface.get_size() == (8, 8)
    path = str(tmp_path / "roundtrip.png")
    renderer.saveImage(surface, path)
    assert os.path.isfile(path)
    loaded = renderer.tryLoadImage(path)
    assert loaded is not None and loaded.get_size() == (8, 8)


def test_try_load_image_returns_none_for_missing_or_unreadable(renderer, tmp_path):
    assert renderer.tryLoadImage(str(tmp_path / "does-not-exist.png")) is None
    corrupt = tmp_path / "corrupt.png"
    corrupt.write_text("not a real png")
    assert renderer.tryLoadImage(str(corrupt)) is None


def test_capture_screenshot_delegates_without_touching_disk(renderer, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        pygameRendererModule,
        "takeScreenshot",
        lambda surface: captured.setdefault("surface", surface),
    )
    renderer.captureScreenshot()
    assert captured["surface"] is renderer.graphik.getGameDisplay()


def test_render_target_redirects_drawing_offscreen_and_restores(renderer):
    # worldScreen.saveCurrentRoomAsPNG relies on this: drawing must land on the
    # offscreen target while it is set, and the display must be restored after.
    windowTarget = renderer.getRenderTarget()
    offscreen = pygame.Surface((40, 40))

    renderer.setRenderTarget(offscreen)
    assert renderer.getRenderTarget() is offscreen
    renderer.clearScreen((10, 20, 30))
    assert offscreen.get_at((5, 5))[:3] == (10, 20, 30)
    # The real window surface was not painted while redirected.
    assert windowTarget.get_at((5, 5))[:3] != (10, 20, 30)

    renderer.setRenderTarget(windowTarget)
    assert renderer.getRenderTarget() is windowTarget


def test_main_menu_screen_draw_path_runs(renderer):
    # A representative screen draw path exercised end-to-end through the real
    # renderer, confirming the migrated screen code calls the interface correctly.
    config = MagicMock()
    config.getVersion.return_value = "1.2.3"
    updateChecker = MagicMock()
    updateChecker.isUpdateAvailable.return_value = True
    updateChecker.getLatestVersion.return_value = "9.9.9"
    updateChecker.getReleasesUrl.return_value = "https://example.invalid/releases"

    inputSource = MagicMock()
    inputSource.getMousePosition.return_value = (0, 0)
    inputSource.getMouseButtons.return_value = (False, False, False)
    screen = MainMenuScreen(renderer, inputSource, config, updateChecker)
    renderer.clearScreen(palette.BLACK)
    screen.drawText()
    screen.drawMenuButtons()
    screen.drawUpdateBanner()
    screen.drawVersion()
    renderer.present()
