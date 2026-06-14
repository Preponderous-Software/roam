from abc import ABC, abstractmethod


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Backend-neutral frame-pacing interface (frontend-abstraction epic #433,
# follow-up #463). The game loop limits its frame rate through this instead of
# pygame.time.Clock, so the same loop runs behind any frontend; the pygame
# implementation wraps pygame.time.Clock and a text/web frontend supplies its
# own pacing (or a no-op).
class Clock(ABC):
    @abstractmethod
    def tick(self, fps):
        """Block as needed so the loop runs at most `fps` times per second.
        Returns the milliseconds since the previous tick."""
