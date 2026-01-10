package com.preponderous.roam.dto;

/**
 * DTO for game session initialization requests.
 * 
 * @author Daniel McCoy Stephenson
 */
public class InitSessionRequest {
    private String playerName;

    public InitSessionRequest() {
    }

    public String getPlayerName() {
        return playerName;
    }

    public void setPlayerName(String playerName) {
        this.playerName = playerName;
    }
}
