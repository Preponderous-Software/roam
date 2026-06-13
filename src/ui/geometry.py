# @author Daniel McCoy Stephenson
# @since June 13th, 2026
#
# Backend-neutral geometry value types for the UI/layout layer
# (frontend-abstraction epic #433).
#
# HUD layout and hit-testing previously used pygame.Rect, which pulled pygame
# into otherwise backend-agnostic code. Rect mirrors the small slice of the
# pygame.Rect API the codebase actually uses (mutable x/y/width/height, the
# common edge/center accessors, collidepoint, copy, move) so a text or web
# frontend can lay out HUD elements without importing pygame. The pygame
# renderer converts to a real pygame.Rect only where it draws.


class Rect:
    __slots__ = ("x", "y", "width", "height")

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    # Edge / center accessors (read-only; mutate x/y directly to move).
    @property
    def left(self):
        return self.x

    @property
    def top(self):
        return self.y

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def centerx(self):
        return self.x + self.width // 2

    @property
    def centery(self):
        return self.y + self.height // 2

    @property
    def center(self):
        return (self.centerx, self.centery)

    def collidepoint(self, px, py):
        return (
            self.x <= px < self.x + self.width and self.y <= py < self.y + self.height
        )

    def move(self, dx, dy):
        return Rect(self.x + dx, self.y + dy, self.width, self.height)

    def copy(self):
        return Rect(self.x, self.y, self.width, self.height)

    def __eq__(self, other):
        return (
            isinstance(other, Rect)
            and self.x == other.x
            and self.y == other.y
            and self.width == other.width
            and self.height == other.height
        )

    def __repr__(self):
        return "Rect(%r, %r, %r, %r)" % (self.x, self.y, self.width, self.height)
