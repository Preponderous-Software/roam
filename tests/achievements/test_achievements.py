"""achievements.Achievements: checks only on arcade, on a schedule, and never
lets an error reach the game loop."""

import pytest

from achievements import achievements as achievementsModule
from achievements import arcadeBridge
from achievements.achievementRegistry import EVENT_PLACED_CAMPFIRE
from achievements.achievements import (
    CHECK_INTERVAL_TICKS,
    ROOMS_REPORT_INTERVAL_SECONDS,
    AchievementContext,
    Achievements,
    heldClassNames,
)
from entity.apple import Apple
from entity.goldenLantern import GoldenLantern
from inventory.inventory import Inventory

DAY = 54000


@pytest.fixture(autouse=True)
def _fresh_bridge():
    arcadeBridge.reset()
    yield
    arcadeBridge.reset()


@pytest.fixture
def sent():
    messages = []
    arcadeBridge.install(messages.append)
    return messages


def builder(**overrides):
    calls = []

    def build(events=()):
        values = dict(
            tick=0,
            dayLengthTicks=DAY,
            roomsExplored=1,
            foodEaten=0,
            discovered=[],
            heldClassNames=[],
            depth=0,
            deepestDepth=3,
            events=events,
        )
        values.update(overrides)
        calls.append(1)
        return AchievementContext(**values)

    build.calls = calls
    return build


def unlocked(messages):
    return [m["achievement"] for m in messages if m["kind"] == "unlock"]


def scores(messages):
    return [(m["board"], m["value"]) for m in messages if m["kind"] == "score"]


def test_off_arcade_nothing_is_even_checked():
    build = builder(roomsExplored=500)
    assert Achievements().update(build, 0, force=True) == []
    assert build.calls == []


def test_loading_a_world_credits_what_it_already_did(sent):
    build = builder(tick=DAY * 2 + 5, roomsExplored=30, foodEaten=60)
    met = Achievements().update(build, DAY * 2 + 5, force=True)
    assert {a.identifier for a in met} == {
        "nightfall",
        "first-light",
        "one-full-day",
        "wanderer",
        "well-fed",
    }
    assert set(unlocked(sent)) == {a.identifier for a in met}
    assert scores(sent) == [("most-days", 2), ("most-rooms", 30)]


def test_titles_travel_with_unlocks_for_the_page_toast(sent):
    Achievements().update(builder(roomsExplored=25), 0, force=True)
    assert {"kind": "unlock", "achievement": "wanderer", "title": "Wanderer"} in sent


def test_checks_run_once_per_interval(sent):
    tracker = Achievements()
    build = builder()
    tracker.update(build, 100)
    tracker.update(build, 100 + CHECK_INTERVAL_TICKS - 1)
    assert len(build.calls) == 1
    tracker.update(build, 100 + CHECK_INTERVAL_TICKS)
    assert len(build.calls) == 2


def test_a_tick_that_goes_backwards_checks_at_once(sent):
    # Another world (with an earlier tick) was loaded into the same tracker.
    tracker = Achievements()
    build = builder()
    tracker.update(build, 5000)
    tracker.update(build, 10)
    assert len(build.calls) == 2


def test_an_event_is_checked_on_the_next_update(sent):
    tracker = Achievements()
    tracker.update(builder(), 100)
    tracker.noteEvent(EVENT_PLACED_CAMPFIRE)
    tracker.update(lambda: builder()(events=tracker.getEvents()), 101)
    assert unlocked(sent) == ["hearth"]


def test_no_day_board_before_the_first_full_day(sent):
    Achievements().update(builder(tick=DAY - 1), 0, force=True)
    assert scores(sent) == []


def test_a_new_world_with_one_room_reports_no_rooms_score(sent):
    Achievements().update(builder(roomsExplored=1), 0, force=True)
    assert scores(sent) == []


def test_the_rooms_board_is_reported_at_most_every_interval(sent, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(achievementsModule.time, "monotonic", lambda: now[0])
    tracker = Achievements()
    tracker.update(builder(roomsExplored=5), 0)
    now[0] += 10
    tracker.update(builder(roomsExplored=6), CHECK_INTERVAL_TICKS)
    assert scores(sent) == [("most-rooms", 5)]
    now[0] += ROOMS_REPORT_INTERVAL_SECONDS
    tracker.update(builder(roomsExplored=9), 2 * CHECK_INTERVAL_TICKS)
    assert scores(sent) == [("most-rooms", 5), ("most-rooms", 9)]
    # Leaving the world (force) reports the latest count at once.
    now[0] += 1
    tracker.update(builder(roomsExplored=10), 2 * CHECK_INTERVAL_TICKS + 1, True)
    assert scores(sent)[-1] == ("most-rooms", 10)


def test_an_error_while_checking_never_escapes(sent):
    def broken():
        raise RuntimeError("codex not loaded")

    tracker = Achievements()
    assert tracker.update(broken, 0, force=True) == []
    assert tracker.update(broken, 0, force=True) == []
    assert sent == []


def test_held_class_names_reads_every_slot():
    inventory = Inventory()
    inventory.placeIntoFirstAvailableInventorySlot(Apple())
    inventory.placeIntoFirstAvailableInventorySlot(GoldenLantern())
    assert heldClassNames(inventory) == {"Apple", "GoldenLantern"}
