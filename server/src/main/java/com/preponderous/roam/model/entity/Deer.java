package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.LivingEntity;

/**
 * Represents a deer wildlife entity.
 * Deer are passive animals that flee from threats.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Deer extends LivingEntity {
    public static final double DEFAULT_ENERGY = 50.0;
    public static final int DEFAULT_MOVE_SPEED = 35;
    public static final double FLEE_RANGE = 4.0;
    
    private int moveSpeed;
    private double fleeRange;

    public Deer(long tickCreated) {
        super("Deer", "assets/images/deer.png", DEFAULT_ENERGY, tickCreated);
        this.moveSpeed = DEFAULT_MOVE_SPEED;
        this.fleeRange = FLEE_RANGE;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates deer with specific ID.
     */
    public Deer(String id, long tickCreated) {
        super(id, "Deer", "assets/images/deer.png", DEFAULT_ENERGY, tickCreated);
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
