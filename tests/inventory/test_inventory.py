from src.entity.grass import Grass
from src.inventory import inventory


def createInventory():
    return inventory.Inventory()


def createGrassEntity():
    return Grass()


def test_initialization():
    inventoryInstance = createInventory()
    assert inventoryInstance.getNumInventorySlots() == 25
    assert inventoryInstance.getNumFreeInventorySlots() == 25
    assert inventoryInstance.getNumTakenInventorySlots() == 0


def test_placeIntoFirstAvailableInventorySlot():
    inventoryInstance = createInventory()
    item = createGrassEntity()
    inventoryInstance.placeIntoFirstAvailableInventorySlot(item)
    assert inventoryInstance.getNumFreeInventorySlots() == 24
    assert inventoryInstance.getNumTakenInventorySlots() == 1
    assert inventoryInstance.getNumItems() == 1
    assert inventoryInstance.getInventorySlots()[0].getContents() == [item]


def test_removeByItem():
    inventoryInstance = createInventory()
    item = createGrassEntity()
    inventoryInstance.placeIntoFirstAvailableInventorySlot(item)
    inventoryInstance.removeByItem(item)
    assert inventoryInstance.getNumFreeInventorySlots() == 25
    assert inventoryInstance.getNumTakenInventorySlots() == 0
    assert inventoryInstance.getNumItems() == 0
    assert inventoryInstance.getInventorySlots()[0].getContents() == []


def test_clear():
    inventoryInstance = createInventory()
    item = createGrassEntity()
    inventoryInstance.placeIntoFirstAvailableInventorySlot(item)
    inventoryInstance.clear()
    assert inventoryInstance.getNumFreeInventorySlots() == 25
    assert inventoryInstance.getNumTakenInventorySlots() == 0
    assert inventoryInstance.getNumItems() == 0
    assert inventoryInstance.getInventorySlots()[0].getContents() == []


def test_getNumFreeInventorySlots():
    inventoryInstance = createInventory()
    for i in range(5 * 20):
        item = createGrassEntity()
        inventoryInstance.placeIntoFirstAvailableInventorySlot(item)
    assert inventoryInstance.getNumFreeInventorySlots() == 20
    assert inventoryInstance.getNumTakenInventorySlots() == 5


def test_getNumTakenInventorySlots():
    inventoryInstance = createInventory()
    for i in range(5 * 20):
        item = createGrassEntity()
        inventoryInstance.placeIntoFirstAvailableInventorySlot(item)
    assert inventoryInstance.getNumTakenInventorySlots() == 5
    assert inventoryInstance.getNumFreeInventorySlots() == 20


def test_getNumItems():
    inventoryInstance = createInventory()
    for i in range(5):
        item = createGrassEntity()
        inventoryInstance.placeIntoFirstAvailableInventorySlot(item)
    assert inventoryInstance.getNumItems() == 5


def test_getNumItemsByType():
    inventoryInstance = createInventory()
    for i in range(5):
        item = createGrassEntity()
        inventoryInstance.placeIntoFirstAvailableInventorySlot(item)
    assert inventoryInstance.getNumItemsByType(Grass) == 5


def test_getSelectedInventorySlotIndex():
    inventoryInstance = createInventory()
    assert inventoryInstance.getSelectedInventorySlotIndex() == 0


def test_setSelectedInventorySlotIndex():
    inventoryInstance = createInventory()
    inventoryInstance.setSelectedInventorySlotIndex(5)
    assert inventoryInstance.getSelectedInventorySlotIndex() == 5


def test_getSelectedInventorySlot():
    inventoryInstance = createInventory()
    assert (
        inventoryInstance.getSelectedInventorySlot()
        == inventoryInstance.getInventorySlots()[0]
    )


def removeSelectedItem():
    inventoryInstance = createInventory()
    item = createGrassEntity()
    inventoryInstance.placeIntoFirstAvailableInventorySlot(item)
    inventoryInstance.removeSelectedItem()
    assert inventoryInstance.getNumFreeInventorySlots() == 25
    assert inventoryInstance.getNumTakenInventorySlots() == 0
    assert inventoryInstance.getNumItems() == 0
    assert inventoryInstance.getInventorySlots()[0].getContents() == []


