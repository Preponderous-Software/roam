package com.preponderous.roam.persistence.entity;

import jakarta.persistence.*;

/**
 * JPA entity representing a tile in a room.
 * 
 * @author Daniel McCoy Stephenson
 */
@Entity
@Table(name = "tiles", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"room_id", "tile_x", "tile_y"})
})
public class TileEntity {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "room_id", nullable = false)
    private RoomEntity room;
    
    @Column(name = "tile_x", nullable = false)
    private int tileX;
    
    @Column(name = "tile_y", nullable = false)
    private int tileY;
    
    @Column(name = "biome", nullable = false, length = 50)
    private String biome;
    
    @Column(name = "resource_type", length = 100)
    private String resourceType;
    
    @Column(name = "resource_amount", nullable = false)
    private int resourceAmount;
    
    @Column(name = "has_hazard", nullable = false)
    private boolean hasHazard;
    
    @Column(name = "hazard_type", length = 100)
    private String hazardType;
    
    public TileEntity() {
        this.resourceAmount = 0;
        this.hasHazard = false;
    }
    
    public TileEntity(int tileX, int tileY, String biome) {
        this();
        this.tileX = tileX;
        this.tileY = tileY;
        this.biome = biome;
    }
    
    // Getters and Setters
    
    public Long getId() {
        return id;
    }
    
    public void setId(Long id) {
        this.id = id;
    }
    
    public RoomEntity getRoom() {
        return room;
    }
    
    public void setRoom(RoomEntity room) {
        this.room = room;
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
    
    public String getBiome() {
        return biome;
    }
    
    public void setBiome(String biome) {
        this.biome = biome;
    }
    
    public String getResourceType() {
        return resourceType;
    }
    
    public void setResourceType(String resourceType) {
        this.resourceType = resourceType;
    }
    
    public int getResourceAmount() {
        return resourceAmount;
    }
    
    public void setResourceAmount(int resourceAmount) {
        this.resourceAmount = resourceAmount;
    }
    
    public boolean isHasHazard() {
        return hasHazard;
    }
    
    public void setHasHazard(boolean hasHazard) {
        this.hasHazard = hasHazard;
    }
    
    public String getHazardType() {
        return hazardType;
    }
    
    public void setHazardType(String hazardType) {
        this.hazardType = hazardType;
    }
}
