# @author Daniel McCoy Stephenson
from goals.goal import Goal


class GoalRegistry:
    """Defines the default set of progression goals.

    Goals rely only on state Roam already tracks (explored rooms, food eaten,
    Codex discoveries, the day/night cycle), so no new instrumentation is
    required for this initial set.
    """

    def getGoals(self):
        return [
            Goal(
                "explore_5_rooms",
                "Explore 5 rooms",
                5,
                lambda context: context.stats.getRoomsExplored(),
            ),
            Goal(
                "eat_10_food",
                "Eat 10 food",
                10,
                lambda context: context.stats.getFoodEaten(),
            ),
            Goal(
                "discover_3_entities",
                "Discover 3 entities in the Codex",
                3,
                lambda context: len(context.codex.getDiscoveredEntities()),
            ),
            Goal(
                "experience_nightfall",
                "Experience nightfall",
                1,
                lambda context: (
                    1
                    if context.dayNightCycle.getPhase(
                        context.tickCounter.getTick()
                    )
                    == "night"
                    else 0
                ),
            ),
        ]
