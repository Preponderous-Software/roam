package com.preponderous.roam.dto.websocket;

import com.preponderous.roam.dto.EntityDTO;

/**
 * WebSocket message for entity state changes.
 * 
 * @author Daniel McCoy Stephenson
 */
public class EntityStateUpdate extends WebSocketMessage {
    private EntityDTO entity;
    private String action; // "added", "removed", "updated"

    public EntityStateUpdate() {
        super();
    }

    public EntityDTO getEntity() {
        return entity;
    }

    public void setEntity(EntityDTO entity) {
        this.entity = entity;
    }

    public String getAction() {
        return action;
    }

    public void setAction(String action) {
        this.action = action;
    }
}
