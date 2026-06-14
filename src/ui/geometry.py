# @author Daniel McCoy Stephenson
# @since June 13th, 2026
#
# Backend-neutral geometry value types for the UI/layout layer
# (frontend-abstraction epic #433).
#
# HUD layout and hit-testing previously used pygame.Rect, which pulled pygame
# into otherwise backend-agnostic code. Rect mirrors the slice of the
# pygame.Rect API the codebase actually uses on these rects (mutable
# x/y/width/height, collidepoint, move, copy) so a text or web frontend can lay
# out HUD elements without importing pygame. The pygame renderer converts to a
# real pygame.Rect only where it draws. Edge/center accessors are intentionally
# omitted until a consumer needs one (and would be added as explicit getters,
# per the codebase's explicit-getter convention).


class Rect:
    __slots__ = ("x", "y", "width", "height", "right", "bottom")

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        # Convenience edges, mirroring pygame.Rect (consumers read gameArea.right
        # / .bottom). Rects here are used immutably — move()/copy() build a new
        # one — so these stay in sync.
        self.right = x + width
        self.bottom = y + height

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
