# @author Daniel McCoy Stephenson


class Goal:
    """A single progression goal.

    A goal measures progress with a function that receives a GoalContext and
    returns an integer (how far the player has gotten). The goal is complete
    once that value reaches the target.
    """

    def __init__(self, identifier, description, target, progressFunction):
        self.identifier = identifier
        self.description = description
        self.target = target
        self.progressFunction = progressFunction
        self.completed = False

    def getIdentifier(self):
        return self.identifier

    def getDescription(self):
        return self.description

    def getTarget(self):
        return self.target

    def isCompleted(self):
        return self.completed

    def setCompleted(self, completed):
        self.completed = completed

    def getProgress(self, context):
        """Return current progress toward the goal, clamped to the target."""
        progress = self.progressFunction(context)
        if progress > self.target:
            return self.target
        return progress

    def evaluate(self, context):
        """Recompute completion from the context.

        Returns True only when this call transitions the goal from incomplete
        to complete, so callers can react to fresh completions (e.g. a toast).
        """
        if self.completed:
            return False
        if self.progressFunction(context) >= self.target:
            self.completed = True
            return True
        return False
