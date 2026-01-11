package com.preponderous.roam.controller;

import com.preponderous.roam.dto.RoomDTO;
import com.preponderous.roam.dto.SessionDTO;
import com.preponderous.roam.dto.WorldDTO;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.service.GameService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class SessionControllerWorldTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private GameService gameService;

    private String getBaseUrl() {
        return "http://localhost:" + port + "/api/v1/session";
    }

    @Test
    void testGetWorld() {
        // Create a session
        GameState gameState = gameService.createSession();
        String sessionId = gameState.getSessionId();

        // Get the world
        String url = getBaseUrl() + "/" + sessionId + "/world";
        ResponseEntity<WorldDTO> response = restTemplate.getForEntity(url, WorldDTO.class);

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
        ResponseEntity<WorldDTO> response = restTemplate.getForEntity(url, WorldDTO.class);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }

    @Test
    void testGetRoom() {
        // Create a session
        GameState gameState = gameService.createSession();
        String sessionId = gameState.getSessionId();

        // Get a specific room
        String url = getBaseUrl() + "/" + sessionId + "/room/0/0";
        ResponseEntity<RoomDTO> response = restTemplate.getForEntity(url, RoomDTO.class);

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
        ResponseEntity<RoomDTO> response = restTemplate.getForEntity(url, RoomDTO.class);

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
        ResponseEntity<RoomDTO> response = restTemplate.getForEntity(url, RoomDTO.class);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }

    @Test
    void testGetRoom_NegativeCoordinates() {
        // Create a session
        GameState gameState = gameService.createSession();
        String sessionId = gameState.getSessionId();

        // Test negative coordinates
        String url = getBaseUrl() + "/" + sessionId + "/room/-1/-1";
        ResponseEntity<RoomDTO> response = restTemplate.getForEntity(url, RoomDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());

        RoomDTO room = response.getBody();
        assertEquals(-1, room.getRoomX());
        assertEquals(-1, room.getRoomY());
    }
}
