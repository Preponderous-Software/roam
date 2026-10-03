"""Each arcade achievement unlocks on exactly the state it describes, and the
ids match what the gateway's boards.yaml declares (they are permanent)."""

import re

import pytest

from achievements.achievementRegistry import (
    EVENT_HARVESTED_WHEAT,
    EVENT_PLACED_CAMPFIRE,
    EVENT_RECOVERED_GRAVESTONE,
    getAchievements,
)
from achievements.achievements import AchievementContext
from codex.codex import ALL_LIVING_ENTITY_TYPES

DAY = 54000

EXPECTED_IDS = [
    "nightfall",
    "first-light",
    "one-full-day",
    "a-week-out",
    "wanderer",
    "far-roamer",
    "into-the-dark",
    "rock-bottom",
    "struck-gold",
    "naturalist",
    "well-fed",
    "hearth",
    "green-thumb",
    "lamplighter",
    "back-for-it",
]


def context(**overrides):
    values = dict(
        tick=0,
        dayLengthTicks=DAY,
        roomsExplored=1,
        foodEaten=0,
        discovered=[],
        heldClassNames=[],
        depth=0,
        deepestDepth=3,
        events=[],
    )
    values.update(overrides)
    return AchievementContext(**values)


def met(ctx):
    return {a.identifier for a in getAchievements() if a.isMet(ctx)}


def test_ids_are_the_declared_permanent_set():
    assert [a.identifier for a in getAchievements()] == EXPECTED_IDS


def test_ids_titles_and_descriptions_fit_arcade_social():
    for a in getAchievements():
        assert re.fullmatch(r"[a-z][a-z0-9-]{1,30}", a.identifier)
        assert a.title and a.description


def test_a_brand_new_world_has_nothing():
    assert met(context()) == set()


@pytest.mark.parametrize(
    "tick, expected",
    [
        (DAY // 2 - 1, set()),
        (DAY // 2, {"nightfall"}),
        (DAY * 3 // 4, {"nightfall", "first-light"}),
        (DAY, {"nightfall", "first-light", "one-full-day"}),
        (DAY * 7 - 1, {"nightfall", "first-light", "one-full-day"}),
        (DAY * 7, {"nightfall", "first-light", "one-full-day", "a-week-out"}),
    ],
)
def test_the_day_night_achievements_follow_the_world_tick(tick, expected):
    assert met(context(tick=tick)) == expected


def test_a_disabled_day_night_cycle_unlocks_no_day_achievements():
    assert met(context(tick=10**9, dayLengthTicks=0)) == set()


@pytest.mark.parametrize(
    "rooms, expected",
    [(24, set()), (25, {"wanderer"}), (100, {"wanderer", "far-roamer"})],
)
def test_exploring_rooms(rooms, expected):
    assert met(context(roomsExplored=rooms)) == expected


def test_into_the_dark_from_being_below_or_from_the_codex():
    assert met(context(depth=1)) == {"into-the-dark"}
    assert met(context(discovered=["CaveFloor"])) == {"into-the-dark"}


def test_rock_bottom_only_at_the_deepest_level():
    assert "rock-bottom" not in met(context(depth=2))
    assert met(context(depth=3)) == {"into-the-dark", "rock-bottom"}


def test_struck_gold_from_the_codex_or_the_bag():
    assert met(context(discovered=["GoldOre"])) == {"struck-gold"}
    assert met(context(heldClassNames=["GoldOre"])) == {"struck-gold"}


def test_naturalist_needs_every_creature():
    allButOne = ALL_LIVING_ENTITY_TYPES[:-1]
    assert "naturalist" not in met(context(discovered=allButOne))
    assert met(context(discovered=ALL_LIVING_ENTITY_TYPES)) == {"naturalist"}


def test_well_fed():
    assert met(context(foodEaten=49)) == set()
    assert met(context(foodEaten=50)) == {"well-fed"}


def test_hearth_from_placing_one_or_from_the_codex():
    assert met(context(events=[EVENT_PLACED_CAMPFIRE])) == {"hearth"}
    assert met(context(discovered=["Campfire"])) == {"hearth"}
    # Holding the crafted campfire is not building one.
    assert met(context(heldClassNames=["Campfire"])) == set()


def test_green_thumb_from_harvesting_or_from_wheat_in_the_save():
    assert met(context(events=[EVENT_HARVESTED_WHEAT])) == {"green-thumb"}
    assert met(context(heldClassNames=["Wheat"])) == {"green-thumb"}
    assert met(context(discovered=["Wheat"])) == {"green-thumb"}
    # Seeds and a growing crop are not a harvest.
    assert met(context(heldClassNames=["WheatSeed"], discovered=["YoungCrop"])) == set()


def test_lamplighter_from_the_bag_or_the_codex():
    assert met(context(heldClassNames=["GoldenLantern"])) == {"lamplighter"}
    assert met(context(discovered=["GoldenLantern"])) == {"lamplighter"}


def test_back_for_it_is_hidden_and_needs_the_event():
    (backForIt,) = [a for a in getAchievements() if a.identifier == "back-for-it"]
    assert backForIt.hidden
    assert met(context(discovered=["Gravestone"])) == set()
    assert met(context(events=[EVENT_RECOVERED_GRAVESTONE])) == {"back-for-it"}
    assert [a.identifier for a in getAchievements() if a.hidden] == ["back-for-it"]


def test_the_starting_home_alone_unlocks_nothing():
    # A new world's starting home holds a bed, a chest, a torch and wood
    # floors, and the player starts with apples and bananas.
    ctx = context(
        discovered=["Bed", "Chest", "Torch", "WoodFloor", "Grass", "OakWood"],
        heldClassNames=["Apple", "Banana"],
    )
    assert met(ctx) == set()
