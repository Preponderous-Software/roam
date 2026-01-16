from math import ceil
from lib.graphik.src.graphik import Graphik
from player.player import Player


# @author Daniel McCoy Stephenson
# @since August 16th, 2022
class EnergyBar:
    def __init__(self, graphik: Graphik, player: Player):
        self.graphik = graphik
        self.player = player

    def draw(self):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = 0
        ypos = y - y / 64
        width = x * (self.player.getEnergy() / self.player.getTargetEnergy())
        height = y / 64
        color = (255, 215, 73)

        # draw black bar
        self.graphik.drawRectangle(xpos, ypos, x, height, (0, 0, 0))

        # draw white interior
        self.graphik.drawRectangle(
            xpos + 1, ypos + 1, x - 2, height - 2, (255, 255, 255)
        )

        # fill interior with energy
        self.graphik.drawRectangle(xpos + 1, ypos + 1, width - 2, height - 2, color)

        # draw text in center of bar
        text = (
            str(ceil(self.player.getEnergy()))
            + "/"
            + str(self.player.getTargetEnergy())
        )
        self.graphik.drawText(
            text, x / 2, ypos + height / 2, ceil(height) - 1, (0, 0, 0)
        )
