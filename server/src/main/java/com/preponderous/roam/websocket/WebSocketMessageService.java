package com.preponderous.roam.websocket;

import com.preponderous.roam.dto.websocket.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

/**
 * Service for broadcasting WebSocket messages to connected clients.
 * Provides methods to send real-time updates for player positions, entity states, and world events.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class WebSocketMessageService {

    @Autowired
    private SimpMessagingTemplate messagingTemplate;

    /**
     * Broadcast a player position update to all clients subscribed to the session.
     */
    public void broadcastPlayerPosition(String sessionId, PlayerPositionUpdate update) {
        update.setSessionId(sessionId);
        messagingTemplate.convertAndSend("/topic/session/" + sessionId + "/player", update);
    }

    /**
     * Broadcast an entity state update to all clients subscribed to the session.
     */
    public void broadcastEntityState(String sessionId, EntityStateUpdate update) {
        update.setSessionId(sessionId);
        messagingTemplate.convertAndSend("/topic/session/" + sessionId + "/entity", update);
    }

    /**
     * Broadcast a world event to all clients subscribed to the session.
     */
    public void broadcastWorldEvent(String sessionId, WorldEventMessage event) {
        event.setSessionId(sessionId);
        messagingTemplate.convertAndSend("/topic/session/" + sessionId + "/world", event);
    }

    /**
     * Broadcast a tick update to all clients subscribed to the session.
     */
    public void broadcastTickUpdate(String sessionId, TickUpdate update) {
        update.setSessionId(sessionId);
        messagingTemplate.convertAndSend("/topic/session/" + sessionId + "/tick", update);
    }

    /**
     * Send a heartbeat response to a specific user.
     */
    public void sendHeartbeat(String username, HeartbeatMessage heartbeat) {
        messagingTemplate.convertAndSendToUser(username, "/queue/heartbeat", heartbeat);
    }
}
