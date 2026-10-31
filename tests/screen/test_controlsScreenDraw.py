import pytest

from rendering.inputEvent import EventType, InputEvent
from rendering.keyCode import KeyCode
from screen.controlsScreen import ControlsScreen
from screen.screenType import ScreenType
from ui import palette

# Characterization tests for ControlsScreen's draw path, confirm/reset keys,
# onStart and event dispatch. They lock in the current behavior against the
# conftest renderer mock (1280x720); no production code changed. The rebind
# state machine itself is covered in test_controlsScreen.py.

# Layout derived from the 1280x720 test display.
KEY_X = 1280 * 0.65
ROW_BUTTON_WIDTH = 1280 * 0.25
VISIBLE_ROWS = int((720 - 60 - 80) / 35)  # 16
BOTTOM_BUTTON_WIDTH = 1280 / 5
BOTTOM_Y = 720 - 45
BOTTOM_START_X = (1280 - (BOTTOM_BUTTON_WIDTH * 3 + 10 * 2)) / 2
CONFLICT_LABEL_COLOR = (255, 100, 100)
CONFLICT_BUTTON_COLOR = (255, 50, 50)
WAITING_BUTTON_COLOR = (100, 100, 255)
CURSOR_HIGHLIGHT_COLOR = (255, 255, 0)
HINT = (
    "Up/Down: navigate  -  Enter/Space: remap  -  S: save  -  R: reset  -  Esc: cancel"
)


def _calls(renderer, method):
    return [c.args for c in getattr(renderer, method).call_args_list]


def _rowButtons(renderer):
    return [
        args
        for args in _calls(renderer, "drawButton")
        if args[0] == KEY_X and args[2] == ROW_BUTTON_WIDTH
    ]


def _bottomButtons(renderer):
    return {
        args[7]: args
        for args in _calls(renderer, "drawButton")
        if args[2] == BOTTOM_BUTTON_WIDTH
    }


def _rowLabels(renderer):
    # Row labels are the size-20 texts; the title is 36 and the hints smaller.
    return [args for args in _calls(renderer, "drawText") if args[3] == 20]


def _texts(renderer):
    return [args[0] for args in _calls(renderer, "drawText")]


# --- title -------------------------------------------------------------------


def test_draw_title_is_centered_at_the_top(resolve):
    screen = resolve(ControlsScreen)

    screen.drawTitle()

    assert _calls(screen.renderer, "drawText") == [
        ("Controls", 640, 25, 36, palette.WHITE)
    ]


# --- binding rows --------------------------------------------------------------


def test_draw_bindings_shows_one_visible_page_of_rows(resolve):
    screen = resolve(ControlsScreen)
    actions = screen.keyBindings.getActions()

    screen.drawBindings()

    rows = _rowButtons(screen.renderer)
    labels = _rowLabels(screen.renderer)
    assert len(rows) == VISIBLE_ROWS
    assert [label[0] for label in labels] == [
        screen.keyBindings.getLabel(a) for a in actions[:VISIBLE_ROWS]
    ]
    # Rows are 35 px apart starting at y=60, 28 px tall.
    assert [row[1] for row in rows] == [60 + i * 35 for i in range(VISIBLE_ROWS)]
    assert all(row[3] == 28 for row in rows)


def test_cursor_row_is_prefixed_and_highlighted(resolve):
    screen = resolve(ControlsScreen)

    screen.drawBindings()

    rows = _rowButtons(screen.renderer)
    assert rows[0][7] == "> w"  # move_up, the default W
    assert rows[0][4] == palette.DARKER_GRAY
    assert rows[1][7] == "a"  # move_left, no cursor prefix
    assert _calls(screen.renderer, "drawSelectionHighlight") == [
        (KEY_X, 60, ROW_BUTTON_WIDTH, 28, CURSOR_HIGHLIGHT_COLOR)
    ]


def test_alt_rows_are_indented_and_gray(resolve):
    screen = resolve(ControlsScreen)
    actions = screen.keyBindings.getActions()
    altIndex = actions.index("alt_move_up")
    plainIndex = actions.index("move_up")

    screen.drawBindings()

    labels = _rowLabels(screen.renderer)
    assert labels[altIndex][1] == 1280 * 0.15 + 18
    assert labels[altIndex][4] == palette.MEDIUM_GRAY
    assert labels[plainIndex][1] == 1280 * 0.15
    assert labels[plainIndex][4] == palette.WHITE


