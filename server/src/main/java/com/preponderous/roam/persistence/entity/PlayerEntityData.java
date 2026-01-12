package com.preponderous.roam.persistence.entity;

import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

/**
 * JPA entity representing a player's state.
 * 
 * @author Daniel McCoy Stephenson
 */
@Entity
@Table(name = "players")
public class PlayerEntityData {
    
    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;
    
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private GameSessionEntity session;
    
    @Column(name = "name", nullable = false, length = 100)
    private String name;
    
    @Column(name = "image_path", nullable = false, length = 255)
    private String imagePath;
    
    @Column(name = "energy", nullable = false)
    private double energy;
    
    @Column(name = "target_energy", nullable = false)
    private double targetEnergy;
    
    @Column(name = "tick_created", nullable = false)
    private long tickCreated;
    
    @Column(name = "direction", nullable = false)
    private int direction;
    
    @Column(name = "last_direction", nullable = false)
    private int lastDirection;
    
    @Column(name = "gathering", nullable = false)
    private boolean gathering;
    
    @Column(name = "is_placing", nullable = false)
    private boolean placing;
    
    @Column(name = "crouching", nullable = false)
    private boolean crouching;
    
    @Column(name = "tick_last_moved", nullable = false)
    private long tickLastMoved;
    
    @Column(name = "tick_last_gathered", nullable = false)
    private long tickLastGathered;
    
    @Column(name = "tick_last_placed", nullable = false)
    private long tickLastPlaced;
    
    @Column(name = "movement_speed", nullable = false)
    private int movementSpeed;
    
    @Column(name = "gather_speed", nullable = false)
    private int gatherSpeed;
    
    @Column(name = "place_speed", nullable = false)
    private int placeSpeed;
    
    @Column(name = "room_x", nullable = false)
    private int roomX;
    
    @Column(name = "room_y", nullable = false)
    private int roomY;
    
    @Column(name = "tile_x", nullable = false)
    private int tileX;
    
    @Column(name = "tile_y", nullable = false)
    private int tileY;
    
    @Column(name = "selected_inventory_slot_index", nullable = false)
    private int selectedInventorySlotIndex;
    
    @OneToMany(mappedBy = "player", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @OrderBy("slotIndex ASC")
    private List<InventorySlotEntity> inventorySlots = new ArrayList<>();
    
    public PlayerEntityData() {
    }
    
    // Getters and Setters
    
    public String getId() {
        return id;
    }
    
    public void setId(String id) {
        this.id = id;
    }
    
    public GameSessionEntity getSession() {
        return session;
    }
    
    public void setSession(GameSessionEntity session) {
        this.session = session;
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public String getImagePath() {
        return imagePath;
    }
    
    public void setImagePath(String imagePath) {
        this.imagePath = imagePath;
    }
    
    public double getEnergy() {
        return energy;
    }
    
    public void setEnergy(double energy) {
        this.energy = energy;
    }
    
    public double getTargetEnergy() {
        return targetEnergy;
    }
    
    public void setTargetEnergy(double targetEnergy) {
        this.targetEnergy = targetEnergy;
    }
    
    public long getTickCreated() {
        return tickCreated;
    }
    
    public void setTickCreated(long tickCreated) {
        this.tickCreated = tickCreated;
    }
    
    public int getDirection() {
        return direction;
    }
    
    public void setDirection(int direction) {
        this.direction = direction;
    }
    
    public int getLastDirection() {
        return lastDirection;
    }
    
    public void setLastDirection(int lastDirection) {
        this.lastDirection = lastDirection;
    }
    
    public boolean isGathering() {
        return gathering;
    }
    
    public void setGathering(boolean gathering) {
        this.gathering = gathering;
    }
    
    public boolean isPlacing() {
        return placing;
    }
    
    public void setPlacing(boolean placing) {
        this.placing = placing;
    }
    
    public boolean isCrouching() {
        return crouching;
    }
    
    public void setCrouching(boolean crouching) {
        this.crouching = crouching;
    }
    
    public long getTickLastMoved() {
        return tickLastMoved;
    }
    
    public void setTickLastMoved(long tickLastMoved) {
        this.tickLastMoved = tickLastMoved;
    }
    
    public long getTickLastGathered() {
        return tickLastGathered;
    }
    
    public void setTickLastGathered(long tickLastGathered) {
        this.tickLastGathered = tickLastGathered;
    }
    
    public long getTickLastPlaced() {
        return tickLastPlaced;
    }
    
    public void setTickLastPlaced(long tickLastPlaced) {
        this.tickLastPlaced = tickLastPlaced;
    }
    
    public int getMovementSpeed() {
        return movementSpeed;
    }
    
    public void setMovementSpeed(int movementSpeed) {
        this.movementSpeed = movementSpeed;
    }
    
    public int getGatherSpeed() {
        return gatherSpeed;
    }
    
    public void setGatherSpeed(int gatherSpeed) {
        this.gatherSpeed = gatherSpeed;
    }
    
    public int getPlaceSpeed() {
        return placeSpeed;
    }
    
    public void setPlaceSpeed(int placeSpeed) {
        this.placeSpeed = placeSpeed;
    }
    
    public int getRoomX() {
        return roomX;
    }
    
    public void setRoomX(int roomX) {
        this.roomX = roomX;
    }
    
    public int getRoomY() {
        return roomY;
    }
    
    public void setRoomY(int roomY) {
        this.roomY = roomY;
    }
    
    public int getTileX() {
        return tileX;
    }
    
    public void setTileX(int tileX) {
        this.tileX = tileX;
    }
    
    public int getTileY() {
        return tileY;
    }
    
    public void setTileY(int tileY) {
        this.tileY = tileY;
    }
    
    public int getSelectedInventorySlotIndex() {
        return selectedInventorySlotIndex;
    }
    
    public void setSelectedInventorySlotIndex(int selectedInventorySlotIndex) {
        this.selectedInventorySlotIndex = selectedInventorySlotIndex;
    }
    
    /**
     * Returns the inventory slots. Note: This list is managed by JPA/Hibernate.
     * Direct modifications are tracked for persistence.
     */
    public List<InventorySlotEntity> getInventorySlots() {
        return inventorySlots;
    }
    
    public void setInventorySlots(List<InventorySlotEntity> inventorySlots) {
        this.inventorySlots = inventorySlots;
    }
    
    public void addInventorySlot(InventorySlotEntity slot) {
        inventorySlots.add(slot);
        slot.setPlayer(this);
    }
    
    public void removeInventorySlot(InventorySlotEntity slot) {
        inventorySlots.remove(slot);
        slot.setPlayer(null);
    }
}
