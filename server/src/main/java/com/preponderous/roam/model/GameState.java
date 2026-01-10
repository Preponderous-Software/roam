package com.preponderous.roam.model;

/**
 * Represents the game state for a single session.
 * 
 * @author Daniel McCoy Stephenson
 */
public class GameState {
    private final String sessionId;
    private final Player player;
    private long currentTick;

    public GameState(String sessionId, long initialTick) {
        this.sessionId = sessionId;
        this.player = new Player(initialTick);
        this.currentTick = initialTick;
    }

    public String getSessionId() {
        return sessionId;
    }

    public Player getPlayer() {
        return player;
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
