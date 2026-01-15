package com.preponderous.roam.dto.websocket;

import com.preponderous.roam.dto.EntityDTO;

/**
 * WebSocket message for entity state changes.
 * 
 * @author Daniel McCoy Stephenson
 */
public class EntityStateUpdate extends WebSocketMessage {
    private EntityDTO entity;
    private EntityAction action;

    public EntityStateUpdate() {
        super();
    }

    public EntityDTO getEntity() {
        return entity;
    }

    public void setEntity(EntityDTO entity) {
        this.entity = entity;
    }

    public EntityAction getAction() {
        return action;
    }

    public void setAction(EntityAction action) {
        this.action = action;
    }
}
