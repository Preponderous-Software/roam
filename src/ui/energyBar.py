from math import ceil
import pygame
from appContainer import component
from lib.graphik.src.graphik import Graphik
from player.player import Player


# @author Daniel McCoy Stephenson
# @since August 16th, 2022
@component
class EnergyBar:
    def __init__(self, graphik: Graphik, player: Player):
        self.graphik = graphik
        self.player = player

    def getDefaultRect(self):
        """Return the default bounding rect for the energy bar (no drag offset)."""
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = 0
        ypos = y - y / 64
        width = x
        height = y / 64
        return pygame.Rect(xpos, ypos, width, height)

    def draw(self, offsetX=0, offsetY=0):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = 0 + offsetX
        ypos = y - y / 64 + offsetY
        width = x * (self.player.getEnergy() / self.player.getTargetEnergy())
        fullWidth = x
        height = y / 64
        color = (255, 215, 73)

        # draw black bar
        self.graphik.drawRectangle(xpos, ypos, fullWidth, height, (0, 0, 0))

        # draw white interior
        self.graphik.drawRectangle(
            xpos + 1, ypos + 1, fullWidth - 2, height - 2, (255, 255, 255)
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
            text, xpos + fullWidth / 2, ypos + height / 2, ceil(height) - 1, (0, 0, 0)
        )
