package com.preponderous.roam.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.preponderous.roam.dto.AuthResponse;
import com.preponderous.roam.dto.LoginRequest;
import com.preponderous.roam.dto.RefreshTokenRequest;
import com.preponderous.roam.dto.RegisterRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for authentication endpoints.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AuthControllerIntegrationTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @Test
    void testRegisterUser() throws Exception {
        RegisterRequest registerRequest = new RegisterRequest(
                "testuser" + System.currentTimeMillis(),
                "password123",
                "test" + System.currentTimeMillis() + "@example.com"
        );
        
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.refreshToken").exists())
                .andExpect(jsonPath("$.username").value(registerRequest.getUsername()));
    }
    
    @Test
    void testRegisterUserWithDuplicateUsername() throws Exception {
        String username = "duplicateuser" + System.currentTimeMillis();
        RegisterRequest registerRequest = new RegisterRequest(
                username,
                "password123",
                "duplicate" + System.currentTimeMillis() + "@example.com"
        );
        
        // First registration should succeed
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated());
        
        // Second registration with same username should fail
        RegisterRequest duplicateRequest = new RegisterRequest(
                username,
                "password456",
                "another" + System.currentTimeMillis() + "@example.com"
        );
        
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(duplicateRequest)))
                .andExpect(status().is5xxServerError());
    }
    
    @Test
    // TODO: Investigate why login after registration fails in test - works in manual testing
    void testLoginUser_Disabled() throws Exception {
        // First register a user
        String username = "loginuser" + System.currentTimeMillis();
        String password = "password123";
        RegisterRequest registerRequest = new RegisterRequest(
                username,
                password,
                "login" + System.currentTimeMillis() + "@example.com"
        );
        
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated());
        
        // Then login
        LoginRequest loginRequest = new LoginRequest(username, password);
        
        mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.refreshToken").exists())
                .andExpect(jsonPath("$.username").value(username));
    }
    
    @Test
    void testLoginWithInvalidCredentials() throws Exception {
        LoginRequest loginRequest = new LoginRequest("nonexistent", "wrongpassword");
        
        mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().is5xxServerError());
    }
    
    @Test
    void testRefreshToken() throws Exception {
        // Register and get tokens
        RegisterRequest registerRequest = new RegisterRequest(
                "refreshuser" + System.currentTimeMillis(),
                "password123",
                "refresh" + System.currentTimeMillis() + "@example.com"
        );
        
        MvcResult result = mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated())
                .andReturn();
        
        AuthResponse authResponse = objectMapper.readValue(
                result.getResponse().getContentAsString(),
                AuthResponse.class
        );
        
        // Use refresh token to get new access token
        RefreshTokenRequest refreshRequest = new RefreshTokenRequest(authResponse.getRefreshToken());
        
        mockMvc.perform(post("/api/v1/auth/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(refreshRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.refreshToken").exists());
    }
    
    @Test
    void testLogout() throws Exception {
        // Register and get tokens
        RegisterRequest registerRequest = new RegisterRequest(
                "logoutuser" + System.currentTimeMillis(),
                "password123",
                "logout" + System.currentTimeMillis() + "@example.com"
        );
        
        MvcResult result = mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated())
                .andReturn();
        
        AuthResponse authResponse = objectMapper.readValue(
                result.getResponse().getContentAsString(),
                AuthResponse.class
        );
        
        // Logout
        mockMvc.perform(post("/api/v1/auth/logout")
                .header("Authorization", "Bearer " + authResponse.getAccessToken()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Logged out successfully"));
    }
    
    @Test
    void testAccessProtectedEndpointWithoutToken() throws Exception {
        mockMvc.perform(get("/api/v1/session/test-session"))
                .andExpect(status().isUnauthorized());
    }
    
    @Test
    void testAccessProtectedEndpointWithToken() throws Exception {
        // Register and get tokens
        RegisterRequest registerRequest = new RegisterRequest(
                "protecteduser" + System.currentTimeMillis(),
                "password123",
                "protected" + System.currentTimeMillis() + "@example.com"
        );
        
        MvcResult result = mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest)))
                .andExpect(status().isCreated())
                .andReturn();
        
        AuthResponse authResponse = objectMapper.readValue(
                result.getResponse().getContentAsString(),
                AuthResponse.class
        );
        
        // Access protected endpoint (should fail because session doesn't exist, but auth should succeed)
        mockMvc.perform(get("/api/v1/session/test-session")
                .header("Authorization", "Bearer " + authResponse.getAccessToken()))
                .andExpect(status().isNotFound());
    }
    
    @Test
    void testValidationOnRegister() throws Exception {
        // Test with invalid email
        RegisterRequest invalidRequest = new RegisterRequest(
                "test",
                "pass",
                "not-an-email"
        );
        
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(invalidRequest)))
                .andExpect(status().isBadRequest());
    }
}
