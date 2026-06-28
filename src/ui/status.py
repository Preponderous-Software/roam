from appContainer import component
from rendering.renderer import Renderer
from ui.hotbarLayout import getHotbarTop
from world.tickCounter import TickCounter
from ui import palette
from ui.geometry import Rect


# @author Daniel McCoy Stephenson
# since August 14th, 2022
@component
class Status:
    def __init__(self, renderer: Renderer, tickCounter: TickCounter):
        self.renderer = renderer
        self.text = -1
        self.textSize = 18
        self.textColor = palette.BLACK
        self.tickLastSet = -1
        self.durationInTicks = 120
        self.tickCounter = tickCounter

    def set(self, text, duration=None):
        self.text = text
        self.tickLastSet = self.tickCounter.getTick()
        self._currentDuration = (
            duration if duration is not None else self.durationInTicks
        )

    def setHint(self, text):
        """Show text only when the status is currently empty (won't clobber action feedback)."""
        if self.text == -1:
            self.set(text, duration=60)

    def clear(self):
        self.text = -1
        self._currentDuration = self.durationInTicks

    def _calcWidth(self, displayW):
        raw = len(self.text) * 11
        return min(raw, int(displayW * 0.8))

    def getDefaultRect(self):
        """Return the default bounding rect for the status text (no drag offset)."""
        if self.text == -1:
            return Rect(0, 0, 0, 0)
        x, y = self.renderer.getDisplaySize()
        width = self._calcWidth(x)
        height = self.textSize * 2
        xpos = x / 2 - width / 2
        hotbarTop = getHotbarTop(y)
        ypos = hotbarTop - height - 10
        return Rect(xpos, ypos, width, height)

    def draw(self, offsetX=0, offsetY=0):
        if self.text == -1:
            return
        x, y = self.renderer.getDisplaySize()
        width = self._calcWidth(x)
        height = self.textSize * 2
        xpos = x / 2 - width / 2 + offsetX
        hotbarTop = getHotbarTop(y)
        ypos = hotbarTop - height - 10 + offsetY
        self.renderer.drawButton(
            xpos,
            ypos,
            width,
            height,
            palette.WHITE,
            self.textColor,
            self.textSize,
            self.text,
            self.clear,
        )

    def getTickLastSet(self):
        return self.tickLastSet

    def checkForExpiration(self, currentTick):
        duration = getattr(self, "_currentDuration", self.durationInTicks)
        expiryTick = self.tickLastSet + duration
        if currentTick > expiryTick:
            self.clear()
