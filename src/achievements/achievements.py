# @author Claude
# @since October 3rd, 2026
import time

from achievements import arcadeBridge
from achievements.achievementRegistry import (
    BOARD_MOST_DAYS,
    BOARD_MOST_ROOMS,
    getAchievements,
)
from appContainer import component
from gameLogging.logger import getLogger

_logger = getLogger(__name__)

# How often (in ticks) the conditions are re-checked during play; an event
# (noteEvent) forces the next update to check at once.
CHECK_INTERVAL_TICKS = 30
# The most-rooms board changes every few seconds while exploring, so it is
# reported at most this often (and once more when the world is left).
ROOMS_REPORT_INTERVAL_SECONDS = 120


class AchievementContext:
    """What the achievement conditions read, gathered from the world."""

    def __init__(
        self,
        tick,
        dayLengthTicks,
        roomsExplored,
        foodEaten,
        discovered,
        heldClassNames,
        depth,
        deepestDepth,
        events,
    ):
        self.tick = tick
        self.dayLengthTicks = dayLengthTicks
        self.roomsExplored = roomsExplored
        self.foodEaten = foodEaten
        self.discovered = set(discovered)
        self.heldClassNames = set(heldClassNames)
        self.depth = depth
        self.deepestDepth = deepestDepth
        self.events = set(events)

    def hasDiscovered(self, className):
        return className in self.discovered

    def holds(self, className):
        return className in self.heldClassNames

    def happened(self, event):
        return event in self.events


def heldClassNames(inventory):
    names = set()
    for slot in inventory.getInventorySlots():
        for item in slot.getContents():
            names.add(item.__class__.__name__)
    return names


@component
class Achievements:
    """Checks Roam's arcade achievements and reports them through the bridge.

    Does nothing at all unless the bridge is active (the browser build on
    arcade), and never lets an error escape into the game loop.
    """

    def __init__(self):
        self.achievements = getAchievements()
        self._events = set()
        self._lastCheckTick = None
        self._lastRoomsReport = None
        self._failed = False

    def noteEvent(self, event):
        """Record something that just happened in play (see the registry)."""
        self._events.add(event)
        self._lastCheckTick = None

    def getEvents(self):
        return set(self._events)

    def update(self, buildContext, tick, force=False):
        """Check the conditions if one is due; ``buildContext()`` is only
        called when a check runs. ``force`` checks now (a world was loaded)
        and reports the most-rooms board regardless of its interval (a world
        is being left)."""
        if not arcadeBridge.isActive():
            return []
        due = (
            force
            or self._lastCheckTick is None
            or tick - self._lastCheckTick >= CHECK_INTERVAL_TICKS
            or tick < self._lastCheckTick
        )
        if not due:
            return []
        self._lastCheckTick = tick
        try:
            return self._check(buildContext(), force)
        except Exception as e:
            if not self._failed:  # log once, not every second
                self._failed = True
                _logger.warning("achievement check failed", error=str(e))
            return []

    def _check(self, context, force):
        met = []
        for achievement in self.achievements:
            if achievement.isMet(context):
                met.append(achievement)
                arcadeBridge.unlock(achievement.identifier, achievement.title)

        if context.dayLengthTicks > 0:
            days = context.tick // context.dayLengthTicks
            if days >= 1:
                arcadeBridge.submitScore(BOARD_MOST_DAYS, days)

        now = time.monotonic()
        if context.roomsExplored >= 2 and (
            force
            or self._lastRoomsReport is None
            or now - self._lastRoomsReport >= ROOMS_REPORT_INTERVAL_SECONDS
        ):
            self._lastRoomsReport = now
            arcadeBridge.submitScore(BOARD_MOST_ROOMS, context.roomsExplored)
        return met
