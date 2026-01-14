package com.preponderous.roam.controller;

import com.preponderous.roam.dto.*;
import com.preponderous.roam.exception.SessionNotFoundException;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.model.Player;
import com.preponderous.roam.model.Room;
import com.preponderous.roam.model.World;
import com.preponderous.roam.service.GameService;
import com.preponderous.roam.service.MappingService;
import com.preponderous.roam.service.WorldGenerationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * REST controller for game session management.
 * 
 * @author Daniel McCoy Stephenson
 */
@RestController
@RequestMapping("/api/v1/session")
public class SessionController {

    @Autowired
    private GameService gameService;

    @Autowired
    private MappingService mappingService;

    @Autowired
    private WorldGenerationService worldGenerationService;
    
    /**
     * Get the username of the currently authenticated user.
     */
    private String getCurrentUsername() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication.getName();
    }

    /**
     * Initialize a new game session.
     */
    @PostMapping("/init")
    public ResponseEntity<SessionDTO> initSession(@RequestBody(required = false) InitSessionRequest request) {
        String username = getCurrentUsername();
        GameState gameState = gameService.createSession(username);
        SessionDTO sessionDTO = mappingService.toSessionDTO(gameState);
        return new ResponseEntity<>(sessionDTO, HttpStatus.CREATED);
    }

    /**
     * Get session state.
     */
    @GetMapping("/{sessionId}")
    public ResponseEntity<SessionDTO> getSession(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        SessionDTO sessionDTO = mappingService.toSessionDTO(gameState);
        return ResponseEntity.ok(sessionDTO);
    }

    /**
     * Delete a session.
     */
    @DeleteMapping("/{sessionId}")
    public ResponseEntity<Void> deleteSession(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        gameService.deleteSession(sessionId);
        return ResponseEntity.noContent().build();
    }

    /**
     * Update game tick.
     */
    @PostMapping("/{sessionId}/tick")
    public ResponseEntity<SessionDTO> updateTick(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        gameService.updateTick(sessionId);
        gameState = gameService.getSession(sessionId, username);
        SessionDTO sessionDTO = mappingService.toSessionDTO(gameState);
        return ResponseEntity.ok(sessionDTO);
    }
    
    /**
     * Save a game session to the database.
     */
    @PostMapping("/{sessionId}/save")
    public ResponseEntity<Map<String, String>> saveSession(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        gameService.saveSession(sessionId);
        Map<String, String> response = new HashMap<>();
        response.put("message", "Session saved successfully");
        response.put("sessionId", sessionId);
        return ResponseEntity.ok(response);
    }
    
    /**
     * Load a game session from the database.
     */
    @PostMapping("/{sessionId}/load")
    public ResponseEntity<SessionDTO> loadSession(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.loadSession(sessionId);
        if (gameState == null || !gameState.getUserId().equals(username)) {
            throw new SessionNotFoundException(sessionId);
        }
        SessionDTO sessionDTO = mappingService.toSessionDTO(gameState);
        return ResponseEntity.ok(sessionDTO);
    }

    /**
     * Get the world for a session.
     */
    @GetMapping("/{sessionId}/world")
    public ResponseEntity<WorldDTO> getWorld(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        WorldDTO worldDTO = mappingService.toWorldDTO(gameState.getWorld());
        return ResponseEntity.ok(worldDTO);
    }

    /**
     * Get a specific room by coordinates.
     */
    @GetMapping("/{sessionId}/room/{x}/{y}")
    public ResponseEntity<RoomDTO> getRoom(
            @PathVariable String sessionId,
            @PathVariable int x,
            @PathVariable int y) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        World world = gameState.getWorld();
        long currentTick = gameState.getCurrentTick();
        Room room = worldGenerationService.getOrGenerateRoom(world, x, y, currentTick);
        RoomDTO roomDTO = mappingService.toRoomDTO(room);
        return ResponseEntity.ok(roomDTO);
    }

    /**
     * Get all entities in a session across all loaded rooms.
     */
    @GetMapping("/{sessionId}/entities")
    public ResponseEntity<List<EntityDTO>> getEntities(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        World world = gameState.getWorld();
        List<EntityDTO> allEntities = new ArrayList<>();
        
        for (Room room : world.getRooms().values()) {
            List<EntityDTO> roomEntities = room.getEntitiesList().stream()
                .map(mappingService::toEntityDTO)
                .collect(Collectors.toList());
            allEntities.addAll(roomEntities);
        }
        
        return ResponseEntity.ok(allEntities);
    }
    
    /**
     * Join an existing game session as a new player.
     */
    @PostMapping("/{sessionId}/join")
    public ResponseEntity<SessionDTO> joinSession(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        
        // Attempt to join the session. Do not perform a separate, unauthenticated
        // existence check to avoid leaking which session IDs are valid.
        boolean joined = gameService.joinSession(sessionId, username);
        if (!joined) {
            // Session is full, does not exist, or other error
            // Return CONFLICT for full sessions, NOT_FOUND for missing sessions
            // We use a generic error to avoid leaking session existence
            return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(null);
        }
        
        // Return updated session state using access-controlled session retrieval
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            // Defensive check: should not occur if join succeeded
            throw new SessionNotFoundException(sessionId);
        }
        
        SessionDTO sessionDTO = mappingService.toSessionDTO(gameState);
        return ResponseEntity.ok(sessionDTO);
    }
    
    /**
     * Leave a game session.
     */
    @PostMapping("/{sessionId}/leave")
    public ResponseEntity<Map<String, String>> leaveSession(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        boolean left = gameService.leaveSession(sessionId, username);
        Map<String, String> response = new HashMap<>();
        if (left) {
            response.put("message", "Successfully left session");
            response.put("sessionId", sessionId);
            return ResponseEntity.ok(response);
        } else {
            response.put("message", "Cannot leave session (owner cannot leave or user is not in session)");
            response.put("sessionId", sessionId);
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
        }
    }
    
    /**
     * Get all players in a session.
     */
    @GetMapping("/{sessionId}/players")
    public ResponseEntity<Map<String, PlayerDTO>> getPlayers(@PathVariable String sessionId) {
        String username = getCurrentUsername();
        GameState gameState = gameService.getSession(sessionId, username);
        if (gameState == null) {
            throw new SessionNotFoundException(sessionId);
        }
        
        Map<String, PlayerDTO> playerDTOs = new HashMap<>();
        for (Map.Entry<String, Player> entry : gameState.getPlayers().entrySet()) {
            playerDTOs.put(entry.getKey(), mappingService.toPlayerDTO(entry.getValue()));
        }
        
        return ResponseEntity.ok(playerDTOs);
    }
}
