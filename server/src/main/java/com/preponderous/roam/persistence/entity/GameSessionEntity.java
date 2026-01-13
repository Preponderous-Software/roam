package com.preponderous.roam.persistence.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * JPA entity representing a game session.
 * Stores the complete state of a game including player, world, and all related data.
 * 
 * @author Daniel McCoy Stephenson
 */
@Entity
@Table(name = "game_sessions")
public class GameSessionEntity {
    
    @Id
    @Column(name = "session_id", length = 36, nullable = false)
    private String sessionId;
    
    @Column(name = "user_id", length = 50, nullable = false)
    private String userId;  // Username of the session owner
    
    @Column(name = "current_tick", nullable = false)
    private long currentTick;
    
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;
    
    @Column(name = "world_seed", nullable = false)
    private long worldSeed;
    
    @Column(name = "world_room_width", nullable = false)
    private int worldRoomWidth;
    
    @Column(name = "world_room_height", nullable = false)
    private int worldRoomHeight;
    
    @Column(name = "world_resource_density", nullable = false)
    private double worldResourceDensity;
    
    @Column(name = "world_hazard_density", nullable = false)
    private double worldHazardDensity;
    
    @OneToOne(mappedBy = "session", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private PlayerEntityData player;
    
    @OneToMany(mappedBy = "session", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<RoomEntity> rooms = new ArrayList<>();
    
    public GameSessionEntity() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }
    
    public GameSessionEntity(String sessionId, String userId, long currentTick, long worldSeed, 
                           int worldRoomWidth, int worldRoomHeight, 
                           double worldResourceDensity, double worldHazardDensity) {
        this();
        this.sessionId = sessionId;
        this.userId = userId;
        this.currentTick = currentTick;
        this.worldSeed = worldSeed;
        this.worldRoomWidth = worldRoomWidth;
        this.worldRoomHeight = worldRoomHeight;
        this.worldResourceDensity = worldResourceDensity;
        this.worldHazardDensity = worldHazardDensity;
    }
    
    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
    
    // Getters and Setters
    
    public String getSessionId() {
        return sessionId;
    }
    
    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }
    
    public String getUserId() {
        return userId;
    }
    
    public void setUserId(String userId) {
        this.userId = userId;
    }
    
    public long getCurrentTick() {
        return currentTick;
    }
    
    public void setCurrentTick(long currentTick) {
        this.currentTick = currentTick;
    }
    
    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
    
    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
    
    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
    
    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
    
    public long getWorldSeed() {
        return worldSeed;
    }
    
    public void setWorldSeed(long worldSeed) {
        this.worldSeed = worldSeed;
    }
    
    public int getWorldRoomWidth() {
        return worldRoomWidth;
    }
    
    public void setWorldRoomWidth(int worldRoomWidth) {
        this.worldRoomWidth = worldRoomWidth;
    }
    
    public int getWorldRoomHeight() {
        return worldRoomHeight;
    }
    
    public void setWorldRoomHeight(int worldRoomHeight) {
        this.worldRoomHeight = worldRoomHeight;
    }
    
    public double getWorldResourceDensity() {
        return worldResourceDensity;
    }
    
    public void setWorldResourceDensity(double worldResourceDensity) {
        this.worldResourceDensity = worldResourceDensity;
    }
    
    public double getWorldHazardDensity() {
        return worldHazardDensity;
    }
    
    public void setWorldHazardDensity(double worldHazardDensity) {
        this.worldHazardDensity = worldHazardDensity;
    }
    
    public PlayerEntityData getPlayer() {
        return player;
    }
    
    public void setPlayer(PlayerEntityData player) {
        this.player = player;
        if (player != null) {
            player.setSession(this);
        }
    }
    
    public List<RoomEntity> getRooms() {
        return rooms;
    }
    
    public void setRooms(List<RoomEntity> rooms) {
        this.rooms = rooms;
    }
    
    public void addRoom(RoomEntity room) {
        rooms.add(room);
        room.setSession(this);
    }
    
    public void removeRoom(RoomEntity room) {
        rooms.remove(room);
        room.setSession(null);
    }
}