def test_conflicting_rows_are_drawn_in_red(resolve):
    screen = resolve(ControlsScreen)
    actions = screen.keyBindings.getActions()
    screen.startRemap("move_up")
    screen.handleKeyDownEvent(KeyCode.A)  # collides with move_left

    screen.drawBindings()

    labels = _rowLabels(screen.renderer)
    rows = _rowButtons(screen.renderer)
    for action in ("move_up", "move_left"):
        index = actions.index(action)
        assert labels[index][4] == CONFLICT_LABEL_COLOR
        assert rows[index][4] == CONFLICT_BUTTON_COLOR
    downIndex = actions.index("move_down")
    assert labels[downIndex][4] == palette.WHITE
    assert rows[downIndex][4] == palette.DARKER_GRAY


def test_row_waiting_for_a_key_shows_the_prompt_without_a_highlight(resolve):
    screen = resolve(ControlsScreen)
    screen.startRemap("move_up")  # cursor is also on move_up

    screen.drawBindings()

    rows = _rowButtons(screen.renderer)
    assert rows[0][4] == WAITING_BUTTON_COLOR
    assert rows[0][7] == "Press a key  (Esc cancels)"
    screen.renderer.drawSelectionHighlight.assert_not_called()


def test_row_button_callback_starts_a_remap_of_that_row(resolve):
    screen = resolve(ControlsScreen)
    actions = screen.keyBindings.getActions()

    screen.drawBindings()
    _rowButtons(screen.renderer)[2][8]()

    assert screen.waitingForKey == actions[2]
    assert screen.pendingBindings is not None


def test_integer_bindings_are_displayed_through_key_code_lookup(resolve):
    screen = resolve(ControlsScreen)
    screen.pendingBindings = dict(screen.keyBindings.bindings)
    screen.pendingBindings["move_up"] = KeyCode.U.value
    screen.pendingBindings["move_left"] = 999999  # not a modeled key

    screen.drawBindings()

    rows = _rowButtons(screen.renderer)
    assert rows[0][7] == "> u"
    assert rows[1][7] == "None"


def test_actions_missing_from_pending_fall_back_to_the_default_key(resolve):
    screen = resolve(ControlsScreen)
    screen.keyBindings.setKey("move_left", KeyCode.U)
    screen.pendingBindings = dict(screen.keyBindings.bindings)
    del screen.pendingBindings["move_left"]

    screen.drawBindings()

    # The default (A) is shown, not the committed binding (U).
    assert _rowButtons(screen.renderer)[1][7] == "a"


def test_hint_and_scroll_position_are_drawn_below_the_rows(resolve):
    screen = resolve(ControlsScreen)
    total = len(screen.keyBindings.getActions())

    screen.drawBindings()

    texts = _calls(screen.renderer, "drawText")
    assert (HINT, 640, 720 - 92, 13, palette.DIM_GRAY) in texts
    assert (
        "1-" + str(VISIBLE_ROWS) + " of " + str(total),
        640,
        720 - 70,
        16,
        palette.MEDIUM_GRAY,
    ) in texts


def test_cursor_below_the_page_scrolls_it_into_view(resolve):
    screen = resolve(ControlsScreen)
    actions = screen.keyBindings.getActions()
    screen._cursor = 20

    screen.drawBindings()

    # The window ends on the cursor row: offset = 20 - 16 + 1 = 5.
    assert screen.scrollOffset == 5
    labels = _rowLabels(screen.renderer)
    assert labels[0][0] == screen.keyBindings.getLabel(actions[5])
    rows = _rowButtons(screen.renderer)
    assert rows[-1][7].startswith("> ")
    assert "6-21 of " + str(len(actions)) in _texts(screen.renderer)


def test_cursor_above_the_page_scrolls_back_up_to_it(resolve):
    screen = resolve(ControlsScreen)
    screen.scrollOffset = 10
    screen._cursor = 3

    screen.drawBindings()

    assert screen.scrollOffset == 3
    assert _rowButtons(screen.renderer)[0][7].startswith("> ")


