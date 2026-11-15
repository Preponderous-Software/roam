"""Characterization tests for SaveSelectionScreen's draw paths and the input
branches the main test file leaves out.

These lock in current behaviour: the keyboard cursor scrolling the list, the
mouse wheel, T and Backspace on the list, Enter in the delete confirmation,
the onStart wait for the mouse button to be released, and what the delete
confirmation, the naming and rename errors, the scroll indicator and the
no-saves hint send to the renderer. The renderer is a MagicMock, so nothing
here opens a display.
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

from rendering.inputEvent import EventType, InputEvent
from rendering.keyCode import KeyCode
from rendering.renderer import Renderer
from screen.saveSelectionScreen import SaveSelectionScreen
from screen.screenType import ScreenType

# On an 800x600 display seven save rows fit: (450 - 75) / (600 / 14 + 8) = 7.37.
ROWS_THAT_FIT = 7


def _renderer(width=800, height=600):
    renderer = MagicMock(spec=Renderer)
    renderer.getDisplaySize.return_value = (width, height)
    return renderer


def _screen(savesDir):
    inputSource = MagicMock()
    inputSource.getMouseButtons.return_value = (False, False, False)
    inputSource.pollEvents.return_value = []
    screen = SaveSelectionScreen(_renderer(), inputSource, MagicMock(), MagicMock())
    screen.savesBaseDirectory = str(savesDir)
    return screen


def _makeSaves(savesDir, count):
    paths = []
    for i in range(count):
        path = os.path.join(str(savesDir), "save_%02d" % i)
        os.makedirs(path)
        paths.append(path)
    return paths


def _screenWithSaves(savesDir, count):
    paths = _makeSaves(savesDir, count)
    screen = _screen(savesDir)
    # Name order is deterministic; directory mtimes created in one test are not.
    screen.sortMode = SaveSelectionScreen.SORT_BY_NAME
    return screen, paths


def _drawnTexts(screen):
    return [c.args[0] for c in screen.renderer.drawText.call_args_list]


def _buttons(screen):
    """Map each drawn button's label to its click callback."""
    return {c.args[7]: c.args[8] for c in screen.renderer.drawButton.call_args_list}


def _recordRemovedWorlds(monkeypatch):
    removed = []
    module = sys.modules[SaveSelectionScreen.__module__]
    monkeypatch.setattr(module, "noteBrowserWorldRemoved", removed.append)
    return removed


# --- name validation and save creation edges ---------------------------------


def test_a_name_containing_two_dots_is_invalid(tmp_path):
    screen = _screen(tmp_path)

    assert screen._isValidSaveName("a..b") is False
    assert screen._isValidSaveName("a.b") is True


def test_creating_a_save_creates_a_missing_base_directory(tmp_path):
    base = tmp_path / "saves"
    screen = _screen(base)

    screen.createNewGameWithName("first")

    assert (base / "first").is_dir()
    assert screen.nextScreen == ScreenType.WORLD_SCREEN
    assert screen.changeScreen is True


def test_generated_name_is_save_1_when_the_base_directory_is_missing(tmp_path):
    screen = _screen(tmp_path / "missing")

    assert screen._generateSaveName() == "save_1"


def test_confirming_a_name_that_exists_keeps_the_dialog_open_with_an_error(
    tmp_path,
):
    os.makedirs(os.path.join(str(tmp_path), "taken"))
    screen = _screen(tmp_path)
    screen.startNamingNewSave()
    screen.newSaveNameInput = "  taken  "

    screen.confirmNewSaveName()

    assert screen.namingNewSave is True
    assert screen.newSaveNameError == 'A save named "taken" already exists.'
    assert screen.changeScreen is False
    assert sorted(os.listdir(str(tmp_path))) == ["taken"]


def test_renaming_a_save_outside_the_base_directory_is_cancelled(tmp_path, monkeypatch):
    removed = _recordRemovedWorlds(monkeypatch)
    base = tmp_path / "saves"
    base.mkdir()
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    screen = _screen(base)
    screen.startRenamingSave(str(outside))
    screen.renameNameInput = "fresh"

    screen.confirmRenameSave()

    assert outside.is_dir()
    assert not (base / "fresh").exists()
    assert screen.renamingSave is None
    assert screen.renameNameInput == ""
    assert screen.renameNameError == ""
    assert removed == []


