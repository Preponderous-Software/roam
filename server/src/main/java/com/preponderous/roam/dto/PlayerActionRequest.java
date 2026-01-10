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
}
