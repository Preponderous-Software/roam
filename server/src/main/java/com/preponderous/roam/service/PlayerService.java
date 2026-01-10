package com.preponderous.roam.service;

import com.preponderous.roam.model.Player;
import org.springframework.stereotype.Service;

/**
 * Service for managing player state and actions.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class PlayerService {

    /**
     * Update player direction.
     */
    public void setDirection(Player player, int direction) {
        player.setDirection(direction);
    }

    /**
     * Update player gathering state.
     */
    public void setGathering(Player player, boolean gathering) {
        player.setGathering(gathering);
    }

    /**
     * Update player placing state.
     */
    public void setPlacing(Player player, boolean placing) {
        player.setPlacing(placing);
    }

    /**
     * Update player crouching state.
     */
    public void setCrouching(Player player, boolean crouching) {
        player.setCrouching(crouching);
    }

    /**
     * Add energy to player.
     */
    public void addEnergy(Player player, double amount) {
        player.addEnergy(amount);
    }

    /**
     * Remove energy from player.
     */
    public void removeEnergy(Player player, double amount) {
        player.removeEnergy(amount);
    }

    /**
     * Update player tick last moved.
     */
    public void setTickLastMoved(Player player, long tick) {
        player.setTickLastMoved(tick);
    }

    /**
     * Update player tick last gathered.
     */
    public void setTickLastGathered(Player player, long tick) {
        player.setTickLastGathered(tick);
    }

    /**
     * Update player tick last placed.
     */
    public void setTickLastPlaced(Player player, long tick) {
        player.setTickLastPlaced(tick);
    }

    /**
     * Set player movement speed.
     */
    public void setMovementSpeed(Player player, int speed) {
        player.setMovementSpeed(speed);
    }

    /**
     * Set player gather speed.
     */
    public void setGatherSpeed(Player player, int speed) {
        player.setGatherSpeed(speed);
    }

    /**
     * Set player place speed.
     */
    public void setPlaceSpeed(Player player, int speed) {
        player.setPlaceSpeed(speed);
    }
}
