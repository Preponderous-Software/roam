package com.preponderous.roam.service;

import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.WorldConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for multiplayer functionality in GameService.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest
class MultiplayerGameServiceTest {

    @Autowired
    private GameService gameService;

    @Autowired
    private WorldGenerationService worldGenerationService;
    
    private String sessionId;
    private String ownerUserId;
    
    @BeforeEach
    void setUp() {
        ownerUserId = "owner-" + System.currentTimeMillis();
        GameState gameState = gameService.createSession(ownerUserId);
        sessionId = gameState.getSessionId();
    }

    @Test
    void testCreateSession_CreatesOwnerPlayer() {
        GameState gameState = gameService.getSession(sessionId, ownerUserId);
        
        assertNotNull(gameState);
        assertEquals(ownerUserId, gameState.getOwnerId());
        assertEquals(1, gameState.getPlayerCount());
        assertTrue(gameState.hasPlayer(ownerUserId));
        
        Player ownerPlayer = gameState.getPlayer(ownerUserId);
        assertNotNull(ownerPlayer);
        assertEquals(ownerUserId, ownerPlayer.getUserId());
    }

    @Test
    void testJoinSession_AddsNewPlayer() {
        String newUserId = "player-" + System.currentTimeMillis();
        
        boolean joined = gameService.joinSession(sessionId, newUserId);
        
        assertTrue(joined);
        
        GameState gameState = gameService.getSession(sessionId, ownerUserId);
        assertEquals(2, gameState.getPlayerCount());
        assertTrue(gameState.hasPlayer(newUserId));
        
        Player newPlayer = gameState.getPlayer(newUserId);
        assertNotNull(newPlayer);
        assertEquals(newUserId, newPlayer.getUserId());
    }

    @Test
    void testJoinSession_PlayerAlreadyExists() {
        String userId = "player-" + System.currentTimeMillis();
        
        gameService.joinSession(sessionId, userId);
        boolean joinedAgain = gameService.joinSession(sessionId, userId);
        
        assertTrue(joinedAgain);
        
        GameState gameState = gameService.getSession(sessionId, ownerUserId);
        assertEquals(2, gameState.getPlayerCount()); // Still only 2 players
    }

    @Test
    void testJoinSession_SessionFull() {
        // Fill the session to capacity
        for (int i = 0; i < GameState.MAX_PLAYERS_PER_SESSION - 1; i++) {
            gameService.joinSession(sessionId, "player-" + i);
        }
        
        GameState gameState = gameService.getSession(sessionId, ownerUserId);
        assertTrue(gameState.isFull());
        
        // Try to add one more player
        boolean joined = gameService.joinSession(sessionId, "extra-player");
        
        assertFalse(joined);
        assertEquals(GameState.MAX_PLAYERS_PER_SESSION, gameState.getPlayerCount());
    }

    @Test
    void testLeaveSession_RemovesPlayer() {
        String userId = "player-" + System.currentTimeMillis();
        gameService.joinSession(sessionId, userId);
        
        boolean left = gameService.leaveSession(sessionId, userId);
        
        assertTrue(left);
        
        GameState gameState = gameService.getSession(sessionId, ownerUserId);
        assertEquals(1, gameState.getPlayerCount());
        assertFalse(gameState.hasPlayer(userId));
    }

    @Test
    void testLeaveSession_OwnerCannotLeave() {
        boolean left = gameService.leaveSession(sessionId, ownerUserId);
        
        assertFalse(left);
        
        GameState gameState = gameService.getSession(sessionId, ownerUserId);
        assertEquals(1, gameState.getPlayerCount());
        assertTrue(gameState.hasPlayer(ownerUserId));
    }

    @Test
    void testGetSession_OnlyPlayersInSessionCanAccess() {
        String nonParticipant = "non-participant-" + System.currentTimeMillis();
        
        GameState gameState = gameService.getSession(sessionId, nonParticipant);
        
        assertNull(gameState);
    }

    @Test
    void testGetSession_ParticipantCanAccess() {
        String userId = "player-" + System.currentTimeMillis();
        gameService.joinSession(sessionId, userId);
        
        GameState gameState = gameService.getSession(sessionId, userId);
        
        assertNotNull(gameState);
        assertEquals(sessionId, gameState.getSessionId());
    }

    @Test
    void testMultiplePlayersInitializedAtStartingPosition() {
        String player1 = "player1-" + System.currentTimeMillis();
        String player2 = "player2-" + System.currentTimeMillis();
        
        gameService.joinSession(sessionId, player1);
        gameService.joinSession(sessionId, player2);
        
        GameState gameState = gameService.getSession(sessionId, ownerUserId);
        
        Player p1 = gameState.getPlayer(player1);
        Player p2 = gameState.getPlayer(player2);
        
        // Both players should be initialized at room (0,0)
        assertEquals(0, p1.getRoomX());
        assertEquals(0, p1.getRoomY());
        assertEquals(0, p2.getRoomX());
        assertEquals(0, p2.getRoomY());
        
        // They should have valid tile coordinates
        assertTrue(p1.getTileX() >= 0);
        assertTrue(p1.getTileY() >= 0);
        assertTrue(p2.getTileX() >= 0);
        assertTrue(p2.getTileY() >= 0);
    }

    @Test
    void testSessionMetadata() {
        GameState gameState = gameService.getSession(sessionId, ownerUserId);
        
        assertFalse(gameState.isFull());
        assertEquals(1, gameState.getPlayerCount());
        assertEquals(10, GameState.MAX_PLAYERS_PER_SESSION);  // Verify the constant value
        
        // Add players until almost full
        for (int i = 0; i < GameState.MAX_PLAYERS_PER_SESSION - 2; i++) {
            gameService.joinSession(sessionId, "player-" + i);
        }
        
        gameState = gameService.getSession(sessionId, ownerUserId);
        assertFalse(gameState.isFull());
        assertEquals(GameState.MAX_PLAYERS_PER_SESSION - 1, gameState.getPlayerCount());
        
        // Add one more to fill it
        gameService.joinSession(sessionId, "final-player");
        
        gameState = gameService.getSession(sessionId, ownerUserId);
        assertTrue(gameState.isFull());
        assertEquals(GameState.MAX_PLAYERS_PER_SESSION, gameState.getPlayerCount());
    }
}
