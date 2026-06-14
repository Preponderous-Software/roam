from rendering.keyCode import KeyCode
from screen.controlsScreen import ControlsScreen
from screen.screenType import ScreenType


# Characterization tests for the ControlsScreen rebind state machine. They lock
# in the screen's current behavior (no behavior change intended) — the screen
# had no dedicated test file before this.


def test_start_remap_snapshots_bindings_and_waits_for_key(resolve):
    screen = resolve(ControlsScreen)
    assert screen.waitingForKey is None

    screen.startRemap("move_up")

    assert screen.waitingForKey == "move_up"
    # A working copy is taken so edits don't touch the live bindings until save.
    assert screen.pendingBindings is not None
    assert screen.pendingBindings is not screen.keyBindings.bindings


def test_capturing_a_key_rebinds_the_pending_action(resolve):
    screen = resolve(ControlsScreen)
    screen.startRemap("move_up")

    screen.handleKeyDownEvent(KeyCode.U)

    assert screen.waitingForKey is None
    # The pending copy changed; the live bindings did not (until save).
    assert screen.pendingBindings["move_up"] == KeyCode.U
    assert screen.keyBindings.getKey("move_up") == KeyCode.W


def test_escape_while_waiting_cancels_the_capture_without_rebinding(resolve):
    screen = resolve(ControlsScreen)
    screen.startRemap("move_up")

    screen.handleKeyDownEvent(KeyCode.ESCAPE)

    assert screen.waitingForKey is None
    # move_up keeps its default; no transition was requested.
    assert screen.pendingBindings["move_up"] == KeyCode.W
    assert screen.changeScreen is False


def test_unmodeled_key_while_waiting_keeps_waiting(resolve):
    screen = resolve(ControlsScreen)
    screen.startRemap("move_up")

    screen.handleKeyDownEvent(None)

    # Still waiting — an unmodeled key cannot be bound.
    assert screen.waitingForKey == "move_up"


def test_escape_when_not_waiting_returns_to_options(resolve):
    screen = resolve(ControlsScreen)

    screen.handleKeyDownEvent(KeyCode.ESCAPE)

    assert screen.nextScreen == ScreenType.OPTIONS_SCREEN
    assert screen.changeScreen is True


def test_save_commits_pending_bindings_and_returns(resolve):
    screen = resolve(ControlsScreen)
    screen.startRemap("move_up")
    screen.handleKeyDownEvent(KeyCode.U)

    screen.saveAndReturn()

    assert screen.keyBindings.getKey("move_up") == KeyCode.U
    assert screen.pendingBindings is None
    assert screen.changeScreen is True


def test_cancel_discards_pending_bindings_and_returns(resolve):
    screen = resolve(ControlsScreen)
    screen.startRemap("move_up")
    screen.handleKeyDownEvent(KeyCode.U)

    screen.cancelAndReturn()

    # The live binding is untouched and the working copy is cleared.
    assert screen.keyBindings.getKey("move_up") == KeyCode.W
    assert screen.pendingBindings is None
    assert screen.changeScreen is True


def test_reset_to_defaults_loads_defaults_into_pending(resolve):
    screen = resolve(ControlsScreen)
    screen.keyBindings.setKey("move_up", KeyCode.U)

    screen.resetToDefaults()

    assert screen.pendingBindings["move_up"] == KeyCode.W


def test_active_bindings_prefers_pending_over_committed(resolve):
    screen = resolve(ControlsScreen)
    assert screen.getActiveBindings() is screen.keyBindings.bindings

    screen.startRemap("move_up")
    assert screen.getActiveBindings() is screen.pendingBindings


def test_active_conflicts_detects_a_pending_collision(resolve):
    screen = resolve(ControlsScreen)
    assert screen.getActiveConflicts() == set()

    # Rebind move_up onto move_left's key -> both conflict.
    screen.startRemap("move_up")
    screen.handleKeyDownEvent(KeyCode.A)

    conflicts = screen.getActiveConflicts()
    assert "move_up" in conflicts
    assert "move_left" in conflicts


def test_scroll_offset_increments_and_clamps_at_zero(resolve):
    screen = resolve(ControlsScreen)

    class _Wheel:
        def __init__(self, scrollY):
            self.scrollY = scrollY

    screen.handleScrollEvent(_Wheel(-1))
    assert screen.scrollOffset == 1
    screen.handleScrollEvent(_Wheel(1))
    assert screen.scrollOffset == 0
    # Cannot scroll above the top.
    screen.handleScrollEvent(_Wheel(1))
    assert screen.scrollOffset == 0
