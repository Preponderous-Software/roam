import jsonschema

from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter


def _raiseValidationError(*args, **kwargs):
    raise jsonschema.exceptions.ValidationError("forced validation failure")


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


def test_saveInventory_aborts_and_preserves_existing_file_on_validation_error(
    resolve, tmp_path, test_config, monkeypatch
):
    test_config.pathToSaveDirectory = str(tmp_path)
    writer = resolve(InventoryJsonReaderWriter)
    inventory = writer.loadInventory("tests/inventory/inventory.json")
    savePath = tmp_path / "inventory2.json"

    # Seed a distinct existing "good" save so an overwrite would be detectable
    sentinel = "EXISTING_GOOD_SAVE"
    savePath.write_text(sentinel)

    # A validation failure must NOT clobber the existing good file
    monkeypatch.setattr(jsonschema, "validate", _raiseValidationError)
    result = writer.saveInventory(inventory, str(savePath))

    assert result is False
    assert savePath.read_text() == sentinel


def test_saveInventory_does_not_create_file_on_validation_error(
    resolve, tmp_path, test_config, monkeypatch
):
    test_config.pathToSaveDirectory = str(tmp_path)
    writer = resolve(InventoryJsonReaderWriter)
    inventory = writer.loadInventory("tests/inventory/inventory.json")
    savePath = tmp_path / "new_inventory.json"

    monkeypatch.setattr(jsonschema, "validate", _raiseValidationError)
    result = writer.saveInventory(inventory, str(savePath))

    assert result is False
    assert not savePath.exists()


def test_saveInventory_returns_true_on_success(resolve, tmp_path, test_config):
    test_config.pathToSaveDirectory = str(tmp_path)
    writer = resolve(InventoryJsonReaderWriter)
    inventory = writer.loadInventory("tests/inventory/inventory.json")
    savePath = tmp_path / "inventory2.json"

    assert writer.saveInventory(inventory, str(savePath)) is True
