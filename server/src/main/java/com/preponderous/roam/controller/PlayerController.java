package com.preponderous.roam.controller;

import com.preponderous.roam.dto.PlayerActionRequest;
import com.preponderous.roam.dto.PlayerDTO;
import com.preponderous.roam.exception.SessionNotFoundException;
import com.preponderous.roam.model.Entity;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.service.EntityInteractionService;
import com.preponderous.roam.service.GameService;
import com.preponderous.roam.service.MappingService;
import com.preponderous.roam.service.PlayerService;
import com.preponderous.roam.service.WorldGenerationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST controller for player management.
 * 
 * @author Daniel McCoy Stephenson
 */
@RestController
@RequestMapping("/api/v1/session/{sessionId}/player")
public class PlayerController {
    public static final double DEFAULT_FOOD_ENERGY_RESTORE = 10.0;

    @Autowired
    private GameService gameService;

    @Autowired
    private PlayerService playerService;

    @Autowired
    private MappingService mappingService;
    
    @Autowired
    private EntityInteractionService entityInteractionService;
    
    @Autowired
    private WorldGenerationService worldGenerationService;

    /**
     * Get player state.
     */
    @GetMapping
    public ResponseEntity<PlayerDTO> getPlayer(@PathVariable String sessionId) {
        Player player = gameService.getPlayer(sessionId);
        if (player == null) {
            throw new SessionNotFoundException(sessionId);
        }
        PlayerDTO playerDTO = mappingService.toPlayerDTO(player);
        return ResponseEntity.ok(playerDTO);
    }

    /**
     * Perform player action.
     */
    @PostMapping("/action")
    public ResponseEntity<PlayerDTO> performAction(
            @PathVariable String sessionId,
            @RequestBody PlayerActionRequest request) {
        
        Player player = gameService.getPlayer(sessionId);
        if (player == null) {
            throw new SessionNotFoundException(sessionId);
        }

        String action = request.getAction();
        if (action == null || action.trim().isEmpty()) {
            throw new IllegalArgumentException("Action must not be null or empty");
        }
        
        long currentTick = gameService.getCurrentTick(sessionId);

        switch (action) {
            case "move":
                if (request.getDirection() != null) {
                    playerService.setDirection(player, request.getDirection());
                    playerService.setTickLastMoved(player, currentTick);
                }
                break;
            case "stop":
                playerService.setDirection(player, -1);
                break;
            case "gather":
                if (request.getGathering() != null) {
                    playerService.setGathering(player, request.getGathering());
                    if (request.getGathering()) {
                        playerService.setTickLastGathered(player, currentTick);
                        
                        // Try to interact with entity in front of player
                        GameState gameState = gameService.getSession(sessionId);
                        Room currentRoom = worldGenerationService.getOrGenerateRoom(
                            gameState.getWorld(), 
                            player.getRoomX(), 
                            player.getRoomY(), 
                            currentTick
                        );
                        
                        Entity targetEntity = entityInteractionService.getEntityInFrontOfPlayer(player, currentRoom);
                        if (targetEntity != null) {
                            // Try harvesting harvestable entities
                            entityInteractionService.harvestEntity(targetEntity, player);
                            
                            // Try gathering resources
                            entityInteractionService.gatherResource(targetEntity, player, currentRoom);
                        }
                    }
                }
                break;
            case "place":
                if (request.getPlacing() != null) {
                    playerService.setPlacing(player, request.getPlacing());
                    if (request.getPlacing()) {
                        playerService.setTickLastPlaced(player, currentTick);
                    }
                }
                break;
            case "crouch":
                if (request.getCrouching() != null) {
                    playerService.setCrouching(player, request.getCrouching());
                }
                break;
            case "consume":
                if (request.getItemName() != null) {
                    // Consume food logic - remove the item from inventory and restore energy
                    boolean removed = player.getInventory().removeByItemName(request.getItemName());
                    if (removed) {
                        // In future, different food types could restore different amounts
                        playerService.addEnergy(player, DEFAULT_FOOD_ENERGY_RESTORE);
                    } else {
                        throw new IllegalArgumentException("Item not found in inventory: " + request.getItemName());
                    }
                }
                break;
            default:
                throw new IllegalArgumentException("Unknown action: " + action);
        }

        PlayerDTO playerDTO = mappingService.toPlayerDTO(player);
        return ResponseEntity.ok(playerDTO);
    }

    /**
     * Update player energy.
     */
    @PutMapping("/energy")
    public ResponseEntity<PlayerDTO> updateEnergy(
            @PathVariable String sessionId,
            @RequestParam double amount,
            @RequestParam(defaultValue = "add") String operation) {
        
        Player player = gameService.getPlayer(sessionId);
        if (player == null) {
            throw new SessionNotFoundException(sessionId);
        }

        if ("add".equals(operation)) {
            playerService.addEnergy(player, amount);
        } else if ("remove".equals(operation)) {
            playerService.removeEnergy(player, amount);
        } else {
            throw new IllegalArgumentException("Invalid operation: " + operation);
        }

        PlayerDTO playerDTO = mappingService.toPlayerDTO(player);
        return ResponseEntity.ok(playerDTO);
    }
}
