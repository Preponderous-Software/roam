package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents a bush interactive object.
 * Bushes can be harvested for berries.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Bush extends Entity {
    public static final int MAX_HARVEST_COUNT = 2;
    
    private int harvestCount;
    private int maxHarvestCount;

    public Bush() {
        super("Bush", "assets/images/bush.png");
        this.harvestCount = 0;
        this.maxHarvestCount = MAX_HARVEST_COUNT;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates bush with specific ID.
     */
    public Bush(String id) {
        super(id, "Bush", "assets/images/bush.png");
        this.harvestCount = 0;
        this.maxHarvestCount = MAX_HARVEST_COUNT;
        this.setSolid(false);
    }

    public int getHarvestCount() {
        return harvestCount;
    }

    public void setHarvestCount(int harvestCount) {
        this.harvestCount = harvestCount;
    }

    public int getMaxHarvestCount() {
        return maxHarvestCount;
    }

    public void setMaxHarvestCount(int maxHarvestCount) {
        this.maxHarvestCount = maxHarvestCount;
    }

    public boolean canHarvest() {
        return harvestCount < maxHarvestCount;
    }

    public void harvest() {
        if (canHarvest()) {
            harvestCount++;
        }
    }

    public boolean isDepleted() {
        return harvestCount >= maxHarvestCount;
    }
}
