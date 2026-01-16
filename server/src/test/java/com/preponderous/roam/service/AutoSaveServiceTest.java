package com.preponderous.roam.service;

import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.WorldConfig;
import com.preponderous.roam.persistence.service.PersistenceService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for AutoSaveService.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest
@ActiveProfiles("test")
class AutoSaveServiceTest {
    
    @Autowired
    private AutoSaveService autoSaveService;
    
    @MockBean
    private GameService gameService;
    
    @MockBean
    private PersistenceService persistenceService;
    
    @BeforeEach
    void setUp() {
        // Reset mocks before each test
        reset(gameService, persistenceService);
    }
    
    @Test
    void testAutoSaveAllSessions_WhenNoActiveSessions() {
        // Given: No active sessions
        when(gameService.getActiveSessions()).thenReturn(new ConcurrentHashMap<>());
        
        // When: Auto-save is triggered
        autoSaveService.autoSaveAllSessions();
        
        // Then: Persistence service should not be called
        verify(persistenceService, never()).saveGameState(any());
    }
    
    @Test
    void testAutoSaveAllSessions_WithMultipleSessions() {
        // Given: Multiple active sessions
        Map<String, GameState> sessions = new ConcurrentHashMap<>();
        
        WorldConfig worldConfig = WorldConfig.getDefault();
        World world1 = new World(worldConfig);
        World world2 = new World(worldConfig);
        
        GameState session1 = new GameState("session-1", "user1", 100L, world1);
        GameState session2 = new GameState("session-2", "user2", 200L, world2);
        
        sessions.put("session-1", session1);
        sessions.put("session-2", session2);
        
        when(gameService.getActiveSessions()).thenReturn(sessions);
        
        // When: Auto-save is triggered (note: auto-save is disabled by default in test profile)
        // We'll call saveAllSessionsNow() instead which doesn't check the flag
        int savedCount = autoSaveService.saveAllSessionsNow();
        
        // Then: Both sessions should be saved
        verify(persistenceService, times(2)).saveGameState(any(GameState.class));
        assertEquals(2, savedCount);
    }
    
    @Test
    void testAutoSaveAllSessions_HandlesFailures() {
        // Given: Active session that will fail to save
        Map<String, GameState> sessions = new ConcurrentHashMap<>();
        
        WorldConfig worldConfig = WorldConfig.getDefault();
        World world = new World(worldConfig);
        GameState session = new GameState("session-1", "user1", 100L, world);
        
        sessions.put("session-1", session);
        
        when(gameService.getActiveSessions()).thenReturn(sessions);
        
        // Simulate save failure
        doThrow(new RuntimeException("Database connection failed"))
            .when(persistenceService).saveGameState(any(GameState.class));
        
        // When: Auto-save is triggered
        int savedCount = autoSaveService.saveAllSessionsNow();
        
        // Then: Save should be attempted but fail gracefully
        verify(persistenceService, atLeastOnce()).saveGameState(any(GameState.class));
        assertEquals(0, savedCount, "Failed saves should not be counted");
    }
    
    @Test
    void testSaveAllSessionsNow_ReturnsSavedCount() {
        // Given: Three active sessions
        Map<String, GameState> sessions = new ConcurrentHashMap<>();
        
        WorldConfig worldConfig = WorldConfig.getDefault();
        
        for (int i = 1; i <= 3; i++) {
            World world = new World(worldConfig);
            GameState session = new GameState("session-" + i, "user" + i, i * 100L, world);
            sessions.put("session-" + i, session);
        }
        
        when(gameService.getActiveSessions()).thenReturn(sessions);
        
        // When: Save all sessions
        int savedCount = autoSaveService.saveAllSessionsNow();
        
        // Then: All sessions should be saved
        verify(persistenceService, times(3)).saveGameState(any(GameState.class));
        assertEquals(3, savedCount);
    }
    
    @Test
    void testSaveAllSessionsNow_CapturesSessionIds() {
        // Given: Active sessions with specific IDs
        Map<String, GameState> sessions = new ConcurrentHashMap<>();
        
        WorldConfig worldConfig = WorldConfig.getDefault();
        World world1 = new World(worldConfig);
        World world2 = new World(worldConfig);
        
        GameState session1 = new GameState("test-session-alpha", "user1", 100L, world1);
        GameState session2 = new GameState("test-session-beta", "user2", 200L, world2);
        
        sessions.put("test-session-alpha", session1);
        sessions.put("test-session-beta", session2);
        
        when(gameService.getActiveSessions()).thenReturn(sessions);
        
        // When: Save all sessions
        ArgumentCaptor<GameState> captor = ArgumentCaptor.forClass(GameState.class);
        int savedCount = autoSaveService.saveAllSessionsNow();
        
        // Then: Capture and verify session IDs
        verify(persistenceService, times(2)).saveGameState(captor.capture());
        
        var capturedSessions = captor.getAllValues();
        assertEquals(2, capturedSessions.size());
        
        boolean hasAlpha = capturedSessions.stream()
            .anyMatch(s -> s.getSessionId().equals("test-session-alpha"));
        boolean hasBeta = capturedSessions.stream()
            .anyMatch(s -> s.getSessionId().equals("test-session-beta"));
        
        assertTrue(hasAlpha, "Should save session alpha");
        assertTrue(hasBeta, "Should save session beta");
        assertEquals(2, savedCount);
    }
}
