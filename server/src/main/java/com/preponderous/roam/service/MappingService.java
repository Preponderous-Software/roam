package com.preponderous.roam.service;

import com.preponderous.roam.dto.*;
import com.preponderous.roam.model.*;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * Service for mapping between domain models and DTOs.
 * 
 * @author Daniel McCoy Stephenson
 */
@Service
public class MappingService {

    public SessionDTO toSessionDTO(GameState gameState) {
        SessionDTO dto = new SessionDTO();
        dto.setSessionId(gameState.getSessionId());
        dto.setCurrentTick(gameState.getCurrentTick());
        dto.setPlayer(toPlayerDTO(gameState.getPlayer()));
        return dto;
    }

    public PlayerDTO toPlayerDTO(Player player) {
        PlayerDTO dto = new PlayerDTO();
        dto.setId(player.getId());
        dto.setName(player.getName());
        dto.setEnergy(player.getEnergy());
        dto.setTargetEnergy(player.getTargetEnergy());
        dto.setDirection(player.getDirection());
        dto.setLastDirection(player.getLastDirection());
        dto.setGathering(player.isGathering());
        dto.setPlacing(player.isPlacing());
        dto.setCrouching(player.isCrouching());
        dto.setMoving(player.isMoving());
        dto.setDead(player.isDead());
        dto.setTickLastMoved(player.getTickLastMoved());
        dto.setTickLastGathered(player.getTickLastGathered());
        dto.setTickLastPlaced(player.getTickLastPlaced());
        dto.setMovementSpeed(player.getMovementSpeed());
        dto.setGatherSpeed(player.getGatherSpeed());
        dto.setPlaceSpeed(player.getPlaceSpeed());
        dto.setInventory(toInventoryDTO(player.getInventory()));
        return dto;
    }

    public InventoryDTO toInventoryDTO(Inventory inventory) {
        InventoryDTO dto = new InventoryDTO();
        
        List<InventorySlotDTO> slotDTOs = new ArrayList<>();
        for (InventorySlot slot : inventory.getInventorySlots()) {
            slotDTOs.add(toInventorySlotDTO(slot));
        }
        
        dto.setSlots(slotDTOs);
        dto.setSelectedSlotIndex(inventory.getSelectedInventorySlotIndex());
        dto.setNumFreeSlots(inventory.getNumFreeInventorySlots());
        dto.setNumTakenSlots(inventory.getNumTakenInventorySlots());
        dto.setNumItems(inventory.getNumItems());
        
        return dto;
    }

    public InventorySlotDTO toInventorySlotDTO(InventorySlot slot) {
        InventorySlotDTO dto = new InventorySlotDTO();
        dto.setItemName(slot.getItemName());
        dto.setNumItems(slot.getNumItems());
        dto.setMaxStackSize(slot.getMaxStackSize());
        dto.setEmpty(slot.isEmpty());
        return dto;
    }
}