def test_scroll_offset_is_clamped_to_the_last_full_page(resolve):
    screen = resolve(ControlsScreen)
    total = len(screen.keyBindings.getActions())
    screen._cursor = total - 1

    screen.drawBindings()

    assert screen.scrollOffset == total - VISIBLE_ROWS
    assert len(_rowButtons(screen.renderer)) == VISIBLE_ROWS
    expected = str(total - VISIBLE_ROWS + 1) + "-" + str(total) + " of " + str(total)
    assert expected in _texts(screen.renderer)


def test_no_scroll_position_when_every_row_fits(resolve):
    screen = resolve(ControlsScreen)
    total = len(screen.keyBindings.getActions())
    screen.renderer.getDisplaySize.return_value = (1280, 60 + 80 + 35 * total)

    screen.drawBindings()

    assert len(_rowButtons(screen.renderer)) == total
    assert not any(" of " in text for text in _texts(screen.renderer))


# --- bottom buttons ------------------------------------------------------------


def test_bottom_buttons_without_conflicts(resolve):
    screen = resolve(ControlsScreen)

    screen.drawBottomButtons()

    buttons = _bottomButtons(screen.renderer)
    assert list(buttons) == ["Reset Defaults", "Save", "Cancel"]
    reset, save, cancel = buttons.values()
    assert reset[:7] == (
        BOTTOM_START_X,
        BOTTOM_Y,
        BOTTOM_BUTTON_WIDTH,
        35,
        palette.WHITE,
        palette.BLACK,
        20,
    )
    assert save[0] == BOTTOM_START_X + BOTTOM_BUTTON_WIDTH + 10
    assert save[4:6] == (palette.GREEN, palette.BLACK)
    assert cancel[0] == BOTTOM_START_X + 2 * (BOTTOM_BUTTON_WIDTH + 10)
    assert reset[8] == screen.resetToDefaults
    assert save[8] == screen.saveAndReturn
    assert cancel[8] == screen.cancelAndReturn
    screen.renderer.drawText.assert_not_called()


def test_bottom_buttons_disable_save_and_explain_conflicts(resolve):
    screen = resolve(ControlsScreen)
    screen.startRemap("move_up")
    screen.handleKeyDownEvent(KeyCode.A)  # move_up + move_left conflict

    screen.drawBottomButtons()

    assert _calls(screen.renderer, "drawText") == [
        (
            "Resolve 2 key conflicts (shown in red) to enable Save",
            640,
            BOTTOM_Y - 18,
            16,
            (255, 120, 120),
        )
    ]
    save = _bottomButtons(screen.renderer)["Save"]
    assert save[4:6] == (palette.DARK_GRAY, palette.MEDIUM_GRAY)
    # The disabled Save button's callback does nothing.
    save[8]()
    assert screen.changeScreen is False
    assert screen.keyBindings.getKey("move_up") == KeyCode.W


def test_conflict_message_uses_the_singular_for_one_conflict(resolve, monkeypatch):
    screen = resolve(ControlsScreen)
    monkeypatch.setattr(screen, "getActiveConflicts", lambda: {"move_up"})

    screen.drawBottomButtons()

    assert _texts(screen.renderer) == [
        "Resolve 1 key conflict (shown in red) to enable Save"
    ]


def test_bottom_button_callbacks_reset_and_cancel(resolve):
    screen = resolve(ControlsScreen)
    screen.keyBindings.setKey("move_up", KeyCode.U)

    screen.drawBottomButtons()
    buttons = _bottomButtons(screen.renderer)

    buttons["Reset Defaults"][8]()
    assert screen.pendingBindings["move_up"] == KeyCode.W
    buttons["Cancel"][8]()
    assert screen.pendingBindings is None
    assert screen.keyBindings.getKey("move_up") == KeyCode.U
    assert screen.changeScreen is True


# --- keys ----------------------------------------------------------------------


@pytest.mark.parametrize("key", [KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE])
def test_confirm_keys_start_a_remap_of_the_cursor_row(resolve, key):
    screen = resolve(ControlsScreen)
    actions = screen.keyBindings.getActions()
    screen._cursor = 3

    screen.handleKeyDownEvent(key)

    assert screen.waitingForKey == actions[3]
    assert screen.pendingBindings is not None


