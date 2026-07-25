import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from unittest.mock import MagicMock

import pygame
import pytest

from roam import _shouldUseTextMode


def test_text_flag_forces_text_mode():
    assert _shouldUseTextMode(["roam.py", "--text"]) is True


def test_no_flag_with_dummy_driver_selects_text_mode():
    # SDL_VIDEODRIVER=dummy is set at module level above; display.init()
    # will pick the dummy driver and _shouldUseTextMode must return True.
    assert _shouldUseTextMode(["roam.py"]) is True


def test_text_flag_takes_precedence_over_other_args():
    assert _shouldUseTextMode(["roam.py", "--selftest", "--text"]) is True


def test_display_init_failure_falls_back_to_text_mode(monkeypatch):
    import pygame as pg

    monkeypatch.setattr(
        pg.display, "init", lambda: (_ for _ in ()).throw(pg.error("no display"))
    )
    assert _shouldUseTextMode(["roam.py"]) is True


def _makeRoam(supportsImageLoading):
    from roam import Roam

    roamInstance = Roam.__new__(Roam)
    roamInstance.renderer = MagicMock()
    roamInstance.renderer.supportsImageLoading.return_value = supportsImageLoading
    roamInstance.renderer.getDisplaySize.return_value = (1024, 768)
    roamInstance.config = MagicMock()
    roamInstance.worldScreen = MagicMock()
    roamInstance.frontend = MagicMock()
    roamInstance.currentScreen = MagicMock()
    return roamInstance


def test_quit_saves_hud_layout_in_pygame_mode():
    roamInstance = _makeRoam(True)

    with pytest.raises(SystemExit):
        roamInstance.quitApplication()

    roamInstance.worldScreen.hudDragManager.save.assert_called_once_with(
        roamInstance.config
    )


def test_quit_does_not_save_hud_layout_in_text_mode():
    roamInstance = _makeRoam(False)

    with pytest.raises(SystemExit):
        roamInstance.quitApplication()

    roamInstance.worldScreen.hudDragManager.save.assert_not_called()


def test_returning_to_main_menu_saves_hud_layout_in_pygame_mode():
    from screen.screenType import ScreenType

    roamInstance = _makeRoam(True)
    roamInstance.currentScreen.run.return_value = ScreenType.MAIN_MENU_SCREEN

    assert roamInstance.run() == "restart"

    roamInstance.worldScreen.hudDragManager.save.assert_called_once_with(
        roamInstance.config
    )


def test_returning_to_main_menu_does_not_save_hud_layout_in_text_mode():
    from screen.screenType import ScreenType

    roamInstance = _makeRoam(False)
    roamInstance.currentScreen.run.return_value = ScreenType.MAIN_MENU_SCREEN

    assert roamInstance.run() == "restart"

    roamInstance.worldScreen.hudDragManager.save.assert_not_called()
