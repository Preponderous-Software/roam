# @author Daniel McCoy Stephenson
from appContainer import component

from stats.stats import Stats
from codex.codex import Codex
from world.dayNightCycle import DayNightCycle
from world.tickCounter import TickCounter
from goals.goalRegistry import GoalRegistry
from goals.goalContext import GoalContext
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


@component
class Goals:
    """Tracks the player's progression goals and their completion state."""

    def __init__(
        self,
        stats: Stats,
        codex: Codex,
        dayNightCycle: DayNightCycle,
        tickCounter: TickCounter,
    ):
        self.stats = stats
        self.codex = codex
        self.dayNightCycle = dayNightCycle
        self.tickCounter = tickCounter
        self.goals = GoalRegistry().getGoals()

    def _buildContext(self):
        return GoalContext(self.stats, self.codex, self.dayNightCycle, self.tickCounter)

    def evaluate(self):
        """Re-evaluate every goal.

        Returns the goals that were newly completed by this call so the caller
        can surface them (e.g. a status message).
        """
        context = self._buildContext()
        newlyCompleted = []
        for goal in self.goals:
            if goal.evaluate(context):
                newlyCompleted.append(goal)
                _logger.info("goal completed", goal=goal.getIdentifier())
        return newlyCompleted

    def getGoals(self):
        return self.goals

    def getProgress(self, goal):
        return goal.getProgress(self._buildContext())

    def getCompletedCount(self):
        return sum(1 for goal in self.goals if goal.isCompleted())

    def getTotalCount(self):
        return len(self.goals)

    def getCompletedIdentifiers(self):
        return [goal.getIdentifier() for goal in self.goals if goal.isCompleted()]

    def setCompletedIdentifiers(self, identifiers):
        completed = set(identifiers)
        for goal in self.goals:
            goal.setCompleted(goal.getIdentifier() in completed)
