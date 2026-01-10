package com.preponderous.roam.dto;

import java.util.List;

/**
 * DTO for inventory information.
 * 
 * @author Daniel McCoy Stephenson
 */
public class InventoryDTO {
    private List<InventorySlotDTO> slots;
    private int selectedSlotIndex;
    private int numFreeSlots;
    private int numTakenSlots;
    private int numItems;

    public InventoryDTO() {
    }

    public List<InventorySlotDTO> getSlots() {
        return slots;
    }

    public void setSlots(List<InventorySlotDTO> slots) {
        this.slots = slots;
    }

    public int getSelectedSlotIndex() {
        return selectedSlotIndex;
    }

    public void setSelectedSlotIndex(int selectedSlotIndex) {
        this.selectedSlotIndex = selectedSlotIndex;
    }

    public int getNumFreeSlots() {
        return numFreeSlots;
    }

    public void setNumFreeSlots(int numFreeSlots) {
        this.numFreeSlots = numFreeSlots;
    }

    public int getNumTakenSlots() {
        return numTakenSlots;
    }

    public void setNumTakenSlots(int numTakenSlots) {
        this.numTakenSlots = numTakenSlots;
    }

    public int getNumItems() {
        return numItems;
    }

    public void setNumItems(int numItems) {
        this.numItems = numItems;
    }
}
