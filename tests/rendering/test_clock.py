import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from rendering.clock import Clock
from rendering.nullClock import NullClock
from rendering.pygameClock import PygameClock


def test_null_clock_never_blocks_and_reports_zero():
    clock = NullClock()
    assert isinstance(clock, Clock)
    assert clock.tick(30) == 0


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def test_pygame_clock_ticks_and_returns_elapsed_milliseconds():
    clock = PygameClock()
    assert isinstance(clock, Clock)
    elapsed = clock.tick(1000)  # high cap so the call returns promptly
    assert isinstance(elapsed, int)
    assert elapsed >= 0
