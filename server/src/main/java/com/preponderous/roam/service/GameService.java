package com.preponderous.roam.service;

import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.WorldConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Service for managing game sessions and state.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class GameService {
    private final Map<String, GameState> sessions = new ConcurrentHashMap<>();
    
    @Autowired
    private WorldGenerationService worldGenerationService;
    
    @Autowired
    private PlayerService playerService;
    
    @Autowired
    private EntityManager entityManager;

    /**
     * Create a new game session.
     */
    public GameState createSession() {
        String sessionId = UUID.randomUUID().toString();
        long initialTick = 0;
        
        // Generate a new world for the session
        WorldConfig worldConfig = WorldConfig.getDefault();
        World world = new World(worldConfig);
        
        // Generate the starting room (0, 0)
        Room startingRoom = worldGenerationService.getOrGenerateRoom(world, 0, 0, initialTick);
        
        GameState gameState = new GameState(sessionId, initialTick, world);
        
        // Initialize player at center of starting room
        Player player = gameState.getPlayer();
        int centerX = startingRoom.getWidth() / 2;
        int centerY = startingRoom.getHeight() / 2;
        playerService.setPlayerPosition(player, 0, 0, centerX, centerY);
        
        sessions.put(sessionId, gameState);
        return gameState;
    }

    /**
     * Get an existing game session.
     */
    public GameState getSession(String sessionId) {
        return sessions.get(sessionId);
    }

    /**
     * Delete a game session.
     */
    public void deleteSession(String sessionId) {
        sessions.remove(sessionId);
    }

    /**
     * Check if a session exists.
     */
    public boolean sessionExists(String sessionId) {
        return sessions.containsKey(sessionId);
    }

    /**
     * Get the player from a session.
     */
    public Player getPlayer(String sessionId) {
        GameState gameState = getSession(sessionId);
        return gameState != null ? gameState.getPlayer() : null;
    }

    /**
     * Update game tick.
     */
    public void updateTick(String sessionId) {
        GameState gameState = getSession(sessionId);
        if (gameState != null) {
            gameState.incrementTick();
            
            // Update player movement
            Player player = gameState.getPlayer();
            if (player.isMoving()) {
                playerService.movePlayer(player, gameState.getWorld(), gameState.getCurrentTick());
            }
            
            // Update entities in all loaded rooms
            World world = gameState.getWorld();
            for (Room room : world.getRooms().values()) {
                entityManager.updateEntities(room, gameState.getCurrentTick());
            }
        }
    }

    /**
     * Get current tick for a session.
     */
    public long getCurrentTick(String sessionId) {
        GameState gameState = getSession(sessionId);
        return gameState != null ? gameState.getCurrentTick() : 0;
    }
}
