package com.preponderous.roam.websocket;

import com.preponderous.roam.dto.websocket.*;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.messaging.converter.MappingJackson2MessageConverter;
import org.springframework.messaging.simp.stomp.*;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.web.socket.client.standard.StandardWebSocketClient;
import org.springframework.web.socket.messaging.WebSocketStompClient;
import org.springframework.web.socket.sockjs.client.SockJsClient;
import org.springframework.web.socket.sockjs.client.WebSocketTransport;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests for WebSocket functionality.
 * Tests real-time message broadcasting for player positions, entity states, and world events.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class WebSocketIntegrationTest {

    @LocalServerPort
    private int port;

    /**
     * Test WebSocket connection establishment and heartbeat.
     */
    @Test
    public void testWebSocketConnection() throws Exception {
        BlockingQueue<HeartbeatMessage> messages = new LinkedBlockingQueue<>();
        
        WebSocketStompClient stompClient = createStompClient();
        StompSession session = stompClient.connectAsync(
            getWebSocketUrl(), 
            new StompSessionHandlerAdapter() {}
        ).get(10, TimeUnit.SECONDS);
        
        assertNotNull(session);
        assertTrue(session.isConnected());
        
        // Subscribe to heartbeat queue
        session.subscribe("/user/queue/heartbeat", new StompFrameHandler() {
            @Override
            public Type getPayloadType(StompHeaders headers) {
                return HeartbeatMessage.class;
            }

            @Override
            public void handleFrame(StompHeaders headers, Object payload) {
                boolean offered = messages.offer((HeartbeatMessage) payload);
                if (!offered) {
                    fail("Failed to enqueue heartbeat message in test queue");
                }
            }
        });
        
        // Send heartbeat
        HeartbeatMessage heartbeat = new HeartbeatMessage();
        heartbeat.setMessage("ping");
        session.send("/app/heartbeat", heartbeat);
        
        // Wait for response
        HeartbeatMessage response = messages.poll(5, TimeUnit.SECONDS);
        assertNotNull(response, "Should receive heartbeat response");
        assertEquals("pong", response.getMessage());
        
        session.disconnect();
    }

    /**
     * Test player position update subscription.
     */
    @Test
    public void testPlayerPositionSubscription() throws Exception {
        BlockingQueue<PlayerPositionUpdate> messages = new LinkedBlockingQueue<>();
        String testSessionId = "test-session-123";
        
        WebSocketStompClient stompClient = createStompClient();
        StompSession session = stompClient.connectAsync(
            getWebSocketUrl(), 
            new StompSessionHandlerAdapter() {}
        ).get(10, TimeUnit.SECONDS);
        
        // Subscribe to player position updates for test session
        session.subscribe("/topic/session/" + testSessionId + "/player", new StompFrameHandler() {
            @Override
            public Type getPayloadType(StompHeaders headers) {
                return PlayerPositionUpdate.class;
            }

            @Override
            public void handleFrame(StompHeaders headers, Object payload) {
                boolean offered = messages.offer((PlayerPositionUpdate) payload);
                assertTrue(offered, "Failed to enqueue PlayerPositionUpdate");
            }
        });
        
        // Small delay to ensure subscription is registered
        TimeUnit.MILLISECONDS.sleep(100);
        
        // Verify subscription was successful (no errors thrown)
        assertTrue(session.isConnected());
        
        session.disconnect();
    }

    /**
     * Test entity state update subscription.
     */
    @Test
    public void testEntityStateSubscription() throws Exception {
        BlockingQueue<EntityStateUpdate> messages = new LinkedBlockingQueue<>();
        String testSessionId = "test-session-456";
        
        WebSocketStompClient stompClient = createStompClient();
        StompSession session = stompClient.connectAsync(
            getWebSocketUrl(), 
            new StompSessionHandlerAdapter() {}
        ).get(10, TimeUnit.SECONDS);
        
        // Subscribe to entity state updates for test session
        session.subscribe("/topic/session/" + testSessionId + "/entity", new StompFrameHandler() {
            @Override
            public Type getPayloadType(StompHeaders headers) {
                return EntityStateUpdate.class;
            }

            @Override
            public void handleFrame(StompHeaders headers, Object payload) {
                boolean offered = messages.offer((EntityStateUpdate) payload);
                assertTrue(offered, "Failed to enqueue EntityStateUpdate");
            }
        });
        
        // Small delay to ensure subscription is registered
        TimeUnit.MILLISECONDS.sleep(100);
        
        // Verify subscription was successful
        assertTrue(session.isConnected());
        
        session.disconnect();
    }

    /**
     * Test tick update subscription.
     */
    @Test
    public void testTickUpdateSubscription() throws Exception {
        BlockingQueue<TickUpdate> messages = new LinkedBlockingQueue<>();
        String testSessionId = "test-session-789";
        
        WebSocketStompClient stompClient = createStompClient();
        StompSession session = stompClient.connectAsync(
            getWebSocketUrl(), 
            new StompSessionHandlerAdapter() {}
        ).get(10, TimeUnit.SECONDS);
        
        // Subscribe to tick updates for test session
        session.subscribe("/topic/session/" + testSessionId + "/tick", new StompFrameHandler() {
            @Override
            public Type getPayloadType(StompHeaders headers) {
                return TickUpdate.class;
            }

            @Override
            public void handleFrame(StompHeaders headers, Object payload) {
                boolean offered = messages.offer((TickUpdate) payload);
                assertTrue(offered, "Failed to enqueue TickUpdate");
            }
        });
        
        // Small delay to ensure subscription is registered
        TimeUnit.MILLISECONDS.sleep(100);
        
        // Verify subscription was successful
        assertTrue(session.isConnected());
        
        session.disconnect();
    }

    /**
     * Helper method to create a WebSocket STOMP client.
     */
    private WebSocketStompClient createStompClient() {
        List<org.springframework.web.socket.sockjs.client.Transport> transports = new ArrayList<>();
        transports.add(new WebSocketTransport(new StandardWebSocketClient()));
        
        SockJsClient sockJsClient = new SockJsClient(transports);
        WebSocketStompClient stompClient = new WebSocketStompClient(sockJsClient);
        stompClient.setMessageConverter(new MappingJackson2MessageConverter());
        
        return stompClient;
    }

    /**
     * Helper method to get WebSocket URL.
     */
    private String getWebSocketUrl() {
        return "ws://localhost:" + port + "/ws";
    }
}
