package com.preponderous.roam.model;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Represents a single room in the game world.
 * Each room contains a grid of tiles and entities.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Room {
    private final int roomX;
    private final int roomY;
    private final int width;
    private final int height;
    private final Tile[][] tiles;
    private final Map<String, Entity> entities;

    public Room(int roomX, int roomY, int width, int height) {
        this.roomX = roomX;
        this.roomY = roomY;
        this.width = width;
        this.height = height;
        this.tiles = new Tile[height][width];
        this.entities = new ConcurrentHashMap<>();
        
        // Initialize all tiles
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                tiles[y][x] = new Tile(x, y, Biome.GRASSLAND);
            }
        }
    }

    public int getRoomX() {
        return roomX;
    }

    public int getRoomY() {
        return roomY;
    }

    public int getWidth() {
        return width;
    }

    public int getHeight() {
        return height;
    }

    public Tile[][] getTiles() {
        return tiles;
    }

    public Tile getTile(int x, int y) {
        if (x < 0 || x >= width || y < 0 || y >= height) {
            return null;
        }
        return tiles[y][x];
    }

    public void setTile(int x, int y, Tile tile) {
        if (x >= 0 && x < width && y >= 0 && y < height) {
            tiles[y][x] = tile;
        }
    }

    public Map<String, Entity> getEntities() {
        return entities;
    }

    public List<Entity> getEntitiesList() {
        return new ArrayList<>(entities.values());
    }

    public void addEntity(Entity entity) {
        entities.put(entity.getId(), entity);
        // Set the entity's location to this room
        entity.setLocationId(getRoomKey());
    }

    public void removeEntity(String entityId) {
        entities.remove(entityId);
    }

    public Entity getEntity(String entityId) {
        return entities.get(entityId);
    }

    private String getRoomKey() {
        return roomX + "," + roomY;
    }
}
