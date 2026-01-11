package com.preponderous.roam.dto;

import java.util.List;

/**
 * DTO for room data transfer.
 * 
 * @author Daniel McCoy Stephenson
 */
public class RoomDTO {
    private int roomX;
    private int roomY;
    private int width;
    private int height;
    private List<TileDTO> tiles;

    public RoomDTO() {
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

    public List<TileDTO> getTiles() {
        return tiles;
    }

    public void setTiles(List<TileDTO> tiles) {
        this.tiles = tiles;
    }
}