# --- keyboard cursor scrolling the list --------------------------------------


def test_moving_the_cursor_below_the_last_visible_row_scrolls_down(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, 10)
    screen._selectedIndex = ROWS_THAT_FIT - 1

    screen.handleKeyDownEvent(KeyCode.DOWN)

    assert screen.getHighlightedSaveIndex() == ROWS_THAT_FIT
    assert screen.scrollOffset == 1


def test_moving_the_cursor_inside_the_visible_rows_does_not_scroll(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, 10)
    screen._selectedIndex = 2

    screen.handleKeyDownEvent(KeyCode.S)

    assert screen.getHighlightedSaveIndex() == 3
    assert screen.scrollOffset == 0


def test_moving_the_cursor_above_the_first_visible_row_scrolls_up(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, 10)
    screen._selectedIndex = 3
    screen.scrollOffset = 3

    screen.handleKeyDownEvent(KeyCode.W)

    assert screen.getHighlightedSaveIndex() == 2
    assert screen.scrollOffset == 2


def test_the_cursor_stops_at_the_last_save(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, 3)
    screen._selectedIndex = 2

    screen.handleKeyDownEvent(KeyCode.DOWN)

    assert screen.getHighlightedSaveIndex() == 2
    assert screen.scrollOffset == 0


# --- mouse wheel ---------------------------------------------------------------


def test_wheel_down_moves_the_cursor_down(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, 3)

    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))

    assert screen.getHighlightedSaveIndex() == 1


def test_wheel_up_moves_the_cursor_up(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, 3)
    screen._selectedIndex = 2

    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=1))

    assert screen.getHighlightedSaveIndex() == 1


def test_wheel_with_no_vertical_scroll_does_nothing(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, 3)
    screen._selectedIndex = 1

    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=0))

    assert screen.getHighlightedSaveIndex() == 1
    assert screen.scrollOffset == 0


# --- T, Backspace and Enter on the list ----------------------------------------


def test_t_toggles_the_sort_order(tmp_path):
    screen = _screen(tmp_path)

    screen.handleKeyDownEvent(KeyCode.T)
    assert screen.sortMode == SaveSelectionScreen.SORT_BY_NAME

    screen.handleKeyDownEvent(KeyCode.T)
    assert screen.sortMode == SaveSelectionScreen.SORT_BY_DATE


def test_backspace_asks_to_delete_the_highlighted_save(tmp_path):
    screen, paths = _screenWithSaves(tmp_path, 3)
    screen._selectedIndex = 1

    screen.handleKeyDownEvent(KeyCode.BACKSPACE)

    assert screen.confirmingDelete == paths[1]
    assert os.path.isdir(paths[1])


def test_backspace_with_no_saves_does_nothing(tmp_path):
    screen = _screen(tmp_path)

    screen.handleKeyDownEvent(KeyCode.BACKSPACE)

    assert screen.confirmingDelete is None


def test_enter_in_the_delete_confirmation_deletes_the_save(tmp_path, monkeypatch):
    removed = _recordRemovedWorlds(monkeypatch)
    screen, paths = _screenWithSaves(tmp_path, 2)
    screen.handleKeyDownEvent(KeyCode.BACKSPACE)

    screen.handleKeyDownEvent(KeyCode.RETURN)

    assert not os.path.exists(paths[0])
    assert os.path.isdir(paths[1])
    assert screen.confirmingDelete is None
    assert removed == [paths[0]]


def test_other_keys_in_the_delete_confirmation_are_ignored(tmp_path):
    screen, paths = _screenWithSaves(tmp_path, 2)
    screen.handleKeyDownEvent(KeyCode.BACKSPACE)

    screen.handleKeyDownEvent(KeyCode.DOWN)
    screen.handleKeyDownEvent(KeyCode.T)

    assert screen.confirmingDelete == paths[0]
    assert screen.getHighlightedSaveIndex() == 0
    assert screen.sortMode == SaveSelectionScreen.SORT_BY_NAME


# --- onStart waits for the mouse button to be released ------------------------


def _countSleeps(monkeypatch):
    sleeps = []
    module = sys.modules[SaveSelectionScreen.__module__]
    monkeypatch.setattr(module.time, "sleep", sleeps.append)
    return sleeps


