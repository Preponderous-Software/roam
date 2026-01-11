package com.preponderous.roam.persistence.entity;

import jakarta.persistence.*;

/**
 * JPA entity representing a game entity (tree, rock, animal, etc.).
 * 
 * @author Daniel McCoy Stephenson
 */
@Entity
@Table(name = "game_entities")
public class GameEntityData {
    
    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "room_id", nullable = false)
    private RoomEntity room;
    
    @Column(name = "entity_type", nullable = false, length = 100)
    private String entityType;
    
    @Column(name = "name", nullable = false, length = 100)
    private String name;
    
    @Column(name = "image_path", nullable = false, length = 255)
    private String imagePath;
    
    @Column(name = "location_id", length = 100)
    private String locationId;
    
    @Column(name = "solid", nullable = false)
    private boolean solid;
    
    @Column(name = "energy")
    private Double energy;
    
    @Column(name = "target_energy")
    private Double targetEnergy;
    
    @Column(name = "tick_created")
    private Long tickCreated;
    
    @Column(name = "tick_last_reproduced")
    private Long tickLastReproduced;
    
    public GameEntityData() {
    }
    
    public GameEntityData(String id, String entityType, String name, String imagePath) {
        this.id = id;
        this.entityType = entityType;
        this.name = name;
        this.imagePath = imagePath;
        this.solid = false;
    }
    
    // Getters and Setters
    
    public String getId() {
        return id;
    }
    
    public void setId(String id) {
        this.id = id;
    }
    
    public RoomEntity getRoom() {
        return room;
    }
    
    public void setRoom(RoomEntity room) {
        this.room = room;
    }
    
    public String getEntityType() {
        return entityType;
    }
    
    public void setEntityType(String entityType) {
        this.entityType = entityType;
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
    
    public String getLocationId() {
        return locationId;
    }
    
    public void setLocationId(String locationId) {
        this.locationId = locationId;
    }
    
    public boolean isSolid() {
        return solid;
    }
    
    public void setSolid(boolean solid) {
        this.solid = solid;
    }
    
    public Double getEnergy() {
        return energy;
    }
    
    public void setEnergy(Double energy) {
        this.energy = energy;
    }
    
    public Double getTargetEnergy() {
        return targetEnergy;
    }
    
    public void setTargetEnergy(Double targetEnergy) {
        this.targetEnergy = targetEnergy;
    }
    
    public Long getTickCreated() {
        return tickCreated;
    }
    
    public void setTickCreated(Long tickCreated) {
        this.tickCreated = tickCreated;
    }
    
    public Long getTickLastReproduced() {
        return tickLastReproduced;
    }
    
    public void setTickLastReproduced(Long tickLastReproduced) {
        this.tickLastReproduced = tickLastReproduced;
    }
}
