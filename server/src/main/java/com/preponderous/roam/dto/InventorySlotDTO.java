package com.preponderous.roam.dto;

/**
 * DTO for inventory slot information.
 * 
 * @author Daniel McCoy Stephenson
 */
public class InventorySlotDTO {
    private String itemName;
    private int numItems;
    private int maxStackSize;
    private boolean empty;

    public InventorySlotDTO() {
    }

    public String getItemName() {
        return itemName;
    }

    public void setItemName(String itemName) {
        this.itemName = itemName;
    }

    public int getNumItems() {
        return numItems;
    }

    public void setNumItems(int numItems) {
        this.numItems = numItems;
    }

    public int getMaxStackSize() {
        return maxStackSize;
    }

    public void setMaxStackSize(int maxStackSize) {
        this.maxStackSize = maxStackSize;
    }

    public boolean isEmpty() {
        return empty;
    }

    public void setEmpty(boolean empty) {
        this.empty = empty;
    }
}
