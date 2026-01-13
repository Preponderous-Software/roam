package com.preponderous.roam.controller;

import com.preponderous.roam.dto.InventoryDTO;
import com.preponderous.roam.exception.SessionNotFoundException;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Inventory;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.service.GameService;
import com.preponderous.roam.service.MappingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

/**
 * REST controller for inventory management.
 * 
 * @author Daniel McCoy Stephenson
 */
@RestController
@RequestMapping("/api/v1/session/{sessionId}/inventory")
public class InventoryController {

    @Autowired
    private GameService gameService;

    @Autowired
    private MappingService mappingService;
    
    /**
     * Get the username of the currently authenticated user.
     */
    private String getCurrentUsername() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication.getName();
    }

    /**
     * Get player inventory.
     */
    @GetMapping
    public ResponseEntity<InventoryDTO> getInventory(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        Player player = gameState.getPlayer();
        InventoryDTO inventoryDTO = mappingService.toInventoryDTO(player.getInventory());
        return ResponseEntity.ok(inventoryDTO);
    }

    /**
     * Add item to inventory.
     */
    @PostMapping("/add")
    public ResponseEntity<InventoryDTO> addItem(
            @PathVariable String sessionId,
            @RequestParam String itemName) {
        
        if (itemName == null || itemName.trim().isEmpty()) {
            throw new IllegalArgumentException("Item name must not be null or empty");
        }
        
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        Player player = gameState.getPlayer();
        Inventory inventory = player.getInventory();
        boolean added = inventory.placeIntoFirstAvailableInventorySlot(itemName);
        
        if (!added) {
            throw new IllegalArgumentException("Inventory is full");
        }

        InventoryDTO inventoryDTO = mappingService.toInventoryDTO(inventory);
        return ResponseEntity.ok(inventoryDTO);
    }

    /**
     * Remove item from inventory.
     */
    @PostMapping("/remove")
    public ResponseEntity<InventoryDTO> removeItem(
            @PathVariable String sessionId,
            @RequestParam String itemName) {
        
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        Player player = gameState.getPlayer();
        Inventory inventory = player.getInventory();
        boolean removed = inventory.removeByItemName(itemName);
        
        if (!removed) {
            throw new IllegalArgumentException("Item not found in inventory");
        }

        InventoryDTO inventoryDTO = mappingService.toInventoryDTO(inventory);
        return ResponseEntity.ok(inventoryDTO);
    }

    /**
     * Select inventory slot.
     */
    @PutMapping("/select")
    public ResponseEntity<InventoryDTO> selectSlot(
            @PathVariable String sessionId,
            @RequestParam int slotIndex) {
        
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        Player player = gameState.getPlayer();
        Inventory inventory = player.getInventory();
        if (slotIndex < 0 || slotIndex >= inventory.getNumInventorySlots()) {
            throw new IllegalArgumentException("Invalid slot index: " + slotIndex);
        }

        inventory.setSelectedInventorySlotIndex(slotIndex);

        InventoryDTO inventoryDTO = mappingService.toInventoryDTO(inventory);
        return ResponseEntity.ok(inventoryDTO);
    }

    /**
     * Clear inventory.
     */
    @DeleteMapping
    public ResponseEntity<InventoryDTO> clearInventory(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        Player player = gameState.getPlayer();
        Inventory inventory = player.getInventory();
        inventory.clear();

        InventoryDTO inventoryDTO = mappingService.toInventoryDTO(inventory);
        return ResponseEntity.ok(inventoryDTO);
    }
}
