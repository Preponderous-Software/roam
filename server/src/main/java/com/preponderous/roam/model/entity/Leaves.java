package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents a leaves resource entity.
 * Leaves can be gathered from bushes or the ground and used for crafting.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Leaves extends Entity {
    private int quantity;

    public Leaves() {
        super("Leaves", "assets/images/leaves.png");
        this.quantity = 1;
        this.setSolid(false);
    }
    
    /**
     * Constructor for persistence - creates leaves with specific ID.
     */
    public Leaves(String id) {
        super(id, "Leaves", "assets/images/leaves.png");
        this.quantity = 1;
        this.setSolid(false);
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }
}
