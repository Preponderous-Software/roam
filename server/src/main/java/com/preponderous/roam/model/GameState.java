package com.preponderous.roam.model;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Represents the game state for a single session with support for multiple players.
 * 
 * @author Daniel McCoy Stephenson
 */
public class GameState {
    public static final int MAX_PLAYERS_PER_SESSION = 10; // Maximum players allowed per session
    
    private final String sessionId;
    private final String ownerId;  // Username of the session owner
    private final Map<String, Player> players; // Map of userId -> Player
    private final World world;
    private long currentTick;

    public GameState(String sessionId, String ownerId, long initialTick, World world) {
        this.sessionId = sessionId;
        this.ownerId = ownerId;
        this.players = new ConcurrentHashMap<>();
        this.world = world;
        this.currentTick = initialTick;
        
        // Create the owner's player
        Player ownerPlayer = new Player(ownerId, initialTick);
        this.players.put(ownerId, ownerPlayer);
    }

    public String getSessionId() {
        return sessionId;
    }

    public String getOwnerId() {
        return ownerId;
    }
    
    /**
     * @deprecated Use getOwnerId() instead. This method is kept for backward compatibility.
     */
    @Deprecated
    public String getUserId() {
        return ownerId;
    }

    /**
     * Get the session owner's player.
     * @deprecated Use getPlayer(ownerId) instead. This method is kept for backward compatibility.
     */
    @Deprecated
    public Player getPlayer() {
        return players.get(ownerId);
    }
    
    /**
     * Get a specific player by userId.
     */
    public Player getPlayer(String userId) {
        return players.get(userId);
    }
    
    /**
     * Get all players in the session.
     * Returns an unmodifiable view to protect internal state.
     */
    public Map<String, Player> getPlayers() {
        return java.util.Collections.unmodifiableMap(players);
    }
    
    /**
     * Add a player to the session.
     * @param userId the userId of the player to add
     * @param currentTick the current game tick
     * @return true if player was added successfully, false if session is full
     * Note: Returns true if player already exists (idempotent operation)
     */
    public boolean addPlayer(String userId, long currentTick) {
        if (players.size() >= MAX_PLAYERS_PER_SESSION) {
            return false;
        }
        if (players.containsKey(userId)) {
            return true; // Player already in session - operation is idempotent
        }
        Player player = new Player(userId, currentTick);
        players.put(userId, player);
        return true;
    }
    
    /**
     * Remove a player from the session.
     * @return true if player was removed, false if player didn't exist or is the owner
     */
    public boolean removePlayer(String userId) {
        if (userId.equals(ownerId)) {
            return false; // Cannot remove owner
        }
        return players.remove(userId) != null;
    }
    
    /**
     * Check if a player is in the session.
     */
    public boolean hasPlayer(String userId) {
        return players.containsKey(userId);
    }
    
    /**
     * Get the number of players in the session.
     */
    public int getPlayerCount() {
        return players.size();
    }
    
    /**
     * Check if the session is full.
     */
    public boolean isFull() {
        return players.size() >= MAX_PLAYERS_PER_SESSION;
    }

    public World getWorld() {
        return world;
    }

    public long getCurrentTick() {
        return currentTick;
    }

    public void setCurrentTick(long currentTick) {
        this.currentTick = currentTick;
    }

    public void incrementTick() {
        this.currentTick++;
    }
}
