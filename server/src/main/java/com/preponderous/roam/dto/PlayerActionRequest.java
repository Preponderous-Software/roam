package com.preponderous.roam.dto;

/**
 * DTO for player action requests.
 * 
 * @author Daniel McCoy Stephenson
 */
public class PlayerActionRequest {
    private String action;
    private Integer direction;
    private String itemName;
    private Boolean gathering;
    private Boolean placing;
    private Boolean crouching;
    private Boolean running;
    private Integer tileX;  // Target tile X coordinate for interactions
    private Integer tileY;  // Target tile Y coordinate for interactions

    public PlayerActionRequest() {
    }

    public String getAction() {
        return action;
    }

    public void setAction(String action) {
        this.action = action;
    }

    public Integer getDirection() {
        return direction;
    }

    public void setDirection(Integer direction) {
        this.direction = direction;
    }

    public String getItemName() {
        return itemName;
    }

    public void setItemName(String itemName) {
        this.itemName = itemName;
    }

    public Boolean getGathering() {
        return gathering;
    }

    public void setGathering(Boolean gathering) {
        this.gathering = gathering;
    }

    public Boolean getPlacing() {
        return placing;
    }

    public void setPlacing(Boolean placing) {
        this.placing = placing;
    }

    public Boolean getCrouching() {
        return crouching;
    }

    public void setCrouching(Boolean crouching) {
        this.crouching = crouching;
    }

    public Boolean getRunning() {
        return running;
    }

    public void setRunning(Boolean running) {
        this.running = running;
    }

    public Integer getTileX() {
        return tileX;
    }

    public void setTileX(Integer tileX) {
        this.tileX = tileX;
    }

    public Integer getTileY() {
        return tileY;
    }

    public void setTileY(Integer tileY) {
        this.tileY = tileY;
    }
}