def test_onStart_waits_until_the_mouse_button_is_released(tmp_path, monkeypatch):
    sleeps = _countSleeps(monkeypatch)
    screen = _screen(tmp_path)
    held, released = (True, False, False), (False, False, False)
    screen.inputSource.getMouseButtons.side_effect = [held, held, released]

    screen.onStart()

    assert sleeps == [0.01, 0.01]
    assert screen.inputSource.pollEvents.call_count == 2
    assert screen.changeScreen is False


def test_onStart_quit_while_the_button_is_held_exits_the_game(tmp_path, monkeypatch):
    sleeps = _countSleeps(monkeypatch)
    screen = _screen(tmp_path)
    screen.inputSource.getMouseButtons.return_value = (True, False, False)
    screen.inputSource.pollEvents.return_value = [InputEvent(EventType.QUIT)]

    screen.onStart()

    assert screen.nextScreen == ScreenType.NONE
    assert screen.changeScreen is True
    assert sleeps == []


def test_onStart_refreshes_the_save_list(tmp_path):
    screen = _screen(tmp_path)
    assert screen.getSaveDirectories() == []
    _makeSaves(tmp_path, 1)

    screen.onStart()

    assert [s["name"] for s in screen.getSaveDirectories()] == ["save_00"]


# --- draw ----------------------------------------------------------------------


def test_a_list_longer_than_the_screen_shows_which_rows_are_visible(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, 10)
    screen.scrollOffset = 2

    screen.draw()

    texts = _drawnTexts(screen)
    assert "3-9 of 10  -  scroll or arrow keys" in texts
    saveLabels = [label for label in _buttons(screen) if "  |  " in label]
    assert len(saveLabels) == ROWS_THAT_FIT
    assert saveLabels[0].startswith("save_02")


def test_a_list_that_fits_shows_no_scroll_indicator(tmp_path):
    screen, _ = _screenWithSaves(tmp_path, ROWS_THAT_FIT)

    screen.draw()

    assert not any("scroll or arrow keys" in t for t in _drawnTexts(screen))


def test_the_delete_confirmation_names_the_save_and_hides_the_controls_hint(
    tmp_path,
):
    screen, paths = _screenWithSaves(tmp_path, 2)
    screen._requestDelete(paths[1])

    screen.draw()

    texts = _drawnTexts(screen)
    assert "Delete 'save_01'?" in texts
    assert "This cannot be undone." in texts
    assert "Enter: confirm  -  Esc: cancel" in texts
    assert not any(t.startswith("W/S or Up/Down") for t in texts)
    # The list and bottom buttons are drawn greyed out, so only the dialog's
    # two buttons are clickable.
    assert sorted(_buttons(screen)) == ["Cancel", "Delete"]


def test_the_delete_confirmations_delete_button_deletes_the_save(tmp_path, monkeypatch):
    _recordRemovedWorlds(monkeypatch)
    screen, paths = _screenWithSaves(tmp_path, 2)
    screen._requestDelete(paths[1])
    screen.draw()

    _buttons(screen)["Delete"]()

    assert not os.path.exists(paths[1])
    assert screen.confirmingDelete is None


def test_the_delete_confirmations_cancel_button_keeps_the_save(tmp_path):
    screen, paths = _screenWithSaves(tmp_path, 2)
    screen._requestDelete(paths[1])
    screen.draw()

    _buttons(screen)["Cancel"]()

    assert os.path.isdir(paths[1])
    assert screen.confirmingDelete is None


def test_the_naming_dialog_shows_its_error(tmp_path):
    screen = _screen(tmp_path)
    screen.startNamingNewSave()
    screen.newSaveNameError = 'A save named "x" already exists.'

    screen.draw()

    assert 'A save named "x" already exists.' in _drawnTexts(screen)


def test_the_rename_dialog_shows_its_error(tmp_path):
    screen, paths = _screenWithSaves(tmp_path, 1)
    screen.startRenamingSave(paths[0])
    screen.renameNameError = "Invalid name."

    screen.draw()

    texts = _drawnTexts(screen)
    assert "Rename save:" in texts
    assert "Invalid name." in texts


def test_with_no_saves_the_hint_points_at_the_create_button(tmp_path):
    screen = _screen(tmp_path)

    screen.draw()

    texts = _drawnTexts(screen)
    assert "Welcome to Roam!" in texts
    assert "C or click button: create new save  -  Esc: back" in texts
    assert "Create New Save" in _buttons(screen)
