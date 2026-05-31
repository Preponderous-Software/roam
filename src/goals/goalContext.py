# @author Daniel McCoy Stephenson


class GoalContext:
    """A snapshot of the game state that goals are evaluated against.

    Bundling the relevant systems here keeps individual goal conditions
    decoupled from how those systems are wired together.
    """

    def __init__(self, stats, codex, dayNightCycle, tickCounter):
        self.stats = stats
        self.codex = codex
        self.dayNightCycle = dayNightCycle
        self.tickCounter = tickCounter
