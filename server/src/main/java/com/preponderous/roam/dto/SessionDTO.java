package com.preponderous.roam.dto;

import java.util.Map;

/**
 * DTO for session initialization response.
 * 
 * @author Daniel McCoy Stephenson
 */
public class SessionDTO {
    private String sessionId;
    private String ownerId;  // Username of the session owner
    private long currentTick;
    private PlayerDTO player;  // Deprecated: use players map instead
    private java.util.Map<String, PlayerDTO> players;  // Map of userId -> PlayerDTO
    private int playerCount;
    private int maxPlayers;
    private boolean full;

    public SessionDTO() {
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public long getCurrentTick() {
        return currentTick;
    }

    public void setCurrentTick(long currentTick) {
        this.currentTick = currentTick;
    }

    /**
     * @deprecated Use getPlayers() instead. This method is kept for backward compatibility.
     */
    @Deprecated
    public PlayerDTO getPlayer() {
        return player;
    }

    public void setPlayer(PlayerDTO player) {
        this.player = player;
    }
    
    public Map<String, PlayerDTO> getPlayers() {
        return players;
    }
    
    public void setPlayers(Map<String, PlayerDTO> players) {
        this.players = players;
    }
    
    public String getOwnerId() {
        return ownerId;
    }
    
    public void setOwnerId(String ownerId) {
        this.ownerId = ownerId;
    }
    
    public int getPlayerCount() {
        return playerCount;
    }
    
    public void setPlayerCount(int playerCount) {
        this.playerCount = playerCount;
    }
    
    public int getMaxPlayers() {
        return maxPlayers;
    }
    
    public void setMaxPlayers(int maxPlayers) {
        this.maxPlayers = maxPlayers;
    }
    
    public boolean isFull() {
        return full;
    }
    
    public void setFull(boolean full) {
        this.full = full;
    }
}