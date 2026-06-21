import os

import pytest

from textPlaythrough import TextPlaythrough

# The driver needs a pseudo-terminal, which is POSIX-only. The CI test job runs
# on ubuntu-latest, so this exercises text mode on every push/PR there; it skips
# cleanly on a developer's Windows machine.
pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="text playthrough harness needs a POSIX pty"
)


def test_text_mode_boots_to_the_main_menu():
    with TextPlaythrough() as game:
        menu = game.expect("Roam")
        assert "Play" in menu
        assert "Quit" in menu
    assert game.cleanExit(), game.getStderr()


def test_enter_advances_main_menu_to_save_selection():
    with TextPlaythrough() as game:
        game.expect("Roam")
        game.send("\r")  # cbreak delivers Enter as CR -> KeyCode.RETURN
        game.expect("Select Save")  # the save-selection screen title
    assert game.cleanExit(), game.getStderr()


def test_creating_a_save_renders_and_runs_the_world():
    # The payoff path and the one that regressed: reaching the world renders the
    # HUD ("Tick:") through the TextRenderer with no pygame and no crash. Guards
    # the geometry.Rect getGameAreaRect fix and cbreak Enter handling.
    with TextPlaythrough() as game:
        game.expect("Roam")
        game.send("\r")  # -> save selection
        game.expect("Select Save")
        game.send("c")  # open the new-save name field
        game.expect("Enter save name")  # wait for the prompt, as a user would
        game.send(game.getSaveName() + "\r")  # name it and confirm
        world = game.expect("Tick", timeout=15.0)
        assert "TPS" in world  # the live HUD, i.e. the loop is ticking
    assert game.cleanExit(), game.getStderr()


def test_the_new_save_name_field_does_not_capture_its_opening_keystroke():
    # 'c' opens the name field; its paired TEXT_INPUT must not type a leading
    # "c". Confirmed end-to-end: the world loads under the intended name, so the
    # save folder created on disk is exactly getSaveName() (no "c" prefix).
    with TextPlaythrough() as game:
        game.expect("Roam")
        game.send("\r")
        game.expect("Select Save")
        game.send("c")
        game.expect("Enter save name")
        game.send(game.getSaveName() + "\r")
        game.expect("Tick", timeout=15.0)
        savePath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "saves",
            game.getSaveName(),
        )
        assert os.path.isdir(savePath)  # exact name -> the 'c' did not leak in
    assert game.cleanExit(), game.getStderr()
