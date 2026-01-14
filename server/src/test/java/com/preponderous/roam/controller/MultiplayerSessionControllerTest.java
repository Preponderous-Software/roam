package com.preponderous.roam.controller;

import com.preponderous.roam.dto.*;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.service.GameService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.*;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for multiplayer session endpoints.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class MultiplayerSessionControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private GameService gameService;
    
    private String authToken1;
    private String username1;
    private String authToken2;
    private String username2;
    private String sessionId;

    private String getBaseUrl() {
        return "http://localhost:" + port + "/api/v1/session";
    }
    
    @BeforeEach
    void setUp() {
        // Register and login first user
        username1 = "user1-" + System.currentTimeMillis();
        RegisterRequest registerRequest1 = new RegisterRequest(
                username1,
                "password123",
                "user1-" + System.currentTimeMillis() + "@example.com"
        );
        
        ResponseEntity<AuthResponse> authResponse1 = restTemplate.postForEntity(
                "http://localhost:" + port + "/api/v1/auth/register",
                registerRequest1,
                AuthResponse.class
        );
        authToken1 = authResponse1.getBody().getAccessToken();
        
        // Register and login second user
        username2 = "user2-" + System.currentTimeMillis();
        RegisterRequest registerRequest2 = new RegisterRequest(
                username2,
                "password123",
                "user2-" + System.currentTimeMillis() + "@example.com"
        );
        
        ResponseEntity<AuthResponse> authResponse2 = restTemplate.postForEntity(
                "http://localhost:" + port + "/api/v1/auth/register",
                registerRequest2,
                AuthResponse.class
        );
        authToken2 = authResponse2.getBody().getAccessToken();
        
        // Create a session with user1
        GameState gameState = gameService.createSession(username1);
        sessionId = gameState.getSessionId();
    }
    
    private HttpHeaders getAuthHeaders(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        return headers;
    }

    @Test
    void testGetSession_ContainsMultiplayerMetadata() {
        String url = getBaseUrl() + "/" + sessionId;
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken1));
        ResponseEntity<SessionDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, SessionDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        SessionDTO session = response.getBody();
        assertNotNull(session);
        
        assertEquals(sessionId, session.getSessionId());
        assertEquals(username1, session.getOwnerId());
        assertEquals(1, session.getPlayerCount());
        assertEquals(GameState.MAX_PLAYERS_PER_SESSION, session.getMaxPlayers());
        assertFalse(session.isFull());
        
        assertNotNull(session.getPlayers());
        assertEquals(1, session.getPlayers().size());
        assertTrue(session.getPlayers().containsKey(username1));
    }

    @Test
    void testJoinSession_AddsSecondPlayer() {
        String url = getBaseUrl() + "/" + sessionId + "/join";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken2));
        ResponseEntity<SessionDTO> response = restTemplate.exchange(url, HttpMethod.POST, request, SessionDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        SessionDTO session = response.getBody();
        assertNotNull(session);
        
        assertEquals(2, session.getPlayerCount());
        assertEquals(2, session.getPlayers().size());
        assertTrue(session.getPlayers().containsKey(username1));
        assertTrue(session.getPlayers().containsKey(username2));
        
        // Verify both players have correct data
        PlayerDTO player1 = session.getPlayers().get(username1);
        PlayerDTO player2 = session.getPlayers().get(username2);
        
        assertNotNull(player1);
        assertNotNull(player2);
        assertEquals(username1, player1.getUserId());
        assertEquals(username2, player2.getUserId());
    }

    @Test
    void testJoinSession_NonExistentSession() {
        String url = getBaseUrl() + "/invalid-session-id/join";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken2));
        ResponseEntity<SessionDTO> response = restTemplate.exchange(url, HttpMethod.POST, request, SessionDTO.class);

        // Returns CONFLICT instead of NOT_FOUND to avoid leaking session existence
        assertEquals(HttpStatus.CONFLICT, response.getStatusCode());
    }

    @Test
    void testLeaveSession_RemovesPlayer() {
        // First, user2 joins the session
        gameService.joinSession(sessionId, username2);
        
        // Then user2 leaves
        String url = getBaseUrl() + "/" + sessionId + "/leave";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken2));
        ResponseEntity<Map> response = restTemplate.exchange(url, HttpMethod.POST, request, Map.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        
        // Verify user2 is no longer in the session
        GameState gameState = gameService.getSession(sessionId, username1);
        assertEquals(1, gameState.getPlayerCount());
        assertFalse(gameState.hasPlayer(username2));
    }

    @Test
    void testLeaveSession_OwnerCannotLeave() {
        String url = getBaseUrl() + "/" + sessionId + "/leave";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken1));
        ResponseEntity<Map> response = restTemplate.exchange(url, HttpMethod.POST, request, Map.class);

        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
        
        // Verify owner is still in the session
        GameState gameState = gameService.getSession(sessionId, username1);
        assertEquals(1, gameState.getPlayerCount());
        assertTrue(gameState.hasPlayer(username1));
    }

    @Test
    void testGetPlayers_ReturnsAllPlayers() {
        // Add second player
        gameService.joinSession(sessionId, username2);
        
        String url = getBaseUrl() + "/" + sessionId + "/players";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken1));
        ResponseEntity<Map> response = restTemplate.exchange(url, HttpMethod.GET, request, Map.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        Map<String, Object> players = response.getBody();
        assertNotNull(players);
        assertEquals(2, players.size());
        assertTrue(players.containsKey(username1));
        assertTrue(players.containsKey(username2));
    }

    @Test
    void testGetSession_NonParticipantCannotAccess() {
        // user2 is not in the session
        String url = getBaseUrl() + "/" + sessionId;
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken2));
        ResponseEntity<SessionDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, SessionDTO.class);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }

    @Test
    void testGetSession_ParticipantCanAccess() {
        // Add user2 to the session
        gameService.joinSession(sessionId, username2);
        
        // user2 should now be able to access the session
        String url = getBaseUrl() + "/" + sessionId;
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken2));
        ResponseEntity<SessionDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, SessionDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        SessionDTO session = response.getBody();
        assertNotNull(session);
        assertEquals(sessionId, session.getSessionId());
        assertEquals(2, session.getPlayerCount());
    }

    @Test
    void testJoinSession_FullSession() {
        // Fill the session to capacity
        for (int i = 0; i < GameState.MAX_PLAYERS_PER_SESSION - 1; i++) {
            gameService.joinSession(sessionId, "player-" + i);
        }
        
        // Try to join with user2
        String url = getBaseUrl() + "/" + sessionId + "/join";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders(authToken2));
        ResponseEntity<SessionDTO> response = restTemplate.exchange(url, HttpMethod.POST, request, SessionDTO.class);

        assertEquals(HttpStatus.CONFLICT, response.getStatusCode());
        
        // Verify session is still full
        GameState gameState = gameService.getSession(sessionId, username1);
        assertTrue(gameState.isFull());
        assertEquals(GameState.MAX_PLAYERS_PER_SESSION, gameState.getPlayerCount());
    }
}
