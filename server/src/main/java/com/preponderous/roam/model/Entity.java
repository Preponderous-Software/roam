package com.preponderous.roam.model;

import java.util.UUID;

/**
 * Base class for all entities in the game world.
 * 
 * @author Daniel McCoy Stephenson
 */
public abstract class Entity {
    private final String id;
    private final String name;
    private String imagePath;
    private String locationId;
    private boolean solid;

    public Entity(String name, String imagePath) {
        this.id = UUID.randomUUID().toString();
        this.name = name;
        this.imagePath = imagePath;
        this.locationId = null;
        this.solid = false;
    }

    public String getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getImagePath() {
        return imagePath;
    }

    public void setImagePath(String imagePath) {
        this.imagePath = imagePath;
    }

    public String getLocationId() {
        return locationId;
    }

    public void setLocationId(String locationId) {
        this.locationId = locationId;
    }

    public boolean isSolid() {
        return solid;
    }

    public void setSolid(boolean solid) {
        this.solid = solid;
    }
}
