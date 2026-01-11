package com.preponderous.roam.model;

/**
 * Represents a single room in the game world.
 * Each room contains a grid of tiles.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Room {
    private final int roomX;
    private final int roomY;
    private final int width;
    private final int height;
    private final Tile[][] tiles;

    public Room(int roomX, int roomY, int width, int height) {
        this.roomX = roomX;
        this.roomY = roomY;
        this.width = width;
        this.height = height;
        this.tiles = new Tile[height][width];
        
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
}
