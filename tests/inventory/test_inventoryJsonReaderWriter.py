import jsonschema
import pytest

from entity.living.livingEntityRegistry import LIVING_ENTITY_TYPES
from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter


def _raiseValidationError(*args, **kwargs):
    raise jsonschema.exceptions.ValidationError("forced validation failure")


def _itemsIn(inventory):
    return [
        item
        for slot in inventory.getInventorySlots()
        for item in slot.getContents()
    ]


@pytest.mark.parametrize("creatureName", sorted(LIVING_ENTITY_TYPES))
def test_picked_up_creature_round_trips(
    creatureName, resolve, tmp_path, test_config
):
    # A creature carried in the inventory must survive save/load as the same
    # species with its tick metadata intact.
    test_config.pathToSaveDirectory = str(tmp_path)
    readerWriter = resolve(InventoryJsonReaderWriter)
    inventory = readerWriter.loadInventory("tests/inventory/inventory.json")

    creature = LIVING_ENTITY_TYPES[creatureName](123)
    creature.setTickLastReproduced(456)
    inventory.placeIntoFirstAvailableInventorySlot(creature)

    savePath = str(tmp_path / "creature_inventory.json")
    readerWriter.saveInventory(inventory, savePath)
    restored = readerWriter.loadInventory(savePath)

    items = _itemsIn(restored)
    assert len(items) == 1
    assert type(items[0]).__name__ == creatureName
    assert items[0].getTickCreated() == 123
    assert items[0].getTickLastReproduced() == 456


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
