from math import ceil
from appContainer import component
from rendering.renderer import Renderer
from player.player import Player
from ui import palette
from ui.geometry import Rect


# @author Daniel McCoy Stephenson
# @since August 16th, 2022
@component
class EnergyBar:
    def __init__(self, renderer: Renderer, player: Player):
        self.renderer = renderer
        self.player = player

    def getDefaultRect(self):
        """Return the default bounding rect for the energy bar (no drag offset)."""
        x, y = self.renderer.getDisplaySize()
        xpos = 0
        ypos = y - y / 64
        width = x
        height = y / 64
        return Rect(xpos, ypos, width, height)

    def draw(self, offsetX=0, offsetY=0):
        x, y = self.renderer.getDisplaySize()
        xpos = 0 + offsetX
        ypos = y - y / 64 + offsetY
        energyRatio = self.player.getEnergy() / self.player.getTargetEnergy()

        if not self.renderer.supportsImageLoading():
            self._drawText(xpos, ypos, energyRatio)
            return

        width = x * energyRatio
        fullWidth = x
        height = y / 64
        if energyRatio < 0.10:
            color = (220, 60, 60)
        elif energyRatio < 0.25:
            color = (240, 160, 60)
        else:
            color = (255, 215, 73)

        # draw black bar
        self.renderer.drawRectangle(xpos, ypos, fullWidth, height, palette.BLACK)

        # draw white interior
        self.renderer.drawRectangle(
            xpos + 1, ypos + 1, fullWidth - 2, height - 2, palette.WHITE
        )

        # fill interior with energy
        self.renderer.drawRectangle(xpos + 1, ypos + 1, width - 2, height - 2, color)

    def _drawText(self, xpos, ypos, energyRatio):
        BAR_WIDTH = 16
        filled = max(0, min(BAR_WIDTH, round(energyRatio * BAR_WIDTH)))
        bar = "=" * filled + " " * (BAR_WIDTH - filled)
        energy = ceil(self.player.getEnergy())
        target = self.player.getTargetEnergy()
        label = f"E:[{bar}] {energy}/{target}"
        self.renderer.drawTextLeftAligned(label, xpos, ypos, 12, palette.WHITE)
