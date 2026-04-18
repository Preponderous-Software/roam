from lib.graphik.src.graphik import Graphik
from world.tickCounter import TickCounter


# @author Daniel McCoy Stephenson
# since August 14th, 2022
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

    def draw(self):
        if self.text == -1:
            return
        x, y = self.graphik.getGameDisplay().get_size()
        width = len(self.text) * 10
        height = self.textSize * 2
        xpos = x / 2 - width / 2
        hotbarTop = y - 50 * 3 - 5
        ypos = hotbarTop - height - 10
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
