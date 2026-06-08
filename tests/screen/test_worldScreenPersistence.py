import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from unittest.mock import MagicMock

from jsonPersistence import readJsonFile
from screen.worldScreenPersistence import WorldScreenPersistence


# --- player attributes -------------------------------------------------------


def test_player_attributes_round_trip(resolve):
    wsp = resolve(WorldScreenPersistence)
    wsp.player.setEnergy(42)
    wsp.savePlayerAttributesToFile()

    wsp.player.setEnergy(1)
    wsp.loadPlayerAttributesFromFile()

    assert wsp.player.getEnergy() == 42


def test_load_player_attributes_missing_file_is_noop(resolve):
    wsp = resolve(WorldScreenPersistence)
    wsp.player.setEnergy(73)
    wsp.loadPlayerAttributesFromFile()  # no file on disk
    assert wsp.player.getEnergy() == 73


def test_load_player_attributes_corrupt_file_is_noop(resolve, test_config, tmp_path):
    # Regression tie-in with #370/#426: a corrupt save must not crash the load.
    wsp = resolve(WorldScreenPersistence)
    with open(str(tmp_path / "playerAttributes.json"), "w") as f:
        f.write("{ not valid json")

    wsp.player.setEnergy(55)
    wsp.loadPlayerAttributesFromFile()
    assert wsp.player.getEnergy() == 55


# --- player location ---------------------------------------------------------


def test_save_player_location_writes_expected_json(resolve, test_config, tmp_path):
    wsp = resolve(WorldScreenPersistence)
    wsp.player.setLocationID("loc-1")
    currentRoom = MagicMock()
    currentRoom.getX.return_value = 2
    currentRoom.getY.return_value = -3

    wsp.savePlayerLocationToFile(currentRoom)

    data = readJsonFile(str(tmp_path / "playerLocation.json"))
    assert data == {"roomX": 2, "roomY": -3, "locationId": "loc-1"}


def test_load_player_location_missing_file_returns_none(resolve):
    wsp = resolve(WorldScreenPersistence)
    assert wsp.loadPlayerLocationFromFile(MagicMock()) is None


def test_load_player_location_room_not_found_returns_none(resolve):
    wsp = resolve(WorldScreenPersistence)
    wsp.player.setLocationID("loc-1")
    wsp.savePlayerLocationToFile(_room(4, 5))

    mapInstance = MagicMock()
    mapInstance.getRoom.return_value = -1  # saved room no longer exists

    assert wsp.loadPlayerLocationFromFile(mapInstance) is None


def test_load_player_location_happy_path(resolve):
    wsp = resolve(WorldScreenPersistence)
    wsp.player.setLocationID("loc-1")
    wsp.savePlayerLocationToFile(_room(4, 5))

    location = MagicMock()
    loadedRoom = MagicMock()
    loadedRoom.getGrid.return_value.getLocation.return_value = location
    mapInstance = MagicMock()
    mapInstance.getRoom.return_value = loadedRoom

    result = wsp.loadPlayerLocationFromFile(mapInstance)

    assert result is loadedRoom
    mapInstance.getRoom.assert_called_once_with(4, 5)
    loadedRoom.addEntityToLocation.assert_called_once_with(wsp.player, location)


# --- player inventory (delegation) ------------------------------------------


def test_save_player_inventory_delegates(resolve, test_config):
    wsp = resolve(WorldScreenPersistence)
    invRW = MagicMock()

    wsp.savePlayerInventoryToFile(invRW)

    invRW.saveInventory.assert_called_once_with(
        wsp.player.getInventory(),
        test_config.pathToSaveDirectory + "/playerInventory.json",
    )


def test_load_player_inventory_sets_inventory_when_present(resolve):
    wsp = resolve(WorldScreenPersistence)
    invRW = MagicMock()
    loadedInventory = MagicMock()
    invRW.loadInventory.return_value = loadedInventory

    wsp.loadPlayerInventoryFromFile(invRW)

    assert wsp.player.getInventory() is loadedInventory


def test_load_player_inventory_keeps_existing_when_none(resolve):
    wsp = resolve(WorldScreenPersistence)
    original = wsp.player.getInventory()
    invRW = MagicMock()
    invRW.loadInventory.return_value = None

    wsp.loadPlayerInventoryFromFile(invRW)

    assert wsp.player.getInventory() is original


# --- room save ---------------------------------------------------------------


def test_save_room_to_file_writes_to_expected_path(resolve, test_config):
    wsp = resolve(WorldScreenPersistence)
    wsp.roomJsonReaderWriter = MagicMock()
    wsp.roomJsonReaderWriter.generateJsonForRoom.return_value = {"x": 1, "y": 1}

    wsp.saveRoomToFile(_room(1, 1))

    expectedPath = test_config.getRoomFilePath(1, 1)
    assert readJsonFile(expectedPath) == {"x": 1, "y": 1}


def _room(x, y):
    room = MagicMock()
    room.getX.return_value = x
    room.getY.return_value = y
    return room
