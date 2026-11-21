from abc import ABC, abstractmethod


class BackgroundRunner(ABC):
    """Runs a task off the game thread.

    Contract:
    - `start(target, args)` arranges for `target(*args)` to run and returns
      without waiting for it (a fake may run it inline).
    - The task must not keep the process alive at exit.
    - `target` handles its own errors; the runner does not report them.
    """

    @abstractmethod
    def start(self, target, args):
        """Run `target(*args)` in the background."""
