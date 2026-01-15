package com.preponderous.roam.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.preponderous.roam.dto.AuthResponse;
import com.preponderous.roam.dto.PlayerActionRequest;
import com.preponderous.roam.dto.RegisterRequest;
import com.preponderous.roam.dto.SessionInitRequest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for rate limiting functionality.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class RateLimitIntegrationTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    private String accessToken;
    private String sessionId;
    
    @BeforeEach
    void setUp() throws Exception {
        // Register a unique user for each test
        String username = "ratelimituser" + System.currentTimeMillis();
        RegisterRequest registerRequest = new RegisterRequest(
                username,
                "password123",
                "ratelimit" + System.currentTimeMillis() + "@example.com"
        );
        
        MvcResult registerResult = mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated())
                .andReturn();
        
        AuthResponse authResponse = objectMapper.readValue(
                registerResult.getResponse().getContentAsString(), 
                AuthResponse.class
        );
        accessToken = authResponse.getAccessToken();
        
        // Initialize a session
        SessionInitRequest sessionInitRequest = new SessionInitRequest();
        sessionInitRequest.setSeed(12345L);
        
        MvcResult sessionResult = mockMvc.perform(post("/api/v1/session/init")
                .header("Authorization", "Bearer " + accessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(sessionInitRequest)))
                .andExpect(status().isOk())
                .andReturn();
        
        String sessionResponse = sessionResult.getResponse().getContentAsString();
        sessionId = objectMapper.readTree(sessionResponse).get("sessionId").asText();
    }
    
    @Test
    void testPlayerActionRateLimit_ExceedsLimit() throws Exception {
        PlayerActionRequest request = new PlayerActionRequest();
        request.setAction("move");
        request.setDirection(0);
        
        // Send 11 requests rapidly (limit is 10 per second)
        int successCount = 0;
        int rateLimitCount = 0;
        
        for (int i = 0; i < 11; i++) {
            MvcResult result = mockMvc.perform(post("/api/v1/session/" + sessionId + "/player/action")
                    .header("Authorization", "Bearer " + accessToken)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                    .andReturn();
            
            int status = result.getResponse().getStatus();
            if (status == 200) {
                successCount++;
            } else if (status == 429) {
                rateLimitCount++;
            }
        }
        
        // At least one request should be rate limited
        assert rateLimitCount > 0 : "Expected at least one request to be rate limited";
        assert successCount <= 10 : "Expected at most 10 successful requests";
    }
    
    @Test
    void testPlayerActionRateLimit_Returns429() throws Exception {
        PlayerActionRequest request = new PlayerActionRequest();
        request.setAction("move");
        request.setDirection(0);
        
        // Send 10 requests to fill the bucket
        for (int i = 0; i < 10; i++) {
            mockMvc.perform(post("/api/v1/session/" + sessionId + "/player/action")
                    .header("Authorization", "Bearer " + accessToken)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                    .andExpect(status().isOk());
        }
        
        // 11th request should be rate limited
        mockMvc.perform(post("/api/v1/session/" + sessionId + "/player/action")
                .header("Authorization", "Bearer " + accessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isTooManyRequests())
                .andExpect(jsonPath("$.error").value("Too Many Requests"))
                .andExpect(jsonPath("$.message").value("Rate limit exceeded for player actions. Maximum 10 actions per second."));
    }
    
    @Test
    void testEnergyUpdateRateLimit_Returns429() throws Exception {
        // Send 10 requests to fill the bucket
        for (int i = 0; i < 10; i++) {
            mockMvc.perform(put("/api/v1/session/" + sessionId + "/player/energy")
                    .header("Authorization", "Bearer " + accessToken)
                    .param("amount", "5.0")
                    .param("operation", "add"))
                    .andExpect(status().isOk());
        }
        
        // 11th request should be rate limited
        mockMvc.perform(put("/api/v1/session/" + sessionId + "/player/energy")
                .header("Authorization", "Bearer " + accessToken)
                .param("amount", "5.0")
                .param("operation", "add"))
                .andExpect(status().isTooManyRequests())
                .andExpect(jsonPath("$.error").value("Too Many Requests"))
                .andExpect(jsonPath("$.message").value("Rate limit exceeded for player actions. Maximum 10 actions per second."));
    }
    
    @Test
    void testRateLimitRecovery_AfterWaiting() throws Exception {
        PlayerActionRequest request = new PlayerActionRequest();
        request.setAction("move");
        request.setDirection(0);
        
        // Fill the bucket with 10 requests
        for (int i = 0; i < 10; i++) {
            mockMvc.perform(post("/api/v1/session/" + sessionId + "/player/action")
                    .header("Authorization", "Bearer " + accessToken)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                    .andExpect(status().isOk());
        }
        
        // 11th request should be rate limited
        mockMvc.perform(post("/api/v1/session/" + sessionId + "/player/action")
                .header("Authorization", "Bearer " + accessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isTooManyRequests());
        
        // Wait for bucket to refill (1.5 seconds to ensure refill)
        Thread.sleep(1500);
        
        // Request should now succeed
        mockMvc.perform(post("/api/v1/session/" + sessionId + "/player/action")
                .header("Authorization", "Bearer " + accessToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk());
    }
}
