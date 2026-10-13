import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame

from src.config.config import Config
from src.rendering import screenshotHelper
from src.rendering.screenshotHelper import getScreenshotsFolder

RED = (255, 0, 0)
BLUE = (0, 0, 255)


def _surfaceWithRedSquare():
    surface = pygame.Surface((6, 4))
    surface.fill(BLUE)
    surface.fill(RED, pygame.Rect(2, 1, 2, 2))
    return surface


def test_screenshots_folder_is_in_user_data_directory(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    assert getScreenshotsFolder() == os.path.join(
        Config.getUserDataDirectory(), "screenshots"
    )


def test_screenshots_folder_uses_appdata_on_windows(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    appData = os.path.join(os.sep, "fake", "AppData", "Roaming")
    monkeypatch.setenv("APPDATA", appData)
    assert getScreenshotsFolder() == os.path.join(appData, "Roam", "screenshots")


def test_screenshots_folder_uses_application_support_on_macos(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr(sys, "platform", "darwin")
    expected = os.path.join(
        os.path.expanduser("~"), "Library", "Application Support", "Roam", "screenshots"
    )
    assert getScreenshotsFolder() == expected


def test_capture_screen_saves_only_the_requested_region(tmp_path):
    path = str(tmp_path / "region.png")

    screenshotHelper.captureScreen(_surfaceWithRedSquare(), path, (2, 1), (2, 2))

    saved = pygame.image.load(path)
    assert saved.get_size() == (2, 2)
    for x in range(2):
        for y in range(2):
            assert saved.get_at((x, y))[:3] == RED


def test_take_screenshot_creates_folder_and_saves_full_display(monkeypatch, tmp_path):
    folder = tmp_path / "shots"
    monkeypatch.setattr(screenshotHelper, "getScreenshotsFolder", lambda: str(folder))

    screenshotHelper.takeScreenshot(_surfaceWithRedSquare())

    files = os.listdir(str(folder))
    assert len(files) == 1
    assert files[0].startswith("screenshot-")
    assert files[0].endswith(".png")
    assert " " not in files[0]
    assert ":" not in files[0]
    saved = pygame.image.load(str(folder / files[0]))
    assert saved.get_size() == (6, 4)
    assert saved.get_at((0, 0))[:3] == BLUE
    assert saved.get_at((2, 1))[:3] == RED


def test_take_screenshot_reuses_existing_folder(monkeypatch, tmp_path):
    folder = tmp_path / "shots"
    folder.mkdir()
    (folder / "keep.txt").write_text("existing")
    monkeypatch.setattr(screenshotHelper, "getScreenshotsFolder", lambda: str(folder))

    screenshotHelper.takeScreenshot(_surfaceWithRedSquare())

    assert sorted(os.listdir(str(folder)))[0] == "keep.txt"
    assert len(os.listdir(str(folder))) == 2
