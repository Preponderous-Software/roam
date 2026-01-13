package com.preponderous.roam.service;

import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.World;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for player-to-player collision detection.
 * 
 * @author Daniel McCoy Stephenson
 */
@SpringBootTest
class PlayerCollisionTest {

    @Autowired
    private GameService gameService;

    @Autowired
    private PlayerService playerService;

    @Autowired
    private WorldGenerationService worldGenerationService;
    
    private String sessionId;
    private String player1Id;
    private String player2Id;
    private GameState gameState;
    
    @BeforeEach
    void setUp() {
        player1Id = "player1-" + System.currentTimeMillis();
        player2Id = "player2-" + System.currentTimeMillis();
        
        gameState = gameService.createSession(player1Id);
        sessionId = gameState.getSessionId();
        gameService.joinSession(sessionId, player2Id);
        
        gameState = gameService.getSession(sessionId, player1Id);
    }

    @Test
    void testPlayerCannotMoveToOccupiedTile() {
        Player p1 = gameState.getPlayer(player1Id);
        Player p2 = gameState.getPlayer(player2Id);
        
        // Position players next to each other
        playerService.setPlayerPosition(p1, 0, 0, 5, 5);
        playerService.setPlayerPosition(p2, 0, 0, 5, 6);
        
        // Try to move player1 down (into player2's position)
        playerService.setDirection(p1, 2); // 2 = down
        boolean moved = playerService.movePlayer(p1, gameState.getWorld(), 
            gameState.getCurrentTick(), gameState.getPlayers());
        
        assertFalse(moved);
        assertEquals(5, p1.getTileX());
        assertEquals(5, p1.getTileY()); // Should not have moved
    }

    @Test
    void testPlayerCanMoveToUnoccupiedTile() {
        Player p1 = gameState.getPlayer(player1Id);
        Player p2 = gameState.getPlayer(player2Id);
        
        // Position players with space between them (use center positions that are less likely to have entities)
        playerService.setPlayerPosition(p1, 0, 0, 10, 10);
        playerService.setPlayerPosition(p2, 0, 0, 15, 15);
        
        // First, verify p1 can move when there's no collision
        int initialX = p1.getTileX();
        int initialY = p1.getTileY();
        
        // Try moving in different directions until we find one that works
        // (some positions might have solid entities from world generation)
        boolean moved = false;
        for (int direction = 0; direction < 4 && !moved; direction++) {
            // Reset position for each try
            playerService.setPlayerPosition(p1, 0, 0, 10, 10);
            playerService.setDirection(p1, direction);
            moved = playerService.movePlayer(p1, gameState.getWorld(), 
                gameState.getCurrentTick(), gameState.getPlayers());
            
            if (moved) {
                // Verify that position changed
                assertTrue(p1.getTileX() != 10 || p1.getTileY() != 10);
                break;
            }
        }
        
        // At least one direction should have been available
        assertTrue(moved, "Player should be able to move in at least one direction");
    }

    @Test
    void testMultiplePlayersCanOccupyDifferentTiles() {
        Player p1 = gameState.getPlayer(player1Id);
        Player p2 = gameState.getPlayer(player2Id);
        
        // Position players at different locations
        playerService.setPlayerPosition(p1, 0, 0, 5, 5);
        playerService.setPlayerPosition(p2, 0, 0, 10, 10);
        
        assertEquals(5, p1.getTileX());
        assertEquals(5, p1.getTileY());
        assertEquals(10, p2.getTileX());
        assertEquals(10, p2.getTileY());
    }

    @Test
    void testPlayerCanMoveInDifferentDirections() {
        Player p1 = gameState.getPlayer(player1Id);
        Player p2 = gameState.getPlayer(player2Id);
        
        // Position player1 in center
        playerService.setPlayerPosition(p1, 0, 0, 5, 5);
        
        // Position player2 to the left
        playerService.setPlayerPosition(p2, 0, 0, 4, 5);
        
        // Try to move player1 left (blocked by player2)
        playerService.setDirection(p1, 1); // 1 = left
        boolean moved = playerService.movePlayer(p1, gameState.getWorld(), 
            gameState.getCurrentTick(), gameState.getPlayers());
        assertFalse(moved);
        
        // Try to move player1 right (should work)
        playerService.setDirection(p1, 3); // 3 = right
        moved = playerService.movePlayer(p1, gameState.getWorld(), 
            gameState.getCurrentTick(), gameState.getPlayers());
        assertTrue(moved);
        assertEquals(6, p1.getTileX());
        assertEquals(5, p1.getTileY());
    }

    @Test
    void testThreePlayersCollision() {
        String player3Id = "player3-" + System.currentTimeMillis();
        gameService.joinSession(sessionId, player3Id);
        gameState = gameService.getSession(sessionId, player1Id);
        
        Player p1 = gameState.getPlayer(player1Id);
        Player p2 = gameState.getPlayer(player2Id);
        Player p3 = gameState.getPlayer(player3Id);
        
        // Surround player1 with other players
        playerService.setPlayerPosition(p1, 0, 0, 5, 5);
        playerService.setPlayerPosition(p2, 0, 0, 5, 6); // below
        playerService.setPlayerPosition(p3, 0, 0, 6, 5); // right
        
        // Try to move player1 down (blocked by p2)
        playerService.setDirection(p1, 2); // 2 = down
        boolean moved = playerService.movePlayer(p1, gameState.getWorld(), 
            gameState.getCurrentTick(), gameState.getPlayers());
        assertFalse(moved);
        
        // Try to move player1 right (blocked by p3)
        playerService.setDirection(p1, 3); // 3 = right
        moved = playerService.movePlayer(p1, gameState.getWorld(), 
            gameState.getCurrentTick(), gameState.getPlayers());
        assertFalse(moved);
        
        // Try to move player1 up (should work)
        playerService.setDirection(p1, 0); // 0 = up
        moved = playerService.movePlayer(p1, gameState.getWorld(), 
            gameState.getCurrentTick(), gameState.getPlayers());
        assertTrue(moved);
        assertEquals(5, p1.getTileX());
        assertEquals(4, p1.getTileY());
    }

    @Test
    void testPlayerCollisionAcrossRooms() {
        Player p1 = gameState.getPlayer(player1Id);
        Player p2 = gameState.getPlayer(player2Id);
        
        // Position players in different rooms
        playerService.setPlayerPosition(p1, 0, 0, 5, 5);
        playerService.setPlayerPosition(p2, 1, 0, 3, 3);
        
        // Players in different rooms should not collide
        // Move player1 right (should work)
        playerService.setDirection(p1, 3); // 3 = right
        boolean moved = playerService.movePlayer(p1, gameState.getWorld(), 
            gameState.getCurrentTick(), gameState.getPlayers());
        assertTrue(moved);
    }
}
