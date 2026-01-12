package com.preponderous.roam.service;

import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.World;
import com.preponderous.roam.model.WorldConfig;
import com.preponderous.roam.persistence.service.GameStateStorage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Service for managing game sessions and state.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class GameService {
    private static final Logger logger = LoggerFactory.getLogger(GameService.class);
    
    private final Map<String, GameState> sessions = new ConcurrentHashMap<>();
    
    @Autowired
    private WorldGenerationService worldGenerationService;
    
    @Autowired
    private PlayerService playerService;
    
    @Autowired
    private EntityManager entityManager;
    
    @Autowired
    private GameStateStorage gameStateStorage;
    
    @Value("${roam.persistence.auto-save:false}")
    private boolean autoSaveEnabled;

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
     * Attempts to load from memory first, then from database if not in memory.
     */
    public GameState getSession(String sessionId) {
        GameState gameState = sessions.get(sessionId);
        if (gameState == null) {
            // Try to load from database
            Optional<GameState> loadedState = gameStateStorage.loadGameState(sessionId);
            if (loadedState.isPresent()) {
                gameState = loadedState.get();
                sessions.put(sessionId, gameState);
                logger.info("Loaded session from database: {}", sessionId);
            }
        }
        return gameState;
    }

    /**
     * Delete a game session from memory and database.
     */
    public void deleteSession(String sessionId) {
        sessions.remove(sessionId);
        gameStateStorage.deleteGameState(sessionId);
        logger.info("Deleted session: {}", sessionId);
    }

    /**
     * Check if a session exists in memory or database.
     */
    public boolean sessionExists(String sessionId) {
        return sessions.containsKey(sessionId) || gameStateStorage.sessionExists(sessionId);
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
            
            // Auto-save if enabled (every 100 ticks to avoid too frequent saves)
            if (autoSaveEnabled && gameState.getCurrentTick() % 100 == 0) {
                saveSession(sessionId);
            }
        }
    }
    
    /**
     * Manually save a game session to the database.
     */
    public void saveSession(String sessionId) {
        GameState gameState = getSession(sessionId);  // Use getSession to ensure auto-load behavior
        if (gameState != null) {
            gameStateStorage.saveGameState(gameState);
            logger.info("Saved session: {}", sessionId);
        }
    }
    
    /**
     * Load a game session from the database into memory.
     */
    public GameState loadSession(String sessionId) {
        Optional<GameState> loadedState = gameStateStorage.loadGameState(sessionId);
        if (loadedState.isPresent()) {
            GameState gameState = loadedState.get();
            sessions.put(sessionId, gameState);
            logger.info("Loaded session into memory: {}", sessionId);
            return gameState;
        }
        return null;
    }

    /**
     * Get current tick for a session.
     */
    public long getCurrentTick(String sessionId) {
        GameState gameState = getSession(sessionId);
        return gameState != null ? gameState.getCurrentTick() : 0;
    }
}
