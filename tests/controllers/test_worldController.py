import pytest
from unittest.mock import MagicMock

from controllers.worldController import WorldController
from services.saveService import SaveService
from services.worldService import WorldService
from services.entityService import EntityService
from world.roomPreloader import RoomPreloader


def makeController():
    saveService = MagicMock(spec=SaveService)
    worldService = MagicMock(spec=WorldService)
    entityService = MagicMock(spec=EntityService)
    roomPreloader = MagicMock(spec=RoomPreloader)
    controller = WorldController(saveService, worldService, entityService, roomPreloader)
    return controller, saveService, worldService, entityService, roomPreloader


def test_initialize_delegates_to_saveService():
    controller, saveService, _, _, _ = makeController()
    mapMock = MagicMock()
    saveService.loadAll.return_value = MagicMock()
    result = controller.initialize(mapMock)
    saveService.loadAll.assert_called_once_with(mapMock)
    assert result is saveService.loadAll.return_value


def test_save_delegates_to_saveService():
    controller, saveService, _, _, _ = makeController()
    room = MagicMock()
    controller.save(room)
    saveService.saveAll.assert_called_once_with(room)


def test_discoverLivingEntitiesInRoom_delegates():
    controller, _, _, entityService, _ = makeController()
    room = MagicMock()
    controller.discoverLivingEntitiesInRoom(room)
    entityService.discoverLivingEntitiesInRoom.assert_called_once_with(room)


def test_preloadNearbyRooms_delegates():
    controller, _, _, _, roomPreloader = makeController()
    mapMock = MagicMock()
    controller.preloadNearbyRooms(1, 2, mapMock)
    roomPreloader.preloadNearbyRooms.assert_called_once_with(1, 2, mapMock)
