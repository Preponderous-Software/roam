package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.LivingEntity;

/**
 * Represents a chicken wildlife entity.
 * Chickens are passive animals that flee from threats.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Chicken extends LivingEntity {
    public static final double DEFAULT_ENERGY = 30.0;
    public static final int DEFAULT_MOVE_SPEED = 25;
    public static final double FLEE_RANGE = 3.0;
    
    private int moveSpeed;
    private double fleeRange;

    public Chicken(long tickCreated) {
        super("Chicken", "assets/images/chicken.png", DEFAULT_ENERGY, tickCreated);
        this.moveSpeed = DEFAULT_MOVE_SPEED;
        this.fleeRange = FLEE_RANGE;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates chicken with specific ID.
     */
    public Chicken(String id, long tickCreated) {
        super(id, "Chicken", "assets/images/chicken.png", DEFAULT_ENERGY, tickCreated);
        this.moveSpeed = DEFAULT_MOVE_SPEED;
        this.fleeRange = FLEE_RANGE;
        this.setSolid(false);
    }

    public int getMoveSpeed() {
        return moveSpeed;
    }

    public void setMoveSpeed(int moveSpeed) {
        this.moveSpeed = moveSpeed;
    }

    public double getFleeRange() {
        return fleeRange;
    }

    public void setFleeRange(double fleeRange) {
        this.fleeRange = fleeRange;
    }
}
