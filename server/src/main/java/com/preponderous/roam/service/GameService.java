package com.preponderous.roam.service;

import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Player;
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

    /**
     * Create a new game session.
     */
    public GameState createSession() {
        String sessionId = UUID.randomUUID().toString();
        long initialTick = 0;
        GameState gameState = new GameState(sessionId, initialTick);
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
