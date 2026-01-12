package com.preponderous.roam.persistence.entity;

import jakarta.persistence.*;

/**
 * JPA entity representing an inventory slot.
 * 
 * @author Daniel McCoy Stephenson
 */
@Entity
@Table(name = "inventory_slots")
public class InventorySlotEntity {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "player_id", nullable = false)
    private PlayerEntityData player;
    
    @Column(name = "slot_index", nullable = false)
    private int slotIndex;
    
    @Column(name = "item_name", length = 100)
    private String itemName;
    
    @Column(name = "num_items", nullable = false)
    private int numItems;
    
    @Column(name = "max_stack_size", nullable = false)
    private int maxStackSize;
    
    public InventorySlotEntity() {
        this.numItems = 0;
        this.maxStackSize = 64;
    }
    
    // Getters and Setters
    
    public Long getId() {
        return id;
    }
    
    public void setId(Long id) {
        this.id = id;
    }
    
    public PlayerEntityData getPlayer() {
        return player;
    }
    
    public void setPlayer(PlayerEntityData player) {
        this.player = player;
    }
    
    public int getSlotIndex() {
        return slotIndex;
    }
    
    public void setSlotIndex(int slotIndex) {
        this.slotIndex = slotIndex;
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
}
