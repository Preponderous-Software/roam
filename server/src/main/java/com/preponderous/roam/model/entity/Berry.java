package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents a berry resource entity.
 * Berries can be gathered and consumed for energy.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Berry extends Entity {
    public static final double ENERGY_VALUE = 10.0;
    
    private double energyValue;

    public Berry() {
        super("Berry", "assets/images/berry.png");
        this.energyValue = ENERGY_VALUE;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates berry with specific ID.
     */
    public Berry(String id) {
        super(id, "Berry", "assets/images/berry.png");
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
