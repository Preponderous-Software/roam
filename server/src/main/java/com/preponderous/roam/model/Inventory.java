package com.preponderous.roam.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Represents a player's inventory.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Inventory {
    public static final int DEFAULT_INVENTORY_SIZE = 25;
    
    private final List<InventorySlot> inventorySlots;
    private final int size;
    private int selectedInventorySlotIndex;

    public Inventory() {
        this(DEFAULT_INVENTORY_SIZE);
    }
    
    public Inventory(int size) {
        this.size = size;
        this.inventorySlots = new ArrayList<>();
        for (int i = 0; i < size; i++) {
            inventorySlots.add(new InventorySlot());
        }
        this.selectedInventorySlotIndex = 0;
    }

    public List<InventorySlot> getInventorySlots() {
        return Collections.unmodifiableList(inventorySlots);
    }

    public int getNumInventorySlots() {
        return inventorySlots.size();
    }

    public boolean placeIntoFirstAvailableInventorySlot(String itemName) {
        for (InventorySlot inventorySlot : inventorySlots) {
            if (inventorySlot.isEmpty()) {
                inventorySlot.add(itemName);
                return true;
            } else if (inventorySlot.getItemName().equals(itemName) 
                    && inventorySlot.getNumItems() < inventorySlot.getMaxStackSize()) {
                inventorySlot.add(itemName);
                return true;
            }
        }
        return false;
    }

    public boolean removeByItemName(String itemName) {
        for (InventorySlot inventorySlot : inventorySlots) {
            if (inventorySlot.isEmpty()) {
                continue;
            }
            if (inventorySlot.getItemName().equals(itemName)) {
                if (inventorySlot.getNumItems() > 1) {
                    inventorySlot.remove();
                } else {
                    inventorySlot.clear();
                }
                return true;
            }
        }
        return false;
    }

    public void clear() {
        for (InventorySlot inventorySlot : inventorySlots) {
            inventorySlot.clear();
        }
    }

    public int getNumFreeInventorySlots() {
        int count = 0;
        for (InventorySlot inventorySlot : inventorySlots) {
            if (inventorySlot.isEmpty()) {
                count++;
            }
        }
        return count;
    }

    public int getNumTakenInventorySlots() {
        return getNumInventorySlots() - getNumFreeInventorySlots();
    }

    public int getNumItems() {
        int count = 0;
        for (InventorySlot inventorySlot : inventorySlots) {
            if (!inventorySlot.isEmpty()) {
                count += inventorySlot.getNumItems();
            }
        }
        return count;
    }

    public int getSelectedInventorySlotIndex() {
        return selectedInventorySlotIndex;
    }

    public void setSelectedInventorySlotIndex(int index) {
        if (index < 0 || index >= inventorySlots.size()) {
            throw new IndexOutOfBoundsException("Selected inventory slot index out of bounds: " + index);
        }
        this.selectedInventorySlotIndex = index;
    }

    public InventorySlot getSelectedInventorySlot() {
        return inventorySlots.get(selectedInventorySlotIndex);
    }

    public String removeSelectedItem() {
        return inventorySlots.get(selectedInventorySlotIndex).pop();
    }

    public List<InventorySlot> getFirstTenInventorySlots() {
        if (inventorySlots.size() > 10) {
            return inventorySlots.subList(0, 10);
        } else {
            return inventorySlots;
        }
    }
    
    /**
     * Place an item into a specific inventory slot. Used for loading saved inventories.
     * @param slotIndex The slot index to place the item in
     * @param itemName The name of the item
     * @return true if the item was successfully placed, false otherwise
     */
    public boolean placeIntoSlot(int slotIndex, String itemName) {
        if (slotIndex < 0 || slotIndex >= inventorySlots.size()) {
            return false;
        }
        
        InventorySlot slot = inventorySlots.get(slotIndex);
        if (slot.isEmpty()) {
            slot.add(itemName);
            return true;
        } else if (slot.getItemName().equals(itemName) 
                && slot.getNumItems() < slot.getMaxStackSize()) {
            slot.add(itemName);
            return true;
        }
        
        return false;
    }
    
    /**
     * Swap two inventory slots.
     * @param fromSlot The index of the first slot
     * @param toSlot The index of the second slot
     * @throws IndexOutOfBoundsException if either slot index is out of bounds
     */
    public void swapSlots(int fromSlot, int toSlot) {
        if (fromSlot < 0 || fromSlot >= inventorySlots.size()) {
            throw new IndexOutOfBoundsException("fromSlot index out of bounds: " + fromSlot);
        }
        if (toSlot < 0 || toSlot >= inventorySlots.size()) {
            throw new IndexOutOfBoundsException("toSlot index out of bounds: " + toSlot);
        }
        
        // Early return if swapping slot with itself
        if (fromSlot == toSlot) {
            return;
        }
        
        // Swap the slots
        InventorySlot temp = inventorySlots.get(fromSlot);
        inventorySlots.set(fromSlot, inventorySlots.get(toSlot));
        inventorySlots.set(toSlot, temp);
    }
}
