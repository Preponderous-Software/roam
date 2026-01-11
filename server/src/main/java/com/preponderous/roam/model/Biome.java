package com.preponderous.roam.model;

/**
 * Represents different biome types in the game world.
 * Each biome has different characteristics and resource distribution.
 * 
 * @author Daniel McCoy Stephenson
 */
public enum Biome {
    GRASSLAND("Grassland", "#90EE90"),
    FOREST("Forest", "#228B22"),
    DESERT("Desert", "#F4A460"),
    TUNDRA("Tundra", "#E0FFFF"),
    MOUNTAIN("Mountain", "#808080"),
    SWAMP("Swamp", "#556B2F");

    private final String displayName;
    private final String color;

    Biome(String displayName, String color) {
        this.displayName = displayName;
        this.color = color;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getColor() {
        return color;
    }
}
