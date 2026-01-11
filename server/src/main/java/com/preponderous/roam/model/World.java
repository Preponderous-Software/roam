package com.preponderous.roam.model;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Represents the game world containing multiple rooms.
 * 
 * @author Daniel McCoy Stephenson
 */
public class World {
    private final WorldConfig config;
    private final Map<String, Room> rooms;

    public World(WorldConfig config) {
        this.config = config;
        this.rooms = new ConcurrentHashMap<>();
    }

    public WorldConfig getConfig() {
        return config;
    }

    public Map<String, Room> getRooms() {
        return rooms;
    }

    public Room getRoom(int x, int y) {
        return rooms.get(getRoomKey(x, y));
    }

    public void addRoom(Room room) {
        rooms.put(getRoomKey(room.getRoomX(), room.getRoomY()), room);
    }

    public boolean hasRoom(int x, int y) {
        return rooms.containsKey(getRoomKey(x, y));
    }

    private String getRoomKey(int x, int y) {
        return x + "," + y;
    }
}
