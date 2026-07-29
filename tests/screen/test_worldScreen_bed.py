import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from unittest.mock import MagicMock

from entity.bed import Bed
from entity.stoneBed import StoneBed


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def createWorldScreen():
    from config.config import Config
    from screen.worldScreen import WorldScreen

    config = Config()
    gameDisplay = pygame.display.set_mode((800, 600))
    graphik = MagicMock()
    graphik.getGameDisplay.return_value = gameDisplay
    status = MagicMock()
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = config
    ws.graphik = graphik
    ws.status = status
    ws._isRunning = False
    ws._isCrouching = False
    return ws


def createMockPlayer(energy=20):
    player = MagicMock()

    state = {"energy": energy}

    def setEnergy(value):
        state["energy"] = max(0, min(100, value))

    def addEnergy(amount):
        state["energy"] = max(0, min(100, state["energy"] + amount))

    def getEnergy():
        return state["energy"]

    player.setEnergy.side_effect = setEnergy
    player.addEnergy.side_effect = addEnergy
    player.getEnergy.side_effect = getEnergy
    return player


def test_sleep_in_bed_fully_restores_energy():
    ws = createWorldScreen()
    ws.player = createMockPlayer(energy=10)

    bed = Bed()
    ws._sleepInBed(bed)

    ws.player.setEnergy.assert_called_once_with(100)
    assert ws.player.getEnergy() == 100
    ws.status.set.assert_called_with("Slept in the Bed")


def test_sleep_in_stone_bed_partially_restores_energy():
    ws = createWorldScreen()
    ws.player = createMockPlayer(energy=10)

    stoneBed = StoneBed()
    ws._sleepInBed(stoneBed)

    ws.player.addEnergy.assert_called_once_with(50)
    assert ws.player.getEnergy() == 60
    ws.status.set.assert_called_with("Rested on the Stone Bed")


def test_execute_place_at_dispatches_bed_interaction_without_placing():
    ws = createWorldScreen()
    ws.player = createMockPlayer(energy=10)
    ws._sleepInBed = MagicMock()

    bed = Bed()
    targetLocation = MagicMock()
    targetLocation.getEntities.return_value = {1: bed}
    targetLocation.getEntity.return_value = bed
    targetRoom = MagicMock()

    ws._executePlaceAt(targetLocation, targetRoom)

    ws._sleepInBed.assert_called_once_with(bed)
    # Placement logic must not run once the special interaction has fired.
    ws.player.getInventory.assert_not_called()
