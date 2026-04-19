from unittest.mock import MagicMock
from src.config import config
from src.inventory import inventoryJsonReaderWriter


def createInventoryJsonReaderWriterInstance():
    config.pygame.display = MagicMock()
    configInstance = config.Config()
    return inventoryJsonReaderWriter.InventoryJsonReaderWriter(configInstance)


def test_initialization():
    inventoryJsonReaderWriterInstance = createInventoryJsonReaderWriterInstance()
    assert inventoryJsonReaderWriterInstance != None


def test_loadInventory():
    inventoryJsonReaderWriterInstance = createInventoryJsonReaderWriterInstance()
    inventoryInstance = inventoryJsonReaderWriterInstance.loadInventory(
        "tests/inventory/inventory.json"
    )
    assert inventoryInstance != None
    assert inventoryInstance.getNumInventorySlots() == 25
    assert inventoryInstance.getNumFreeInventorySlots() == 25
    assert inventoryInstance.getNumTakenInventorySlots() == 0


def test_saveInventory():
    inventoryJsonReaderWriterInstance = createInventoryJsonReaderWriterInstance()
    inventoryInstance = inventoryJsonReaderWriterInstance.loadInventory(
        "tests/inventory/inventory.json"
    )
    inventoryJsonReaderWriterInstance.saveInventory(
        inventoryInstance, "tests/inventory/inventory2.json"
    )
    inventoryInstance2 = inventoryJsonReaderWriterInstance.loadInventory(
        "tests/inventory/inventory2.json"
    )
    assert inventoryInstance2 != None
    assert inventoryInstance2.getNumInventorySlots() == 25
    assert inventoryInstance2.getNumFreeInventorySlots() == 25
    assert inventoryInstance2.getNumTakenInventorySlots() == 0
