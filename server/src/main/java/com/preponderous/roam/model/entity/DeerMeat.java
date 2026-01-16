package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents deer meat that can be consumed for energy.
 * 
 * @author Daniel McCoy Stephenson
 */
public class DeerMeat extends Entity {
    public static final double ENERGY_VALUE = 7.5;
    
    private double energyValue;

    public DeerMeat() {
        super("Deer Meat", "assets/images/chicken.png");
        this.energyValue = ENERGY_VALUE;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates deer meat with specific ID.
     */
    public DeerMeat(String id) {
        super(id, "Deer Meat", "assets/images/chicken.png");
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
