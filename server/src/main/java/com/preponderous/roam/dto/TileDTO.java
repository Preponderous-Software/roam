package com.preponderous.roam.dto;

/**
 * DTO for tile data transfer.
 * 
 * @author Daniel McCoy Stephenson
 */
public class TileDTO {
    private int x;
    private int y;
    private String biome;
    private String biomeColor;
    private String resourceType;
    private int resourceAmount;
    private boolean hasHazard;
    private String hazardType;

    public TileDTO() {
    }

    public int getX() {
        return x;
    }

    public void setX(int x) {
        this.x = x;
    }

    public int getY() {
        return y;
    }

    public void setY(int y) {
        this.y = y;
    }

    public String getBiome() {
        return biome;
    }

    public void setBiome(String biome) {
        this.biome = biome;
    }

    public String getBiomeColor() {
        return biomeColor;
    }

    public void setBiomeColor(String biomeColor) {
        this.biomeColor = biomeColor;
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

    public boolean isHasHazard() {
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
