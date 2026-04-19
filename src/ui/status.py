import pygame
from appContainer import component
from lib.graphik.src.graphik import Graphik
from ui.hotbarLayout import getHotbarTop
from world.tickCounter import TickCounter


# @author Daniel McCoy Stephenson
# since August 14th, 2022
@component
class Status:
    def __init__(self, graphik: Graphik, tickCounter: TickCounter):
        self.graphik = graphik
        self.text = -1
        self.textSize = 18
        self.textColor = (0, 0, 0)
        self.tickLastSet = -1
        self.durationInTicks = 20
        self.tickCounter = tickCounter

    def set(self, text):
        self.text = text
        self.tickLastSet = self.tickCounter.getTick()

    def clear(self):
        self.text = -1

    def getDefaultRect(self):
        """Return the default bounding rect for the status text (no drag offset)."""
        if self.text == -1:
            return pygame.Rect(0, 0, 0, 0)
        x, y = self.graphik.getGameDisplay().get_size()
        width = len(self.text) * 10
        height = self.textSize * 2
        xpos = x / 2 - width / 2
        hotbarTop = getHotbarTop(y)
        ypos = hotbarTop - height - 10
        return pygame.Rect(xpos, ypos, width, height)

    def draw(self, offsetX=0, offsetY=0):
        if self.text == -1:
            return
        x, y = self.graphik.getGameDisplay().get_size()
        width = len(self.text) * 10
        height = self.textSize * 2
        xpos = x / 2 - width / 2 + offsetX
        hotbarTop = getHotbarTop(y)
        ypos = hotbarTop - height - 10 + offsetY
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
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
