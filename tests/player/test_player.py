from unittest.mock import MagicMock

from player import player


def createPlayerInstance(resolve):
    return resolve(player.Player)


def test_initialization(resolve, monkeypatch):
    # call
    inventoryConstructor = MagicMock()
    monkeypatch.setattr(player, "Inventory", inventoryConstructor)
    playerInstance = createPlayerInstance(resolve)

    # check
    assert playerInstance.getDirection() == -1
    assert playerInstance.getLastDirection() == -1
    assert playerInstance.isGathering() == False
    assert playerInstance.isPlacing() == False
    assert playerInstance.isDead() == False
    assert playerInstance.getTickLastMoved() == -1
    assert playerInstance.getMovementSpeed() == 30
    assert playerInstance.getGatherSpeed() == 30
    assert playerInstance.getPlaceSpeed() == 30
    assert playerInstance.isCrouching() == False
    assert playerInstance.isSolid() == False

    inventoryConstructor.assert_called_once()


def test_set_direction_up(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setDirection(0)

    # check
    assert playerInstance.getDirection() == 0
    assert playerInstance.getLastDirection() == -1
    assert playerInstance.imagePath == "assets/images/player_up.png"


def test_set_direction_left(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setDirection(1)

    # check
    assert playerInstance.getDirection() == 1
    assert playerInstance.getLastDirection() == -1
    assert playerInstance.imagePath == "assets/images/player_left.png"


def test_set_direction_down(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setDirection(2)

    # check
    assert playerInstance.getDirection() == 2
    assert playerInstance.getLastDirection() == -1
    assert playerInstance.imagePath == "assets/images/player_down.png"


def test_set_direction_right(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setDirection(3)

    # check
    assert playerInstance.getDirection() == 3
    assert playerInstance.getLastDirection() == -1
    assert playerInstance.imagePath == "assets/images/player_right.png"


def test_set_gathering(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setGathering(True)

    # check
    assert playerInstance.isGathering() == True


def test_set_placing(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setPlacing(True)

    # check
    assert playerInstance.isPlacing() == True


def test_set_tick_last_moved(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setTickLastMoved(10)

    # check
    assert playerInstance.getTickLastMoved() == 10


def test_set_inventory(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)
    inventory = MagicMock()

    # call
    playerInstance.setInventory(inventory)

    # check
    assert playerInstance.getInventory() == inventory


def test_set_movement_speed(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setMovementSpeed(10)

    # check
    assert playerInstance.movementSpeed == 10


def test_set_gather_speed(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setGatherSpeed(10)

    # check
    assert playerInstance.gatherSpeed == 10


def test_set_place_speed(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setPlaceSpeed(10)

    # check
    assert playerInstance.placeSpeed == 10


def test_set_crouching(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setCrouching(True)

    # check
    assert playerInstance.crouching == True


def test_is_moving(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setDirection(0)

    # check
    assert playerInstance.isMoving() == True


def is_moving_false(resolve):
    # prepare
    playerInstance = createPlayerInstance(resolve)

    # call
    playerInstance.setDirection(-1)

    # check
    assert playerInstance.isMoving() == False
