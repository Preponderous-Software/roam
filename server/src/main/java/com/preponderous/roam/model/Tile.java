package com.preponderous.roam.model;

/**
 * Represents a single tile in the game world.
 * Each tile has a biome type and may contain resources or hazards.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Tile {
    private final int x;
    private final int y;
    private Biome biome;
    private String resourceType;
    private int resourceAmount;
    private boolean hasHazard;
    private String hazardType;

    public Tile(int x, int y, Biome biome) {
        this.x = x;
        this.y = y;
        this.biome = biome;
        this.resourceType = null;
        this.resourceAmount = 0;
        this.hasHazard = false;
        this.hazardType = null;
    }

    public int getX() {
        return x;
    }

    public int getY() {
        return y;
    }

    public Biome getBiome() {
        return biome;
    }

    public void setBiome(Biome biome) {
        this.biome = biome;
    }

    public String getResourceType() {
        return resourceType;
    }

    public void setResourceType(String resourceType) {
        this.resourceType = resourceType;
    }

    public int getResourceAmount() {
        return resourceAmount;
    }

    public void setResourceAmount(int resourceAmount) {
        this.resourceAmount = resourceAmount;
    }

    public boolean hasResource() {
        return resourceType != null && resourceAmount > 0;
    }

    public boolean hasHazard() {
        return hasHazard;
    }

    public void setHasHazard(boolean hasHazard) {
        this.hasHazard = hasHazard;
    }

    public String getHazardType() {
        return hazardType;
    }

    public void setHazardType(String hazardType) {
        this.hazardType = hazardType;
    }
}
