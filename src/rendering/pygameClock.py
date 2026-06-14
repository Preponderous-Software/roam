import pygame

from rendering.clock import Clock


# @author Daniel McCoy Stephenson
# @since June 14th, 2026
#
# pygame implementation of the frame-pacing Clock (epic #433 / #463): a thin
# wrapper over pygame.time.Clock so the game loop no longer references pygame
# for timing.
class PygameClock(Clock):
    def __init__(self):
        self._clock = pygame.time.Clock()

    def tick(self, fps):
        return self._clock.tick(fps)
