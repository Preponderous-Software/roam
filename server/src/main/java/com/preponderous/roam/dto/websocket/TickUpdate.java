package com.preponderous.roam.dto.websocket;

/**
 * WebSocket message for game tick updates.
 * 
 * @author Daniel McCoy Stephenson
 */
public class TickUpdate extends WebSocketMessage {
    private long currentTick;

    public TickUpdate() {
        super();
    }

    public long getCurrentTick() {
        return currentTick;
    }

    public void setCurrentTick(long currentTick) {
        this.currentTick = currentTick;
    }
}
