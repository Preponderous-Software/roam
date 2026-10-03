# @author Claude
# @since October 3rd, 2026
"""Roam's arcade achievements and leaderboards (Stephenson-Software RFC 0014).

The ids are permanent: arcade-social keys each player's unlocks by them, and
the gateway's config/play/boards.yaml declares the same ids, titles and
descriptions. Rename a title freely; never change or reuse an id.

Almost every condition is read from state a save already holds (stats, the
world's tick, the Codex, the inventory, the level the player is on), so
loading an existing world credits what it has already done. The few that
need a moment of play (placing a campfire, harvesting wheat, emptying a
gravestone) also accept lasting evidence of it where the save has some.
"""

from codex.codex import ALL_LIVING_ENTITY_TYPES

# Events WorldScreen reports as they happen (see Achievements.noteEvent).
EVENT_PLACED_CAMPFIRE = "placed:Campfire"
EVENT_HARVESTED_WHEAT = "harvested-wheat"
EVENT_RECOVERED_GRAVESTONE = "recovered-gravestone"

# Leaderboard ids.
BOARD_MOST_DAYS = "most-days"
BOARD_MOST_ROOMS = "most-rooms"


class Achievement:
    def __init__(self, identifier, title, description, condition, hidden=False):
        self.identifier = identifier
        self.title = title
        self.description = description
        self.condition = condition
        self.hidden = hidden

    def isMet(self, context):
        return bool(self.condition(context))


def _daysPassed(context, fraction):
    """True once the world has lived ``fraction`` of a day/night cycle."""
    length = context.dayLengthTicks
    return length > 0 and context.tick >= length * fraction


def _sawOrHolds(context, className):
    return context.hasDiscovered(className) or context.holds(className)


def getAchievements():
    return [
        # The day/night cycle (a world starts at midday: dusk falls a quarter
        # of the way through a cycle, night at half, dawn at three quarters).
        Achievement(
            "nightfall",
            "Nightfall",
            "See your first night fall",
            lambda c: _daysPassed(c, 0.5),
        ),
        Achievement(
            "first-light",
            "First Light",
            "Make it through your first night to the dawn",
            lambda c: _daysPassed(c, 0.75),
        ),
        Achievement(
            "one-full-day",
            "One Full Day",
            "Live through a whole day and night",
            lambda c: _daysPassed(c, 1),
        ),
        Achievement(
            "a-week-out",
            "A Week Out",
            "Live through seven days in one world",
            lambda c: _daysPassed(c, 7),
        ),
        # Exploration
        Achievement(
            "wanderer",
            "Wanderer",
            "Explore 25 rooms",
            lambda c: c.roomsExplored >= 25,
        ),
        Achievement(
            "far-roamer",
            "Far Roamer",
            "Explore 100 rooms",
            lambda c: c.roomsExplored >= 100,
        ),
        Achievement(
            "into-the-dark",
            "Into the Dark",
            "Climb down into a cave",
            lambda c: c.depth > 0 or c.hasDiscovered("CaveFloor"),
        ),
        Achievement(
            "rock-bottom",
            "Rock Bottom",
            "Reach the deepest level of the caves",
            lambda c: c.depth >= c.deepestDepth,
        ),
        Achievement(
            "struck-gold",
            "Struck Gold",
            "Find gold ore",
            lambda c: _sawOrHolds(c, "GoldOre"),
        ),
        Achievement(
            "naturalist",
            "Naturalist",
            "Find every creature for the Codex",
            lambda c: all(c.hasDiscovered(n) for n in ALL_LIVING_ENTITY_TYPES),
        ),
        # Survival and building
        Achievement(
            "well-fed",
            "Well Fed",
            "Eat 50 food",
            lambda c: c.foodEaten >= 50,
        ),
        Achievement(
            "hearth",
            "Hearth",
            "Build a campfire",
            lambda c: c.happened(EVENT_PLACED_CAMPFIRE) or c.hasDiscovered("Campfire"),
        ),
        Achievement(
            "green-thumb",
            "Green Thumb",
            "Harvest wheat you grew",
            lambda c: c.happened(EVENT_HARVESTED_WHEAT) or _sawOrHolds(c, "Wheat"),
        ),
        Achievement(
            "lamplighter",
            "Lamplighter",
            "Craft a golden lantern",
            lambda c: _sawOrHolds(c, "GoldenLantern"),
        ),
        Achievement(
            "back-for-it",
            "Back for It",
            "Recover your things from your gravestone",
            lambda c: c.happened(EVENT_RECOVERED_GRAVESTONE),
            hidden=True,
        ),
    ]
