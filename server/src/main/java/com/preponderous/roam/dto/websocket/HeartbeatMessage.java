package com.preponderous.roam.dto.websocket;

/**
 * WebSocket message for heartbeat/ping-pong.
 * 
 * @author Daniel McCoy Stephenson
 */
public class HeartbeatMessage extends WebSocketMessage {
    private String message;

    public HeartbeatMessage() {
        super();
        this.message = "ping";
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
