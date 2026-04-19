# @author Copilot
# @since April 18th, 2026

from appContainer import component

MINIMUM_VISIBLE_FRACTION = 0.2


class HudElement:
    """Represents a draggable HUD element with a name, default position, and current offset."""

    def __init__(self, name, rectFunc):
        self.name = name
        self.rectFunc = rectFunc
        self.offsetX = 0
        self.offsetY = 0

    def getRect(self):
        """Return the current bounding rect (default + offset)."""
        rect = self.rectFunc()
        rect.x += self.offsetX
        rect.y += self.offsetY
        return rect

    def getOffset(self):
        return (self.offsetX, self.offsetY)

    def setOffset(self, ox, oy):
        self.offsetX = ox
        self.offsetY = oy


def clampPosition(x, y, elementWidth, elementHeight, screenWidth, screenHeight):
    """Clamp x, y so at least MINIMUM_VISIBLE_FRACTION of the element remains visible on screen."""
    minX = -elementWidth * (1 - MINIMUM_VISIBLE_FRACTION)
    maxX = screenWidth - elementWidth * MINIMUM_VISIBLE_FRACTION
    minY = -elementHeight * (1 - MINIMUM_VISIBLE_FRACTION)
    maxY = screenHeight - elementHeight * MINIMUM_VISIBLE_FRACTION
    cx = max(minX, min(x, maxX))
    cy = max(minY, min(y, maxY))
    return (cx, cy)


@component
class HudDragManager:
    """Manages drag state for all registered HUD elements."""

    def __init__(self):
        self.elements = {}
        self.dragging = None
        self.dragStartMouseX = 0
        self.dragStartMouseY = 0
        self.dragStartOffsetX = 0
        self.dragStartOffsetY = 0

    def register(self, name, rectFunc):
        """Register a HUD element by name with a callable that returns its default pygame.Rect."""
        self.elements[name] = HudElement(name, rectFunc)

    def getOffset(self, name):
        """Return (offsetX, offsetY) for the named element."""
        if name in self.elements:
            return self.elements[name].getOffset()
        return (0, 0)

    def isDragging(self):
        """Return True if any element is currently being dragged."""
        return self.dragging is not None

    def handleMouseDown(self, mouseX, mouseY):
        """Begin dragging the last-registered HUD element under the cursor. Returns True if a drag started."""
        for name, element in reversed(list(self.elements.items())):
            rect = element.getRect()
            if rect.collidepoint(mouseX, mouseY):
                self.dragging = name
                self.dragStartMouseX = mouseX
                self.dragStartMouseY = mouseY
                self.dragStartOffsetX = element.offsetX
                self.dragStartOffsetY = element.offsetY
                return True
        return False

    def handleMouseMotion(self, mouseX, mouseY, screenWidth, screenHeight):
        """Update the offset of the element being dragged. Returns True if a drag is active."""
        if self.dragging is None:
            return False
        element = self.elements[self.dragging]
        dx = mouseX - self.dragStartMouseX
        dy = mouseY - self.dragStartMouseY
        newOffsetX = self.dragStartOffsetX + dx
        newOffsetY = self.dragStartOffsetY + dy

        # Compute the default rect to find the element size and default position
        defaultRect = element.rectFunc()
        newX = defaultRect.x + newOffsetX
        newY = defaultRect.y + newOffsetY
        clampedX, clampedY = clampPosition(
            newX, newY, defaultRect.width, defaultRect.height, screenWidth, screenHeight
        )
        element.offsetX = clampedX - defaultRect.x
        element.offsetY = clampedY - defaultRect.y
        return True

    def handleMouseUp(self, mouseX, mouseY, screenWidth, screenHeight):
        """Finish dragging. Returns True if a drag was in progress."""
        if self.dragging is None:
            return False
        # Apply final clamped position
        self.handleMouseMotion(mouseX, mouseY, screenWidth, screenHeight)
        self.dragging = None
        return True
