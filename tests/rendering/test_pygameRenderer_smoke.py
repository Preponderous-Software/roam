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


def test_all_draw_operations_run_against_a_real_surface(renderer):
    # Drives every drawing/lifecycle method offscreen (SDL dummy). Catches
    # wrapper bugs and surface-API misuse that the logic-only screen tests miss.
    renderer.clearScreen(palette.BLACK)
    renderer.drawRectangle(10, 10, 50, 50, palette.RED)
    renderer.drawText("smoke", 100, 100, 18, palette.WHITE)
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


def test_capture_screenshot_delegates_without_touching_disk(renderer, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        pygameRendererModule,
        "takeScreenshot",
        lambda surface: captured.setdefault("surface", surface),
    )
    renderer.captureScreenshot()
    assert captured["surface"] is renderer.graphik.getGameDisplay()


def test_main_menu_screen_draw_path_runs(renderer):
    # A representative screen draw path exercised end-to-end through the real
    # renderer, confirming the migrated screen code calls the interface correctly.
    config = MagicMock()
    config.getVersion.return_value = "1.2.3"
    updateChecker = MagicMock()
    updateChecker.isUpdateAvailable.return_value = True
    updateChecker.getLatestVersion.return_value = "9.9.9"
    updateChecker.getReleasesUrl.return_value = "https://example.invalid/releases"

    screen = MainMenuScreen(renderer, config, updateChecker)
    renderer.clearScreen(palette.BLACK)
    screen.drawText()
    screen.drawMenuButtons()
    screen.drawUpdateBanner()
    screen.drawVersion()
    renderer.present()
