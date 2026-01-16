package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents chicken meat that can be consumed for energy.
 * 
 * @author Daniel McCoy Stephenson
 */
public class ChickenMeat extends Entity {
    public static final double ENERGY_VALUE = 7.5;
    
    private double energyValue;

    public ChickenMeat() {
        super("Chicken Meat", "assets/images/chicken.png");
        this.energyValue = ENERGY_VALUE;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates chicken meat with specific ID.
     */
    public ChickenMeat(String id) {
        super(id, "Chicken Meat", "assets/images/chicken.png");
        this.energyValue = ENERGY_VALUE;
        this.setSolid(false);
    }

    public double getEnergyValue() {
        return energyValue;
    }

    public void setEnergyValue(double energyValue) {
        this.energyValue = energyValue;
    }
}
