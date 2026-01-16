package com.preponderous.roam.controller;

import com.preponderous.roam.dto.AuthResponse;
import com.preponderous.roam.dto.InventoryDTO;
import com.preponderous.roam.dto.RegisterRequest;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.service.GameService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.*;
import org.springframework.web.util.UriComponentsBuilder;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class InventoryControllerTest {

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
    void testSwapSlots_EmptySlots() {
        // Create a session
        GameState gameState = gameService.createSession(username);
        String sessionId = gameState.getSessionId();

        // Swap two empty slots
        String url = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/" + sessionId + "/inventory/swap")
                .queryParam("fromSlot", 0)
                .queryParam("toSlot", 1)
                .toUriString();
        
        HttpEntity<Void> request = new HttpEntity<>(getAuthHeaders());
        ResponseEntity<InventoryDTO> response = restTemplate.exchange(url, HttpMethod.POST, request, InventoryDTO.class);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        
        InventoryDTO inventory = response.getBody();
        assertNotNull(inventory.getSlots());
        assertEquals(25, inventory.getSlots().size());
    }

    @Test
    void testSwapSlots_WithItems() {
        // Create a session
        GameState gameState = gameService.createSession(username);
        String sessionId = gameState.getSessionId();

        // Add items to inventory
        String addUrl1 = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/" + sessionId + "/inventory/add")
                .queryParam("itemName", "Stone")
                .toUriString();
        restTemplate.exchange(addUrl1, HttpMethod.POST, new HttpEntity<>(getAuthHeaders()), InventoryDTO.class);

        String addUrl2 = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/" + sessionId + "/inventory/add")
                .queryParam("itemName", "Wood")
                .toUriString();
        restTemplate.exchange(addUrl2, HttpMethod.POST, new HttpEntity<>(getAuthHeaders()), InventoryDTO.class);

        // Get initial inventory state
        String getUrl = getBaseUrl() + "/" + sessionId + "/inventory";
        ResponseEntity<InventoryDTO> initialResponse = restTemplate.exchange(
                getUrl, HttpMethod.GET, new HttpEntity<>(getAuthHeaders()), InventoryDTO.class);
        InventoryDTO initialInventory = initialResponse.getBody();
        
        String slot0Item = initialInventory.getSlots().get(0).getItemName();
        String slot1Item = initialInventory.getSlots().get(1).getItemName();
        
        // Swap the two slots
        String swapUrl = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/" + sessionId + "/inventory/swap")
                .queryParam("fromSlot", 0)
                .queryParam("toSlot", 1)
                .toUriString();
        
        ResponseEntity<InventoryDTO> swapResponse = restTemplate.exchange(
                swapUrl, HttpMethod.POST, new HttpEntity<>(getAuthHeaders()), InventoryDTO.class);

        assertEquals(HttpStatus.OK, swapResponse.getStatusCode());
        assertNotNull(swapResponse.getBody());
        
        InventoryDTO swappedInventory = swapResponse.getBody();
        
        // Verify the slots were swapped
        assertEquals(slot1Item, swappedInventory.getSlots().get(0).getItemName());
        assertEquals(slot0Item, swappedInventory.getSlots().get(1).getItemName());
    }

    @Test
    void testSwapSlots_SameSlot() {
        // Create a session
        GameState gameState = gameService.createSession(username);
        String sessionId = gameState.getSessionId();

        // Add an item to inventory
        String addUrl = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/" + sessionId + "/inventory/add")
                .queryParam("itemName", "Stone")
                .toUriString();
        restTemplate.exchange(addUrl, HttpMethod.POST, new HttpEntity<>(getAuthHeaders()), InventoryDTO.class);

        // Get initial inventory state
        String getUrl = getBaseUrl() + "/" + sessionId + "/inventory";
        ResponseEntity<InventoryDTO> initialResponse = restTemplate.exchange(
                getUrl, HttpMethod.GET, new HttpEntity<>(getAuthHeaders()), InventoryDTO.class);
        InventoryDTO initialInventory = initialResponse.getBody();
        
        String slot0Item = initialInventory.getSlots().get(0).getItemName();

        // Swap slot with itself
        String swapUrl = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/" + sessionId + "/inventory/swap")
                .queryParam("fromSlot", 0)
                .queryParam("toSlot", 0)
                .toUriString();
        
        ResponseEntity<InventoryDTO> swapResponse = restTemplate.exchange(
                swapUrl, HttpMethod.POST, new HttpEntity<>(getAuthHeaders()), InventoryDTO.class);

        assertEquals(HttpStatus.OK, swapResponse.getStatusCode());
        assertNotNull(swapResponse.getBody());
        
        InventoryDTO swappedInventory = swapResponse.getBody();
        
        // Verify the slot is unchanged
        assertEquals(slot0Item, swappedInventory.getSlots().get(0).getItemName());
    }

    @Test
    void testSwapSlots_OutOfBounds() {
        // Create a session
        GameState gameState = gameService.createSession(username);
        String sessionId = gameState.getSessionId();

        // Try to swap with out-of-bounds slot index (negative)
        String url1 = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/" + sessionId + "/inventory/swap")
                .queryParam("fromSlot", -1)
                .queryParam("toSlot", 0)
                .toUriString();
        
        ResponseEntity<String> response1 = restTemplate.exchange(
                url1, HttpMethod.POST, new HttpEntity<>(getAuthHeaders()), String.class);

        assertEquals(HttpStatus.BAD_REQUEST, response1.getStatusCode());

        // Try to swap with out-of-bounds slot index (too high)
        String url2 = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/" + sessionId + "/inventory/swap")
                .queryParam("fromSlot", 0)
                .queryParam("toSlot", 25)
                .toUriString();
        
        ResponseEntity<String> response2 = restTemplate.exchange(
                url2, HttpMethod.POST, new HttpEntity<>(getAuthHeaders()), String.class);

        assertEquals(HttpStatus.BAD_REQUEST, response2.getStatusCode());
    }

    @Test
    void testSwapSlots_InvalidSession() {
        String url = UriComponentsBuilder.fromHttpUrl(getBaseUrl() + "/invalid-session-id/inventory/swap")
                .queryParam("fromSlot", 0)
                .queryParam("toSlot", 1)
                .toUriString();
        
        ResponseEntity<String> response = restTemplate.exchange(
                url, HttpMethod.POST, new HttpEntity<>(getAuthHeaders()), String.class);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }
}
