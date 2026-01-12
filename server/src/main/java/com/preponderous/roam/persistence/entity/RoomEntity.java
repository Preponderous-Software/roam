package com.preponderous.roam.persistence.entity;

import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

/**
 * JPA entity representing a room in the game world.
 * 
 * @author Daniel McCoy Stephenson
 */
@Entity
@Table(name = "rooms", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"session_id", "room_x", "room_y"})
})
public class RoomEntity {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    private GameSessionEntity session;
    
    @Column(name = "room_x", nullable = false)
    private int roomX;
    
    @Column(name = "room_y", nullable = false)
    private int roomY;
    
    @Column(name = "width", nullable = false)
    private int width;
    
    @Column(name = "height", nullable = false)
    private int height;
    
    @OneToMany(mappedBy = "room", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<TileEntity> tiles = new ArrayList<>();
    
    @OneToMany(mappedBy = "room", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<GameEntityData> entities = new ArrayList<>();
    
    public RoomEntity() {
    }
    
    public RoomEntity(int roomX, int roomY, int width, int height) {
        this.roomX = roomX;
        this.roomY = roomY;
        this.width = width;
        this.height = height;
    }
    
    // Getters and Setters
    
    public Long getId() {
        return id;
    }
    
    public void setId(Long id) {
        this.id = id;
    }
    
    public GameSessionEntity getSession() {
        return session;
    }
    
    public void setSession(GameSessionEntity session) {
        this.session = session;
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
    
    public int getWidth() {
        return width;
    }
    
    public void setWidth(int width) {
        this.width = width;
    }
    
    public int getHeight() {
        return height;
    }
    
    public void setHeight(int height) {
        this.height = height;
    }
    
    /**
     * Returns the tiles in this room. Note: This list is managed by JPA/Hibernate.
     * Direct modifications are tracked for persistence.
     */
    public List<TileEntity> getTiles() {
        return tiles;
    }
    
    public void setTiles(List<TileEntity> tiles) {
        this.tiles = tiles;
    }
    
    public void addTile(TileEntity tile) {
        tiles.add(tile);
        tile.setRoom(this);
    }
    
    public void removeTile(TileEntity tile) {
        tiles.remove(tile);
        tile.setRoom(null);
    }
    
    /**
     * Returns the entities in this room. Note: This list is managed by JPA/Hibernate.
     * Direct modifications are tracked for persistence.
     */
    public List<GameEntityData> getEntities() {
        return entities;
    }
    
    public void setEntities(List<GameEntityData> entities) {
        this.entities = entities;
    }
    
    public void addEntity(GameEntityData entity) {
        entities.add(entity);
        entity.setRoom(this);
    }
    
    public void removeEntity(GameEntityData entity) {
        entities.remove(entity);
        entity.setRoom(null);
    }
}
