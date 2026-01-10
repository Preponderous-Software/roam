package com.preponderous.roam.model;

/**
 * Represents a single slot in an inventory.
 * 
 * @author Daniel McCoy Stephenson
 */
public class InventorySlot {
    private String itemName;
    private int numItems;
    private final int maxStackSize;

    public InventorySlot() {
        this.itemName = null;
        this.numItems = 0;
        this.maxStackSize = 64;
    }

    public boolean isEmpty() {
        return itemName == null || numItems == 0;
    }

    public String getItemName() {
        return itemName;
    }

    public int getNumItems() {
        return numItems;
    }

    public int getMaxStackSize() {
        return maxStackSize;
    }

    public void add(String itemName) {
        if (this.itemName == null) {
            this.itemName = itemName;
            this.numItems = 1;
        } else if (this.itemName.equals(itemName) && numItems < maxStackSize) {
            this.numItems++;
        }
    }

    public void remove() {
        if (numItems > 0) {
            numItems--;
            if (numItems == 0) {
                itemName = null;
            }
        }
    }

    public String pop() {
        if (isEmpty()) {
            return null;
        }
        String item = itemName;
        remove();
        return item;
    }

    public void clear() {
        this.itemName = null;
        this.numItems = 0;
    }
}
