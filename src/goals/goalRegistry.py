# @author Daniel McCoy Stephenson
from goals.goal import Goal
from codex.codex import ALL_LIVING_ENTITY_TYPES


def _discovered(context, name):
    return 1 if name in context.codex.getDiscoveredEntities() else 0


def _discoveredCreatureCount(context):
    discovered = context.codex.getDiscoveredEntities()
    return sum(1 for name in ALL_LIVING_ENTITY_TYPES if name in discovered)


def _isPhase(context, phase):
    return (
        1
        if context.dayNightCycle.getPhase(context.tickCounter.getTick()) == phase
        else 0
    )


class GoalRegistry:
    """Defines the default set of progression goals.

    Goals rely only on state Roam already tracks (explored rooms, food eaten,
    score, Codex discoveries, the day/night cycle), so no new instrumentation
    is required.
    """

    def getGoals(self):
        return [
            # Exploration
            Goal(
                "explore_5_rooms",
                "Explore 5 rooms",
                5,
                lambda context: context.stats.getRoomsExplored(),
            ),
            Goal(
                "explore_25_rooms",
                "Explore 25 rooms",
                25,
                lambda context: context.stats.getRoomsExplored(),
            ),
            Goal(
                "explore_100_rooms",
                "Explore 100 rooms",
                100,
                lambda context: context.stats.getRoomsExplored(),
            ),
            # Food / survival
            Goal(
                "eat_10_food",
                "Eat 10 food",
                10,
                lambda context: context.stats.getFoodEaten(),
            ),
            Goal(
                "eat_50_food",
                "Eat 50 food",
                50,
                lambda context: context.stats.getFoodEaten(),
            ),
            # Codex discovery
            Goal(
                "discover_chicken",
                "Discover a Chicken",
                1,
                lambda context: _discovered(context, "Chicken"),
            ),
            Goal(
                "discover_bear",
                "Discover a Bear",
                1,
                lambda context: _discovered(context, "Bear"),
            ),
            Goal(
                "discover_all_creatures",
                "Discover every creature",
                len(ALL_LIVING_ENTITY_TYPES),
                _discoveredCreatureCount,
            ),
            # Day / night cycle
            Goal(
                "experience_nightfall",
                "Experience nightfall",
                1,
                lambda context: _isPhase(context, "night"),
            ),
            Goal(
                "witness_dawn",
                "Witness the dawn",
                1,
                lambda context: _isPhase(context, "dawn"),
            ),
            # Score milestones
            Goal(
                "reach_score_25",
                "Reach a score of 25",
                25,
                lambda context: context.stats.getScore(),
            ),
            Goal(
                "reach_score_100",
                "Reach a score of 100",
                100,
                lambda context: context.stats.getScore(),
            ),
        ]
