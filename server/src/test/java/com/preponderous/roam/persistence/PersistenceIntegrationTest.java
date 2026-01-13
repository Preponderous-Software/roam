package com.preponderous.roam.persistence;

import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.WorldConfig;
import com.preponderous.roam.persistence.service.PersistenceService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests for persistence layer.
 * Uses H2 in-memory database for testing.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest
@ActiveProfiles("test")
public class PersistenceIntegrationTest {
    
    @Autowired
    private PersistenceService persistenceService;
    
    @Test
    public void testSaveAndLoadGameState() {
        // Given: Create a game state
        String sessionId = "test-session-123";
        WorldConfig worldConfig = new WorldConfig(12345L, 20, 20, 0.1, 0.0);
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, "testuser", 0L, world);
        
        // Modify player state
        Player player = gameState.getPlayer();
        player.setEnergy(75.0);
        player.setRoomX(1);
        player.setRoomY(2);
        player.setTileX(5);
        player.setTileY(7);
        
        // Advance game tick
        gameState.setCurrentTick(150);
        
        // When: Save the game state
        persistenceService.saveGameState(gameState);
        
        // Then: Load the game state and verify
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        assertTrue(loadedState.isPresent(), "Game state should be loaded");
        
        GameState loaded = loadedState.get();
        assertEquals(sessionId, loaded.getSessionId());
        assertEquals(150, loaded.getCurrentTick());
        
        // Verify player state
        Player loadedPlayer = loaded.getPlayer();
        assertEquals(75.0, loadedPlayer.getEnergy(), 0.01);
        assertEquals(1, loadedPlayer.getRoomX());
        assertEquals(2, loadedPlayer.getRoomY());
        assertEquals(5, loadedPlayer.getTileX());
        assertEquals(7, loadedPlayer.getTileY());
        
        // Verify world config
        WorldConfig loadedConfig = loaded.getWorld().getConfig();
        assertEquals(12345L, loadedConfig.getSeed());
        assertEquals(20, loadedConfig.getRoomWidth());
        assertEquals(20, loadedConfig.getRoomHeight());
    }
    
    @Test
    public void testUpdateExistingGameState() {
        // Given: Create and save a game state
        String sessionId = "test-session-456";
        WorldConfig worldConfig = WorldConfig.getDefault();
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, "testuser", 0L, world);
        persistenceService.saveGameState(gameState);
        
        // When: Modify and save again
        gameState.setCurrentTick(250);
        gameState.getPlayer().setEnergy(50.0);
        persistenceService.saveGameState(gameState);
        
        // Then: Load and verify the updates
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        assertTrue(loadedState.isPresent());
        assertEquals(250, loadedState.get().getCurrentTick());
        assertEquals(50.0, loadedState.get().getPlayer().getEnergy(), 0.01);
    }
    
    @Test
    public void testDeleteGameState() {
        // Given: Create and save a game state
        String sessionId = "test-session-789";
        WorldConfig worldConfig = WorldConfig.getDefault();
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, "testuser", 0L, world);
        persistenceService.saveGameState(gameState);
        
        // Verify it exists
        assertTrue(persistenceService.sessionExists(sessionId));
        
        // When: Delete the game state
        persistenceService.deleteGameState(sessionId);
        
        // Then: Verify it's deleted
        assertFalse(persistenceService.sessionExists(sessionId));
        Optional<GameState> loadedState = persistenceService.loadGameState(sessionId);
        assertFalse(loadedState.isPresent());
    }
    
    @Test
    public void testSessionExists() {
        // Given: A non-existent session
        String sessionId = "non-existent-session";
        
        // Then: Should not exist
        assertFalse(persistenceService.sessionExists(sessionId));
        
        // When: Save a session
        WorldConfig worldConfig = WorldConfig.getDefault();
        World world = new World(worldConfig);
        GameState gameState = new GameState(sessionId, "testuser", 0L, world);
        persistenceService.saveGameState(gameState);
        
        // Then: Should exist
        assertTrue(persistenceService.sessionExists(sessionId));
    }
}
