package com.preponderous.roam.model;

/**
 * Represents the game state for a single session.
 * 
 * @author Daniel McCoy Stephenson
 */
public class GameState {
    private final String sessionId;
    private final Player player;
    private final World world;
    private long currentTick;

    public GameState(String sessionId, long initialTick, World world) {
        this.sessionId = sessionId;
        this.player = new Player(initialTick);
        this.world = world;
        this.currentTick = initialTick;
    }

    public String getSessionId() {
        return sessionId;
    }

    public Player getPlayer() {
        return player;
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
