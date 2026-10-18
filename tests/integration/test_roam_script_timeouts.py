from roamScript import (
    ASSERT_CONTAINS_DEFAULT_TIMEOUT,
    _handleAssertContains,
    _handleExpect,
)


class FakeGame:
    def __init__(self):
        self.calls = []

    def getSaveName(self):
        return "save"

    def expect(self, text, timeout=None):
        self.calls.append((text, timeout))


def test_assert_contains_waits_past_a_slow_first_frame_by_default():
    # roam#612: a 1 s default failed on a loaded CI runner while the game was
    # still painting the screen the step was waiting for.
    game = FakeGame()

    _handleAssertContains(game, '"press [I] or [Esc] to close"')

    assert ASSERT_CONTAINS_DEFAULT_TIMEOUT >= 5.0
    assert game.calls == [
        ("press [I] or [Esc] to close", ASSERT_CONTAINS_DEFAULT_TIMEOUT)
    ]


def test_assert_contains_explicit_timeout_wins_over_the_default():
    game = FakeGame()

    _handleAssertContains(game, "TPS timeout=2")

    assert game.calls == [("TPS", 2.0)]


def test_expect_passes_its_explicit_timeout_through():
    game = FakeGame()

    _handleExpect(game, '"press [I] or [Esc] to close" timeout=10')

    assert game.calls == [("press [I] or [Esc] to close", 10.0)]
