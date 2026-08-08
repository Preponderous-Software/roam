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


# --- command-line argument handling (issue #553) ---


def test_help_flag_prints_usage_and_exits_zero(capsys):
    from roam import main

    assert main(["roam.py", "--help"]) == 0

    out = capsys.readouterr().out
    assert out.startswith("Usage: roam.py")
    assert "--text" in out
    assert "--selftest" in out


def test_short_help_flag_prints_the_same_usage(capsys):
    from roam import main

    assert main(["roam.py", "-h"]) == 0
    assert capsys.readouterr().out.startswith("Usage: roam.py")


def test_usage_does_not_advertise_the_broken_web_flag(capsys):
    # --web is accepted but left unlisted until issue #550 is resolved.
    from roam import main

    main(["roam.py", "--help"])
    assert "--web" not in capsys.readouterr().out


def test_unknown_argument_is_reported_on_stderr_and_exits_nonzero(capsys):
    from roam import main

    assert main(["roam.py", "--txt"]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unrecognized argument: --txt" in captured.err
    assert "Usage: roam.py" in captured.err


def test_every_unknown_argument_is_reported(capsys):
    from roam import main

    assert main(["roam.py", "--txt", "--verbose"]) == 2

    err = capsys.readouterr().err
    assert "unrecognized argument: --txt" in err
    assert "unrecognized argument: --verbose" in err


def test_help_takes_precedence_over_an_unknown_argument(capsys):
    from roam import main

    assert main(["roam.py", "--txt", "--help"]) == 0
    assert capsys.readouterr().err == ""


def test_known_flags_are_not_reported_as_unknown():
    from roam import _unknownArguments

    assert _unknownArguments(["roam.py", "--text", "--selftest", "--web"]) == []


def test_program_name_is_never_treated_as_an_argument():
    from roam import _unknownArguments, _wantsHelp

    assert _unknownArguments(["--help"]) == []
    assert _wantsHelp(["-h"]) is False


def test_macos_process_serial_number_argument_is_ignored():
    # Finder can hand a launched .app bundle a -psn_<n>_<n> argument.
    from roam import _unknownArguments

    assert _unknownArguments(["Roam", "-psn_0_123456"]) == []


def test_usage_names_the_program_that_was_actually_run(capsys):
    # The packaged build is Roam.exe / Roam, not roam.py.
    from roam import main

    # A forward-slash path so os.path.basename behaves the same on every
    # platform the suite runs on.
    assert main(["dist/Roam/Roam.exe", "--help"]) == 0
    assert capsys.readouterr().out.startswith("Usage: Roam.exe")

    assert main(["/opt/roam/Roam", "--bogus"]) == 2
    err = capsys.readouterr().err
    assert "Roam: unrecognized argument: --bogus" in err
    assert "Usage: Roam" in err
