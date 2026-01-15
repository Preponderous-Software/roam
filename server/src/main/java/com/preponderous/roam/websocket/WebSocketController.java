package com.preponderous.roam.websocket;

import com.preponderous.roam.dto.websocket.HeartbeatMessage;
import com.preponderous.roam.service.RateLimitService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.simp.annotation.SendToUser;
import org.springframework.stereotype.Controller;

import java.security.Principal;

/**
 * WebSocket controller for handling client messages.
 * Manages heartbeat/ping-pong and other client-initiated WebSocket messages.
 * 
 * @author Daniel McCoy Stephenson
 */
@Controller
public class WebSocketController {

    @Autowired
    private RateLimitService rateLimitService;

    /**
     * Handle heartbeat/ping messages from clients.
     * Responds with a pong message to keep connection alive.
     */
    @MessageMapping("/heartbeat")
    @SendToUser("/queue/heartbeat")
    public HeartbeatMessage handleHeartbeat(HeartbeatMessage heartbeat, Principal principal) {
        // Apply rate limiting for WebSocket messages
        if (principal != null) {
            rateLimitService.checkWebSocketMessageLimit(principal.getName());
        }
        
        HeartbeatMessage response = new HeartbeatMessage();
        response.setMessage("pong");
        return response;
    }
}
