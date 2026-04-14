from inventory.inventorySlot import InventorySlot


# @author Daniel McCoy Stephenson
class Inventory:
    def __init__(self):
        self.inventorySlots = []
        self.size = 25
        for i in range(self.size):
            self.inventorySlots.append(InventorySlot())
        self.selectedInventorySlotIndex = 0

    def getInventorySlots(self):
        return self.inventorySlots

    def getNumInventorySlots(self):
        return len(self.inventorySlots)

    def placeIntoFirstAvailableInventorySlot(self, item):
        for inventorySlot in self.inventorySlots:
            if inventorySlot.isEmpty():
                # set the item
                inventorySlot.add(item)
                return True
            elif (
                inventorySlot.getContents()[0].getName() == item.getName()
                and inventorySlot.getNumItems() < inventorySlot.getMaxStackSize()
            ):
                # increment the amount
                inventorySlot.add(item)
                return True
        return False

    def removeByItem(self, item):
        for inventorySlot in self.inventorySlots:
            if inventorySlot.isEmpty():
                continue
            if inventorySlot.getContents()[0].getName() == item.getName():
                if inventorySlot.getNumItems() > 1:
                    inventorySlot.remove(item)
                else:
                    inventorySlot.clear()
                return True
        return False

    def clear(self):
        for inventorySlot in self.inventorySlots:
            inventorySlot.clear()

    def getNumFreeInventorySlots(self):
        count = 0
        for inventorySlot in self.inventorySlots:
            if inventorySlot.isEmpty():
                count += 1
        return count

    def getNumTakenInventorySlots(self):
        return self.getNumInventorySlots() - self.getNumFreeInventorySlots()

    def getNumItems(self):
        count = 0
        for inventorySlot in self.inventorySlots:
            if inventorySlot.isEmpty():
                continue
            count += inventorySlot.getNumItems()
        return count

    def getNumItemsByType(self, type):
        count = 0
        for inventorySlot in self.inventorySlots:
            if inventorySlot.isEmpty():
                continue
            item = inventorySlot.getContents()[0]
            if isinstance(item, type):
                count += inventorySlot.getNumItems()
        return count

    def getSelectedInventorySlotIndex(self):
        return self.selectedInventorySlotIndex

    def setSelectedInventorySlotIndex(self, index):
        self.selectedInventorySlotIndex = index

    def getItemByIndex(self, index):
        return self.inventorySlots[index].getItem()

    def getSelectedInventorySlot(self):
        return self.inventorySlots[self.selectedInventorySlotIndex]

    def removeSelectedItem(self):
        return self.inventorySlots[self.selectedInventorySlotIndex].pop()

    def mergeIntoSlot(self, sourceSlot, destSlot):
        if sourceSlot.isEmpty() or destSlot.isEmpty():
            return
        sourceName = sourceSlot.getContents()[0].getName()
        destName = destSlot.getContents()[0].getName()
        if sourceName != destName:
            return
        maxStack = destSlot.getMaxStackSize()
        available = maxStack - destSlot.getNumItems()
        toTransfer = min(available, sourceSlot.getNumItems())
        for _ in range(toTransfer):
            destSlot.add(sourceSlot.pop())

    def getFirstTenInventorySlots(self):
        if len(self.inventorySlots) > 10:
            return self.inventorySlots[:10]
        else:
            return self.inventorySlots
