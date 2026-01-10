package com.preponderous.roam.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents a living entity in the game that has energy and can interact with food.
 * 
 * @author Daniel McCoy Stephenson
 */
public abstract class LivingEntity extends Entity {
    public static final double MIN_ENERGY = 0.0;
    public static final double MAX_ENERGY = 100.0;
    
    private double energy;
    private double targetEnergy;
    private final long tickCreated;
    private Long tickLastReproduced;
    private final List<Class<? extends Entity>> edibleEntityTypes;

    public LivingEntity(String name, String imagePath, double energy, long tickCreated) {
        super(name, imagePath);
        this.energy = energy;
        this.targetEnergy = energy;
        this.tickCreated = tickCreated;
        this.tickLastReproduced = null;
        this.edibleEntityTypes = new ArrayList<>();
    }

    public double getEnergy() {
        return energy;
    }

    public void setEnergy(double energy) {
        if (energy < MIN_ENERGY) {
            this.energy = MIN_ENERGY;
        } else if (energy > MAX_ENERGY) {
            this.energy = MAX_ENERGY;
        } else {
            this.energy = energy;
        }
    }

    public void addEnergy(double amount) {
        if (amount < 0) {
            throw new IllegalArgumentException("Amount must be non-negative: " + amount);
        }
        if (this.energy + amount > MAX_ENERGY) {
            this.energy = MAX_ENERGY;
        } else {
            this.energy += amount;
        }
    }

    public void removeEnergy(double amount) {
        if (amount < 0) {
            throw new IllegalArgumentException("Amount must be non-negative: " + amount);
        }
        if (this.energy - amount < MIN_ENERGY) {
            this.energy = MIN_ENERGY;
        } else {
            this.energy -= amount;
        }
    }

    public boolean needsEnergy() {
        return energy < targetEnergy * 0.50;
    }

    public double getTargetEnergy() {
        return targetEnergy;
    }

    public void setTargetEnergy(double targetEnergy) {
        this.targetEnergy = targetEnergy;
    }

    public long getTickCreated() {
        return tickCreated;
    }

    public Long getTickLastReproduced() {
        return tickLastReproduced;
    }

    public void setTickLastReproduced(Long tick) {
        this.tickLastReproduced = tick;
    }

    public long getAge(long currentTick) {
        return currentTick - tickCreated;
    }

    public void kill() {
        this.energy = 0;
    }

    public List<Class<? extends Entity>> getEdibleEntityTypes() {
        return edibleEntityTypes;
    }

    public boolean canEat(Entity entity) {
        for (Class<? extends Entity> entityType : edibleEntityTypes) {
            if (entityType.isInstance(entity)) {
                return true;
            }
        }
        return false;
    }
}
