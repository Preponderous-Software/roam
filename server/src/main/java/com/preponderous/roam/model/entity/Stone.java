package com.preponderous.roam.model.entity;

import com.preponderous.roam.model.Entity;

/**
 * Represents a stone resource entity.
 * Stone can be gathered from rocks and used for crafting.
 * 
 * @author Daniel McCoy Stephenson
 */
public class Stone extends Entity {
    private int quantity;

    public Stone() {
        super("Stone", "assets/images/stone.png");
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
