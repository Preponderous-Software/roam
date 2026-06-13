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
        self.durationInTicks = 60
        self.tickCounter = tickCounter

    def set(self, text):
        self.text = text
        self.tickLastSet = self.tickCounter.getTick()

    def clear(self):
        self.text = -1

    def getDefaultRect(self):
        """Return the default bounding rect for the status text (no drag offset)."""
        if self.text == -1:
            return Rect(0, 0, 0, 0)
        x, y = self.renderer.getDisplaySize()
        width = len(self.text) * 10
        height = self.textSize * 2
        xpos = x / 2 - width / 2
        hotbarTop = getHotbarTop(y)
        ypos = hotbarTop - height - 10
        return Rect(xpos, ypos, width, height)

    def draw(self, offsetX=0, offsetY=0):
        if self.text == -1:
            return
        x, y = self.renderer.getDisplaySize()
        width = len(self.text) * 10
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
        expiryTick = self.tickLastSet + self.durationInTicks
        if currentTick > expiryTick:
            self.clear()
