import pytest
from unittest.mock import MagicMock

from services.entityService import EntityService
from codex.codex import Codex
from config.config import Config
from player.player import Player
from stats.stats import Stats
from ui.status import Status
from world.tickCounter import TickCounter
from repositories.codexRepository import CodexRepository
from entity.living.chicken import Chicken
from entity.living.bear import Bear


def makeService():
    config = MagicMock(spec=Config)
    config.playerInteractionEnergyCost = 1
    player = MagicMock(spec=Player)
    stats = MagicMock(spec=Stats)
    status = MagicMock(spec=Status)
    tickCounter = MagicMock(spec=TickCounter)
    tickCounter.getTick.return_value = 100
    codex = MagicMock(spec=Codex)
    codexRepository = MagicMock(spec=CodexRepository)
    return EntityService(config, player, stats, status, tickCounter, codex, codexRepository), codex, codexRepository


def makeRoom(entities=None):
    room = MagicMock()
    livingEntities = entities or {}
    room.getLivingEntities.return_value = livingEntities
    room.getEntity.side_effect = lambda eid: livingEntities.get(eid)
    room.getName.return_value = "TestRoom"
    return room


def test_discoverLivingEntitiesInRoom_discovers_new_entity():
    service, codex, codexRepo = makeService()
    chicken = MagicMock(spec=Chicken)
    chicken.__class__ = Chicken
    room = makeRoom({1: chicken})
    codex.discover.return_value = True
    service.discoverLivingEntitiesInRoom(room)
    codex.discover.assert_called_with("Chicken")
    codexRepo.save.assert_called_once_with(codex)


def test_discoverLivingEntitiesInRoom_already_discovered():
    service, codex, codexRepo = makeService()
    chicken = MagicMock(spec=Chicken)
    chicken.__class__ = Chicken
    room = makeRoom({1: chicken})
    codex.discover.return_value = False
    service.discoverLivingEntitiesInRoom(room)
    codexRepo.save.assert_not_called()


def test_checkForLivingEntityDeaths_removes_dead():
    service, codex, codexRepo = makeService()
    chicken = MagicMock(spec=Chicken)
    chicken.__class__ = Chicken
    chicken.getEnergy.return_value = 0
    chicken.getLocationID.return_value = "-1"
    room = MagicMock()
    room.getLivingEntities.return_value = {1: chicken}
    room.getEntity.side_effect = lambda eid: {1: chicken}.get(eid)
    room.getName.return_value = "TestRoom"
    service.checkForLivingEntityDeaths(room)
    room.removeEntity.assert_called_with(chicken)
    room.removeLivingEntity.assert_called_with(chicken)


def test_checkForLivingEntityDeaths_keeps_alive():
    service, codex, codexRepo = makeService()
    chicken = MagicMock(spec=Chicken)
    chicken.getEnergy.return_value = 50
    room = makeRoom({1: chicken})
    service.checkForLivingEntityDeaths(room)
    room.removeEntity.assert_not_called()
