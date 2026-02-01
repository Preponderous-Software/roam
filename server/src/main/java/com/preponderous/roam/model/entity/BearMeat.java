package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents bear meat that can be consumed for energy.
 * 
 * @author Daniel McCoy Stephenson
 */
public class BearMeat extends Entity {
    public static final double ENERGY_VALUE = 7.5;
    
    private double energyValue;

    public BearMeat() {
        super("Bear Meat", "assets/images/bear.png");
        this.energyValue = ENERGY_VALUE;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates bear meat with specific ID.
     */
    public BearMeat(String id) {
        super(id, "Bear Meat", "assets/images/bear.png");
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
