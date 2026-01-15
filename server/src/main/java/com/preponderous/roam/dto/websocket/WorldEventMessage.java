package com.preponderous.roam.dto.websocket;

/**
 * WebSocket message for world events.
 * 
 * @author Daniel McCoy Stephenson
 */
public class WorldEventMessage extends WebSocketMessage {
    private String eventType;
    private String description;
    private int roomX;
    private int roomY;

    public WorldEventMessage() {
        super();
    }

    public String getEventType() {
        return eventType;
    }

    public void setEventType(String eventType) {
        this.eventType = eventType;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
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
}
