package com.preponderous.roam.dto.websocket;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

/**
 * Base class for WebSocket messages.
 * Uses Jackson polymorphic type handling to serialize/deserialize different message types.
 * 
 * @author Daniel McCoy Stephenson
 */
@JsonTypeInfo(
    use = JsonTypeInfo.Id.NAME,
    include = JsonTypeInfo.As.PROPERTY,
    property = "type"
)
@JsonSubTypes({
    @JsonSubTypes.Type(value = PlayerPositionUpdate.class, name = "PLAYER_POSITION"),
    @JsonSubTypes.Type(value = EntityStateUpdate.class, name = "ENTITY_STATE"),
    @JsonSubTypes.Type(value = WorldEventMessage.class, name = "WORLD_EVENT"),
    @JsonSubTypes.Type(value = TickUpdate.class, name = "TICK_UPDATE"),
    @JsonSubTypes.Type(value = HeartbeatMessage.class, name = "HEARTBEAT")
})
public abstract class WebSocketMessage {
    private String sessionId;
    private long timestamp;

    public WebSocketMessage() {
        this.timestamp = System.currentTimeMillis();
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }
}
