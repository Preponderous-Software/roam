import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import MagicMock

from config.config import Config
from stats.stats import Stats


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def createWorldScreenWithDeadPlayer(score):
    from screen.worldScreen import WorldScreen

    config = Config()
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.status = MagicMock()
    ws.deathRespawnTicksRemaining = 0

    stats = Stats(config)
    stats.setScore(score)
    ws.stats = stats

    player = MagicMock()
    player.isDead.return_value = True
    player.getEnergy.return_value = 0
    player.getTargetEnergy.return_value = 100
    ws.player = player

    return ws


# ---------------------------------------------------------------------------
# removeEnergyAndCheckForPlayerDeath — score penalty on death
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "startScore, expectedScore",
    [
        (1, 0),  # ceil would have left this at 1 (penalty negated)
        (9, 8),  # ceil would have left this at 9 (penalty negated)
        (10, 9),  # first score the old ceil logic actually reduced
        (25, 22),  # floor(22.5) — penalty always applied
        (100, 90),
    ],
)
def test_death_penalty_always_reduces_score(startScore, expectedScore):
    ws = createWorldScreenWithDeadPlayer(startScore)
    ws.removeEnergyAndCheckForPlayerDeath()
    assert ws.stats.getScore() == expectedScore


def test_death_increments_number_of_deaths():
    ws = createWorldScreenWithDeadPlayer(50)
    ws.removeEnergyAndCheckForPlayerDeath()
    assert ws.stats.getNumberOfDeaths() == 1
