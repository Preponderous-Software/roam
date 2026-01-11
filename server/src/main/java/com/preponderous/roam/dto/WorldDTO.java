package com.preponderous.roam.dto;

import java.util.List;

/**
 * DTO for world data transfer.
 * 
 * @author Daniel McCoy Stephenson
 */
public class WorldDTO {
    private long seed;
    private int roomWidth;
    private int roomHeight;
    private double resourceDensity;
    private double hazardDensity;
    private List<RoomDTO> rooms;

    public WorldDTO() {
    }

    public long getSeed() {
        return seed;
    }

    public void setSeed(long seed) {
        this.seed = seed;
    }

    public int getRoomWidth() {
        return roomWidth;
    }

    public void setRoomWidth(int roomWidth) {
        this.roomWidth = roomWidth;
    }

    public int getRoomHeight() {
        return roomHeight;
    }

    public void setRoomHeight(int roomHeight) {
        this.roomHeight = roomHeight;
    }

    public double getResourceDensity() {
        return resourceDensity;
    }

    public void setResourceDensity(double resourceDensity) {
        this.resourceDensity = resourceDensity;
    }

    public double getHazardDensity() {
        return hazardDensity;
    }

    public void setHazardDensity(double hazardDensity) {
        this.hazardDensity = hazardDensity;
    }

    public List<RoomDTO> getRooms() {
        return rooms;
    }

    public void setRooms(List<RoomDTO> rooms) {
        this.rooms = rooms;
    }
}
