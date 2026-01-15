package com.preponderous.roam.dto.websocket;

/**
 * WebSocket message for player position updates.
 * 
 * @author Daniel McCoy Stephenson
 */
public class PlayerPositionUpdate extends WebSocketMessage {
    private String username;
    private int roomX;
    private int roomY;
    private int tileX;
    private int tileY;
    private int direction;
    private boolean gathering;
    private boolean placing;
    private boolean crouching;

    public PlayerPositionUpdate() {
        super();
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
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

    public int getDirection() {
        return direction;
    }

    public void setDirection(int direction) {
        this.direction = direction;
    }

    public boolean isGathering() {
        return gathering;
    }

    public void setGathering(boolean gathering) {
        this.gathering = gathering;
    }

    public boolean isPlacing() {
        return placing;
    }

    public void setPlacing(boolean placing) {
        this.placing = placing;
    }

    public boolean isCrouching() {
        return crouching;
    }

    public void setCrouching(boolean crouching) {
        this.crouching = crouching;
    }
}
