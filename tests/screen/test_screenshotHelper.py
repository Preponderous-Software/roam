import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"

from src.config.config import Config
from src.screen.screenshotHelper import getScreenshotsFolder


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
