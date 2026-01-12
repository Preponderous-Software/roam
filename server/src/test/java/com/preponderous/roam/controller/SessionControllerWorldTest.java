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

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class SessionControllerWorldTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private GameService gameService;
    
    private String authToken;

    private String getBaseUrl() {
        return "http://localhost:" + port + "/api/v1/session";
    }
    
    @BeforeEach
    void setUp() {
        // Register and login to get auth token
        RegisterRequest registerRequest = new RegisterRequest(
                "testuser" + System.currentTimeMillis(),
                "password123",
                "test" + System.currentTimeMillis() + "@example.com"
        );
        
        ResponseEntity<AuthResponse> authResponse = restTemplate.postForEntity(
                "http://localhost:" + port + "/api/v1/auth/register",
                registerRequest,
                AuthResponse.class
        );
        
        authToken = authResponse.getBody().getAccessToken();
    }
    
    private HttpHeaders getAuthHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(authToken);
        return headers;
    }

    @Test
    void testGetWorld() {
        // Create a session
        GameState gameState = gameService.createSession();
        String sessionId = gameState.getSessionId();

        // Get the world
        String url = getBaseUrl() + "/" + sessionId + "/world";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<WorldDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, WorldDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());

        WorldDTO world = response.getBody();
        assertNotNull(world);
        assertTrue(world.getSeed() > 0);
        assertEquals(20, world.getRoomWidth());  // Updated to match new default
        assertEquals(20, world.getRoomHeight());  // Updated to match new default
        assertTrue(world.getResourceDensity() > 0);
        assertEquals(0.0, world.getHazardDensity());  // Updated: hazards removed
        assertNotNull(world.getRooms());
    }

    @Test
    void testGetWorld_InvalidSession() {
        String url = getBaseUrl() + "/invalid-session-id/world";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<WorldDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, WorldDTO.class);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }

    @Test
    void testGetRoom() {
        // Create a session
        GameState gameState = gameService.createSession();
        String sessionId = gameState.getSessionId();

        // Get a specific room
        String url = getBaseUrl() + "/" + sessionId + "/room/0/0";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<RoomDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, RoomDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());

        RoomDTO room = response.getBody();
        assertNotNull(room);
        assertEquals(0, room.getRoomX());
        assertEquals(0, room.getRoomY());
        assertEquals(20, room.getWidth());  // Updated to match new default
        assertEquals(20, room.getHeight());  // Updated to match new default
        assertNotNull(room.getTiles());
        assertEquals(20 * 20, room.getTiles().size());  // Updated to match new default
    }

    @Test
    void testGetRoom_GenerateNewRoom() {
        // Create a session
        GameState gameState = gameService.createSession();
        String sessionId = gameState.getSessionId();

        // Get a room that hasn't been generated yet
        String url = getBaseUrl() + "/" + sessionId + "/room/5/5";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<RoomDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, RoomDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());

        RoomDTO room = response.getBody();
        assertNotNull(room);
        assertEquals(5, room.getRoomX());
        assertEquals(5, room.getRoomY());
    }

    @Test
    void testGetRoom_InvalidSession() {
        String url = getBaseUrl() + "/invalid-session-id/room/0/0";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<RoomDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, RoomDTO.class);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }

    @Test
    void testGetRoom_NegativeCoordinates() {
        // Create a session
        GameState gameState = gameService.createSession();
        String sessionId = gameState.getSessionId();

        // Test negative coordinates
        String url = getBaseUrl() + "/" + sessionId + "/room/-1/-1";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<RoomDTO> response = restTemplate.exchange(url, HttpMethod.GET, request, RoomDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());

        RoomDTO room = response.getBody();
        assertEquals(-1, room.getRoomX());
        assertEquals(-1, room.getRoomY());
    }
}
