package com.preponderous.roam.controller;

import com.preponderous.roam.dto.AuthResponse;
import com.preponderous.roam.dto.PlayerActionRequest;
import com.preponderous.roam.dto.PlayerDTO;
import com.preponderous.roam.dto.RegisterRequest;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.InventorySlot;
import com.preponderous.roam.service.GameService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests for PlayerController.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class PlayerControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private GameService gameService;
    
    private String authToken;
    private String username;

    private String getBaseUrl() {
        return "http://localhost:" + port + "/api/v1/session";
    }
    
    @BeforeEach
    void setUp() {
        // Register and login to get auth token
        username = "testuser" + System.currentTimeMillis();
        RegisterRequest registerRequest = new RegisterRequest(
                username,
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
    void testConsumeFoodIncrementsStatCounter() {
        // Create a session
        GameState gameState = gameService.createSession(username);
        String sessionId = gameState.getSessionId();
        
        // Add an apple to the player's inventory
        InventorySlot slot = gameState.getPlayer().getInventory().getInventorySlots().get(0);
        slot.add("Apple");
        
        // Get initial foodEaten count
        String getPlayerUrl = getBaseUrl() + "/" + sessionId + "/player";
        HttpEntity<Void> getRequest = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<PlayerDTO> initialResponse = restTemplate.exchange(
                getPlayerUrl, 
                HttpMethod.GET, 
                getRequest, 
                PlayerDTO.class
        );
        assertEquals(HttpStatus.OK, initialResponse.getStatusCode());
        int initialFoodEaten = initialResponse.getBody().getFoodEaten();
        
        // Consume the apple
        String consumeUrl = getBaseUrl() + "/" + sessionId + "/player/action";
        PlayerActionRequest consumeRequest = new PlayerActionRequest();
        consumeRequest.setAction("consume");
        consumeRequest.setItemName("Apple");
        
        HttpEntity<PlayerActionRequest> request = new HttpEntity<>(consumeRequest, getAuthHeaders());
        ResponseEntity<PlayerDTO> response = restTemplate.exchange(
                consumeUrl, 
                HttpMethod.POST, 
                request, 
                PlayerDTO.class
        );
        
        // Verify response
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        
        // Verify foodEaten stat was incremented
        assertEquals(initialFoodEaten + 1, response.getBody().getFoodEaten(), 
                "foodEaten stat should be incremented by 1 after consuming food");
        
        // Verify the stat persists when fetching player data again
        ResponseEntity<PlayerDTO> finalResponse = restTemplate.exchange(
                getPlayerUrl, 
                HttpMethod.GET, 
                getRequest, 
                PlayerDTO.class
        );
        assertEquals(HttpStatus.OK, finalResponse.getStatusCode());
        assertEquals(initialFoodEaten + 1, finalResponse.getBody().getFoodEaten(), 
                "foodEaten stat should persist after consumption");
    }
    
    @Test
    void testMultipleFoodConsumptionsIncrementsStat() {
        // Create a session
        GameState gameState = gameService.createSession(username);
        String sessionId = gameState.getSessionId();
        
        // Add multiple food items to inventory
        InventorySlot slot1 = gameState.getPlayer().getInventory().getInventorySlots().get(0);
        slot1.add("Apple");
        
        InventorySlot slot2 = gameState.getPlayer().getInventory().getInventorySlots().get(1);
        slot2.add("Berry");
        
        // Get initial foodEaten count
        String getPlayerUrl = getBaseUrl() + "/" + sessionId + "/player";
        HttpEntity<Void> getRequest = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<PlayerDTO> initialResponse = restTemplate.exchange(
                getPlayerUrl, 
                HttpMethod.GET, 
                getRequest, 
                PlayerDTO.class
        );
        int initialFoodEaten = initialResponse.getBody().getFoodEaten();
        
        // Consume first food item
        String consumeUrl = getBaseUrl() + "/" + sessionId + "/player/action";
        PlayerActionRequest consumeRequest1 = new PlayerActionRequest();
        consumeRequest1.setAction("consume");
        consumeRequest1.setItemName("Apple");
        
        HttpEntity<PlayerActionRequest> request1 = new HttpEntity<>(consumeRequest1, getAuthHeaders());
        restTemplate.exchange(consumeUrl, HttpMethod.POST, request1, PlayerDTO.class);
        
        // Consume second food item
        PlayerActionRequest consumeRequest2 = new PlayerActionRequest();
        consumeRequest2.setAction("consume");
        consumeRequest2.setItemName("Berry");
        
        HttpEntity<PlayerActionRequest> request2 = new HttpEntity<>(consumeRequest2, getAuthHeaders());
        ResponseEntity<PlayerDTO> response2 = restTemplate.exchange(
                consumeUrl, 
                HttpMethod.POST, 
                request2, 
                PlayerDTO.class
        );
        
        // Verify foodEaten was incremented twice
        assertEquals(initialFoodEaten + 2, response2.getBody().getFoodEaten(), 
                "foodEaten stat should be incremented by 2 after consuming two food items");
    }
    
    @Test
    void testGetPlayer_ReturnsStatsFields() {
        // Create a session
        GameState gameState = gameService.createSession(username);
        String sessionId = gameState.getSessionId();
        
        // Set some stats values
        gameState.getPlayer().setScore(100);
        gameState.getPlayer().setRoomsExplored(5);
        gameState.getPlayer().setFoodEaten(3);
        gameState.getPlayer().setNumberOfDeaths(1);
        
        // Get player data
        String getPlayerUrl = getBaseUrl() + "/" + sessionId + "/player";
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<PlayerDTO> response = restTemplate.exchange(
                getPlayerUrl, 
                HttpMethod.GET, 
                request, 
                PlayerDTO.class
        );
        
        // Verify stats are returned
        assertEquals(HttpStatus.OK, response.getStatusCode());
        PlayerDTO player = response.getBody();
        assertNotNull(player);
        assertEquals(100, player.getScore());
        assertEquals(5, player.getRoomsExplored());
        assertEquals(3, player.getFoodEaten());
        assertEquals(1, player.getNumberOfDeaths());
    }
}
