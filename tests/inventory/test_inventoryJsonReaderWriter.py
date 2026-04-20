from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter


def test_initialization(resolve):
    inventoryJsonReaderWriterInstance = resolve(InventoryJsonReaderWriter)
    assert inventoryJsonReaderWriterInstance != None


def test_loadInventory(resolve):
    inventoryJsonReaderWriterInstance = resolve(InventoryJsonReaderWriter)
    inventoryInstance = inventoryJsonReaderWriterInstance.loadInventory(
        "tests/inventory/inventory.json"
    )
    assert inventoryInstance != None
    assert inventoryInstance.getNumInventorySlots() == 25
    assert inventoryInstance.getNumFreeInventorySlots() == 25
    assert inventoryInstance.getNumTakenInventorySlots() == 0


def test_saveInventory(resolve, tmp_path, test_config):
    test_config.pathToSaveDirectory = str(tmp_path)
    inventoryJsonReaderWriterInstance = resolve(InventoryJsonReaderWriter)
    inventoryInstance = inventoryJsonReaderWriterInstance.loadInventory(
        "tests/inventory/inventory.json"
    )
    savePath = str(tmp_path / "inventory2.json")
    inventoryJsonReaderWriterInstance.saveInventory(
        inventoryInstance, savePath
    )
    inventoryInstance2 = inventoryJsonReaderWriterInstance.loadInventory(
        savePath
    )
    assert inventoryInstance2 != None
    assert inventoryInstance2.getNumInventorySlots() == 25
    assert inventoryInstance2.getNumFreeInventorySlots() == 25
    assert inventoryInstance2.getNumTakenInventorySlots() == 0
