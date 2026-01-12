package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents a tree interactive object.
 * Trees can be harvested for wood.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Tree extends Entity {
    public static final int MAX_HARVEST_COUNT = 3;
    
    private int harvestCount;
    private int maxHarvestCount;

    public Tree() {
        super("Tree", "assets/images/tree.png");
        this.harvestCount = 0;
        this.maxHarvestCount = MAX_HARVEST_COUNT;
        this.setSolid(true);
    }
    
    /**
     * Constructor for persistence - creates tree with specific ID.
     */
    public Tree(String id) {
        super(id, "Tree", "assets/images/tree.png");
        this.harvestCount = 0;
        this.maxHarvestCount = MAX_HARVEST_COUNT;
        this.setSolid(true);
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
