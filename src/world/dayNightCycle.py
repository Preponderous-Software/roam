import math

from appContainer import component
from config.config import Config


# @author Copilot
# @since April 20th, 2026
@component
class DayNightCycle:
    def __init__(self, config: Config):
        self.config = config

    def getOverlayOpacity(self, tick):
        """Return overlay opacity (0–200) for the given tick.

        Uses a cosine curve so that midday (tick % cycleLengthTicks == 0) maps
        to 0 (full brightness) and midnight (halfway point) maps to 200
        (near-dark).
        """
        cycleLengthTicks = self.config.dayNightCycleLengthTicks
        if cycleLengthTicks <= 0:
            return 0
        phase = (tick % cycleLengthTicks) / cycleLengthTicks
        # cos(0) = 1 → opacity 0 (midday), cos(pi) = -1 → opacity 200 (midnight)
        opacity = (1 - math.cos(2 * math.pi * phase)) / 2 * 200
        return int(round(opacity))

    def getPhase(self, tick):
        """Return the current cycle phase name: day, dusk, night, or dawn."""
        cycleLengthTicks = self.config.dayNightCycleLengthTicks
        if cycleLengthTicks <= 0:
            return "day"
        progress = (tick % cycleLengthTicks) / cycleLengthTicks
        if progress < 0.25:
            return "day"
        elif progress < 0.5:
            return "dusk"
        elif progress < 0.75:
            return "night"
        else:
            return "dawn"
