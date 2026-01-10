package com.preponderous.roam.dto;

/**
 * DTO for session initialization response.
 * 
 * @author Daniel McCoy Stephenson
 */
public class SessionDTO {
    private String sessionId;
    private long currentTick;
    private PlayerDTO player;

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

    public PlayerDTO getPlayer() {
        return player;
    }

    public void setPlayer(PlayerDTO player) {
        this.player = player;
    }
}
