package com.preponderous.roam.controller;

import com.preponderous.roam.dto.PlayerActionRequest;
import com.preponderous.roam.dto.PlayerDTO;
import com.preponderous.roam.exception.SessionNotFoundException;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.service.GameService;
import com.preponderous.roam.service.MappingService;
import com.preponderous.roam.service.PlayerService;
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
@CrossOrigin(origins = "*")
public class PlayerController {

    @Autowired
    private GameService gameService;

    @Autowired
    private PlayerService playerService;

    @Autowired
    private MappingService mappingService;

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
                    // Consume food logic
                    playerService.addEnergy(player, 10.0);
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
