from abc import ABC, abstractmethod


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# Backend-neutral input interface (frontend-abstraction epic #433, Phase 4).
#
# The input half of the seam: screens read events and key/mouse state through
# this interface instead of calling pygame.event / pygame.key / pygame.mouse
# directly, so the same screen logic runs behind any frontend. The pygame
# implementation (PygameInputSource) translates native pygame input into the
# neutral InputEvent / KeyCode model at the boundary.
class InputSource(ABC):
    @abstractmethod
    def pollEvents(self):
        """Return the queued input events as a list[InputEvent], draining the
        underlying queue (replaces pygame.event.get())."""

    @abstractmethod
    def isPressed(self, keyCode):
        """Whether the given KeyCode is currently held down (replaces
        pygame.key.get_pressed()[...])."""

    @abstractmethod
    def getMousePosition(self):
        """Current mouse position as an (x, y) tuple (replaces
        pygame.mouse.get_pos())."""

    @abstractmethod
    def getMouseButtons(self):
        """Current mouse button states as a tuple of bools, left-to-right
        (replaces pygame.mouse.get_pressed())."""
