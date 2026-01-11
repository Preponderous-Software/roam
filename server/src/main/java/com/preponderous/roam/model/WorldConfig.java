package com.preponderous.roam.model;

/**
 * Configuration parameters for world generation.
 * 
 * @author Daniel McCoy Stephenson
 */
public class WorldConfig {
    private final long seed;
    private final int roomWidth;
    private final int roomHeight;
    private final double resourceDensity;
    private final double hazardDensity;

    public WorldConfig(long seed, int roomWidth, int roomHeight, double resourceDensity, double hazardDensity) {
        this.seed = seed;
        this.roomWidth = roomWidth;
        this.roomHeight = roomHeight;
        this.resourceDensity = resourceDensity;
        this.hazardDensity = hazardDensity;
    }

    /**
     * Creates a default WorldConfig with standard settings.
     * 
     * Note: Uses System.currentTimeMillis() as the seed, which means every session will generate
     * a different, non-reproducible world. This provides variety but makes debugging difficult.
     * For reproducible world generation (testing, debugging, or world sharing), use the constructor
     * with a fixed seed value instead.
     * 
     * @return a WorldConfig with default values and a time-based random seed
     */
    public static WorldConfig getDefault() {
        return new WorldConfig(
            System.currentTimeMillis(),
            32,  // Default room width
            32,  // Default room height
            0.1, // 10% resource density
            0.05 // 5% hazard density
        );
    }

    public long getSeed() {
        return seed;
    }

    public int getRoomWidth() {
        return roomWidth;
    }

    public int getRoomHeight() {
        return roomHeight;
    }

    public double getResourceDensity() {
        return resourceDensity;
    }

    public double getHazardDensity() {
        return hazardDensity;
    }
}
