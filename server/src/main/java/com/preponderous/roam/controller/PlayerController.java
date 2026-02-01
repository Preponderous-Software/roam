package com.preponderous.roam.controller;

import com.preponderous.roam.dto.PlayerActionRequest;
import com.preponderous.roam.dto.PlayerDTO;
import com.preponderous.roam.exception.SessionNotFoundException;
import com.preponderous.roam.model.Entity;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.LivingEntity;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.entity.*;
import com.preponderous.roam.service.EntityInteractionService;
import com.preponderous.roam.service.GameService;
import com.preponderous.roam.service.MappingService;
import com.preponderous.roam.service.PlayerService;
import com.preponderous.roam.service.RateLimitService;
import com.preponderous.roam.service.WorldGenerationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
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
    
    @Autowired
    private RateLimitService rateLimitService;
    
    /**
     * Get the username of the currently authenticated user.
     */
    private String getCurrentUsername() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication.getName();
    }

    /**
     * Get player state.
     */
    @GetMapping
    public ResponseEntity<PlayerDTO> getPlayer(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        Player player = gameState.getPlayer();
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
        
        String username = getCurrentUsername();
        
        // Apply rate limiting
        rateLimitService.checkPlayerActionLimit(username);
        
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        Player player = gameState.getPlayer();

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
                    playerService.broadcastPlayerPosition(sessionId, player, username);
                }
                break;
            case "stop":
                playerService.setDirection(player, -1);
                playerService.broadcastPlayerPosition(sessionId, player, username);
                break;
            case "gather":
                if (request.getGathering() != null) {
                    playerService.setGathering(player, request.getGathering());
                    if (request.getGathering()) {
                        playerService.setTickLastGathered(player, currentTick);
                        
                        // Get current game state and room
                        Room currentRoom = worldGenerationService.getOrGenerateRoom(
                            gameState.getWorld(), 
                            player.getRoomX(), 
                            player.getRoomY(), 
                            currentTick
                        );
                        
                        Entity targetEntity = null;
                        
                        // If tile coordinates provided, get entity at that tile
                        if (request.getTileX() != null && request.getTileY() != null) {
                            targetEntity = entityInteractionService.getEntityAtTile(
                                player.getRoomX(), 
                                player.getRoomY(), 
                                request.getTileX(), 
                                request.getTileY(), 
                                currentRoom
                            );
                        } else {
                            // Otherwise get entity in front of player
                            targetEntity = entityInteractionService.getEntityInFrontOfPlayer(player, currentRoom);
                        }
                        
                        // If no entity found at the target location, do nothing (intentional)
                        if (targetEntity != null) {
                            // Try harvesting harvestable entities (trees, rocks, bushes) for resources
                            // Harvesting extracts resources but leaves the entity in place (with cooldown)
                            entityInteractionService.harvestEntity(targetEntity, player);
                            
                            // Try gathering resource entities (apples, berries, wood, stone) from the ground
                            // Gathering picks up and removes the entity completely
                            entityInteractionService.gatherResource(targetEntity, player, currentRoom, sessionId);
                            
                            // Try hunting wildlife (bears, deer, chickens)
                            if (targetEntity instanceof LivingEntity) {
                                LivingEntity livingEntity = (LivingEntity) targetEntity;
                                // Deal 50 damage per gather action (might need multiple clicks to kill)
                                entityInteractionService.huntEntity(livingEntity, player, currentRoom, 50.0, sessionId);
                            }
                        }
                    }
                }
                break;
            case "place":
                if (request.getPlacing() != null) {
                    playerService.setPlacing(player, request.getPlacing());
                    if (request.getPlacing()) {
                        playerService.setTickLastPlaced(player, currentTick);
                        
                        // Get selected item from inventory
                        String itemName = player.getInventory().getSelectedInventorySlot().getItemName();
                        if (itemName != null && !itemName.isEmpty()) {
                            // Get target tile coordinates
                            Integer targetTileX = request.getTileX();
                            Integer targetTileY = request.getTileY();
                            
                            if (targetTileX != null && targetTileY != null) {
                                // Get current room
                                Room currentRoom = worldGenerationService.getOrGenerateRoom(
                                    gameState.getWorld(), 
                                    player.getRoomX(), 
                                    player.getRoomY(), 
                                    currentTick
                                );
                                
                                // Check if tile is empty (no solid entity)
                                String targetLocationId = player.getRoomX() + "," + player.getRoomY() + "," + 
                                                         targetTileX + "," + targetTileY;
                                boolean occupied = currentRoom.getEntitiesList().stream()
                                    .anyMatch(e -> e.isSolid() && targetLocationId.equals(e.getLocationId()));
                                
                                if (!occupied) {
                                    // Create entity based on item name and place it
                                    Entity placedEntity = createEntityFromItemName(itemName);
                                    if (placedEntity != null) {
                                        placedEntity.setLocationId(targetLocationId);
                                        currentRoom.addEntity(placedEntity);
                                        
                                        // Broadcast entity added via WebSocket
                                        entityInteractionService.broadcastEntityAdded(sessionId, placedEntity);
                                        
                                        // Remove item from inventory
                                        player.getInventory().removeByItemName(itemName);
                                    }
                                }
                            }
                        }
                    }
                }
                break;
            case "crouch":
                // Note: Crouching is currently tracked but has no gameplay effect
                // Future enhancements could implement stealth mechanics, speed reduction, etc.
                if (request.getCrouching() != null) {
                    playerService.setCrouching(player, request.getCrouching());
                }
                break;
            case "run":
                if (request.getRunning() != null) {
                    playerService.setRunning(player, request.getRunning());
                }
                break;
            case "consume":
                if (request.getItemName() != null) {
                    // Consume food logic - remove the item from inventory and restore energy
                    boolean removed = player.getInventory().removeByItemName(request.getItemName());
                    if (removed) {
                        // In future, different food types could restore different amounts
                        playerService.addEnergy(player, DEFAULT_FOOD_ENERGY_RESTORE);
                        // Increment food eaten stat
                        player.incrementFoodEaten();
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
     * Create an entity from an item name for placing.
     * 
     * @param itemName the item name
     * @return the created entity, or null if item cannot be placed
     */
    private Entity createEntityFromItemName(String itemName) {
        switch (itemName) {
            case "Grass":
                // TODO: Grass should be an entity like in the original implementation, not just a tile type
                // This would allow grass to be gathered, placed, and interacted with
                return null;
            case "Wood":
                return new Wood();
            case "Stone":
                return new Stone();
            case "Apple":
                return new Apple();
            case "Berry":
                return new Berry();
            case "Chicken Meat":
                return new ChickenMeat();
            case "Bear Meat":
                return new BearMeat();
            case "Deer Meat":
                return new DeerMeat();
            // Trees, rocks, and bushes are not directly placeable from inventory
            default:
                return null;
        }
    }

    /**
     * Update player energy.
     */
    @PutMapping("/energy")
    public ResponseEntity<PlayerDTO> updateEnergy(
            @PathVariable String sessionId,
            @RequestParam double amount,
            @RequestParam(defaultValue = "add") String operation) {
        
        String username = getCurrentUsername();
        
        // Apply rate limiting - throws RateLimitExceededException if limit exceeded, stopping further processing
        rateLimitService.checkPlayerActionLimit(username);
        
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        Player player = gameState.getPlayer();

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