def test_confirm_key_with_the_cursor_out_of_range_does_nothing(resolve):
    screen = resolve(ControlsScreen)
    screen._cursor = len(screen.keyBindings.getActions())

    screen.handleKeyDownEvent(KeyCode.RETURN)

    assert screen.waitingForKey is None
    assert screen.pendingBindings is None


def test_r_resets_pending_bindings_to_defaults(resolve):
    screen = resolve(ControlsScreen)
    screen.keyBindings.setKey("move_up", KeyCode.U)

    screen.handleKeyDownEvent(KeyCode.R)

    assert screen.pendingBindings["move_up"] == KeyCode.W
    # Nothing is committed until save.
    assert screen.keyBindings.getKey("move_up") == KeyCode.U
    assert screen.changeScreen is False


def test_captured_key_without_a_working_copy_creates_one(resolve):
    screen = resolve(ControlsScreen)
    screen.waitingForKey = "move_up"  # set without startRemap's snapshot

    screen.handleKeyDownEvent(KeyCode.U)

    assert screen.pendingBindings is not screen.keyBindings.bindings
    assert screen.pendingBindings["move_up"] == KeyCode.U
    assert screen.keyBindings.getKey("move_up") == KeyCode.W
    assert screen.waitingForKey is None


def test_down_clamps_at_the_last_row(resolve):
    screen = resolve(ControlsScreen)
    last = len(screen.keyBindings.getActions()) - 1
    screen._cursor = last

    screen.handleKeyDownEvent(KeyCode.DOWN)

    assert screen._cursor == last


def test_unbound_keys_are_ignored(resolve):
    screen = resolve(ControlsScreen)

    screen.handleKeyDownEvent(KeyCode.X)

    assert screen._cursor == 0
    assert screen.waitingForKey is None
    assert screen.pendingBindings is None
    assert screen.changeScreen is False


# --- lifecycle and dispatch ----------------------------------------------------


def test_on_start_clears_edit_state_and_cursor(resolve):
    screen = resolve(ControlsScreen)
    screen.startRemap("move_up")
    screen.scrollOffset = 7
    screen._cursor = 9

    screen.onStart()

    assert screen.pendingBindings is None
    assert screen.waitingForKey is None
    assert screen.scrollOffset == 0
    assert screen._cursor == 0


def test_handle_event_dispatches_key_down_and_mouse_wheel(resolve):
    screen = resolve(ControlsScreen)

    screen.handleEvent(InputEvent(EventType.KEY_DOWN, key=KeyCode.DOWN))
    assert screen._cursor == 1
    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))
    assert screen._cursor == 2
    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=1))
    assert screen._cursor == 1


def test_handle_event_ignores_other_event_types(resolve):
    screen = resolve(ControlsScreen)

    screen.handleEvent(InputEvent(EventType.KEY_UP, key=KeyCode.DOWN))
    screen.handleEvent(InputEvent(EventType.MOUSE_DOWN, position=(0, 0), button=1))

    assert screen._cursor == 0
    assert screen.changeScreen is False


def test_draw_clears_then_draws_title_rows_and_buttons(resolve):
    screen = resolve(ControlsScreen)

    screen.draw()

    names = [c[0] for c in screen.renderer.method_calls]
    assert names[0] == "clearScreen"
    screen.renderer.clearScreen.assert_called_once_with(palette.BLACK)
    assert "Controls" in _texts(screen.renderer)
    assert len(_rowButtons(screen.renderer)) == VISIBLE_ROWS
    assert list(_bottomButtons(screen.renderer)) == [
        "Reset Defaults",
        "Save",
        "Cancel",
    ]
    # Title before rows before bottom buttons.
    firstRow = next(
        i
        for i, c in enumerate(screen.renderer.method_calls)
        if c[0] == "drawButton" and c.args[0] == KEY_X
    )
    firstBottom = next(
        i
        for i, c in enumerate(screen.renderer.method_calls)
        if c[0] == "drawButton" and c.args[2] == BOTTOM_BUTTON_WIDTH
    )
    titleIndex = next(
        i
        for i, c in enumerate(screen.renderer.method_calls)
        if c[0] == "drawText" and c.args[0] == "Controls"
    )
    assert titleIndex < firstRow < firstBottom
