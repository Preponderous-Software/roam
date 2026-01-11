package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents an apple resource entity.
 * Apples can be gathered and consumed for energy.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Apple extends Entity {
    public static final double ENERGY_VALUE = 15.0;
    
    private double energyValue;

    public Apple() {
        super("Apple", "assets/images/apple.png");
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