def test_getFirstTenInventorySlots():
    inventoryInstance = createInventory()
    assert (
        inventoryInstance.getFirstTenInventorySlots()
        == inventoryInstance.getInventorySlots()[:10]
    )


def test_mergeIntoSlot_full_merge():
    inventoryInstance = createInventory()
    sourceSlot = inventoryInstance.getInventorySlots()[0]
    destSlot = inventoryInstance.getInventorySlots()[1]
    for i in range(5):
        sourceSlot.add(createGrassEntity())
    for i in range(10):
        destSlot.add(createGrassEntity())
    inventoryInstance.mergeIntoSlot(sourceSlot, destSlot)
    assert sourceSlot.getNumItems() == 0
    assert destSlot.getNumItems() == 15


def test_mergeIntoSlot_dest_full():
    inventoryInstance = createInventory()
    sourceSlot = inventoryInstance.getInventorySlots()[0]
    destSlot = inventoryInstance.getInventorySlots()[1]
    for i in range(5):
        sourceSlot.add(createGrassEntity())
    for i in range(20):
        destSlot.add(createGrassEntity())
    inventoryInstance.mergeIntoSlot(sourceSlot, destSlot)
    assert sourceSlot.getNumItems() == 5
    assert destSlot.getNumItems() == 20


def test_mergeIntoSlot_partial_merge():
    inventoryInstance = createInventory()
    sourceSlot = inventoryInstance.getInventorySlots()[0]
    destSlot = inventoryInstance.getInventorySlots()[1]
    for i in range(10):
        sourceSlot.add(createGrassEntity())
    for i in range(15):
        destSlot.add(createGrassEntity())
    inventoryInstance.mergeIntoSlot(sourceSlot, destSlot)
    assert destSlot.getNumItems() == 20
    assert sourceSlot.getNumItems() == 5


def test_mergeIntoSlot_different_types_no_merge():
    from src.entity.apple import Apple

    inventoryInstance = createInventory()
    sourceSlot = inventoryInstance.getInventorySlots()[0]
    destSlot = inventoryInstance.getInventorySlots()[1]
    for i in range(5):
        sourceSlot.add(createGrassEntity())
    for i in range(5):
        destSlot.add(Apple())
    inventoryInstance.mergeIntoSlot(sourceSlot, destSlot)
    assert sourceSlot.getNumItems() == 5
    assert destSlot.getNumItems() == 5


def test_placeIntoFirstAvailableNonHotbarSlot_empty_inventory():
    inventoryInstance = createInventory()
    item = createGrassEntity()
    result = inventoryInstance.placeIntoFirstAvailableNonHotbarSlot(item)
    assert result is True
    # should be placed in slot 10 (first non-hotbar slot)
    assert inventoryInstance.getInventorySlots()[10].getNumItems() == 1
    # first 10 slots should be empty
    for i in range(10):
        assert inventoryInstance.getInventorySlots()[i].isEmpty()


def test_placeIntoFirstAvailableNonHotbarSlot_stacks_with_matching():
    inventoryInstance = createInventory()
    slot10 = inventoryInstance.getInventorySlots()[10]
    slot10.add(createGrassEntity())
    item = createGrassEntity()
    result = inventoryInstance.placeIntoFirstAvailableNonHotbarSlot(item)
    assert result is True
    assert slot10.getNumItems() == 2


def test_placeIntoFirstAvailableNonHotbarSlot_non_hotbar_full():
    inventoryInstance = createInventory()
    # fill all non-hotbar slots (slots 10-24)
    for i in range(10, 25):
        for j in range(20):
            inventoryInstance.getInventorySlots()[i].add(createGrassEntity())
    item = createGrassEntity()
    result = inventoryInstance.placeIntoFirstAvailableNonHotbarSlot(item)
    assert result is False
