package com.preponderous.roam.controller;

import com.preponderous.roam.dto.*;
import com.preponderous.roam.exception.SessionNotFoundException;
import com.preponderous.roam.model.GameState;
import com.preponderous.roam.service.GameService;
import com.preponderous.roam.service.MappingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

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

    /**
     * Initialize a new game session.
     */
    @PostMapping("/init")
    public ResponseEntity<SessionDTO> initSession(@RequestBody(required = false) InitSessionRequest request) {
        GameState gameState = gameService.createSession();
        SessionDTO sessionDTO = mappingService.toSessionDTO(gameState);
        return new ResponseEntity<>(sessionDTO, HttpStatus.CREATED);
    }

    /**
     * Get session state.
     */
    @GetMapping("/{sessionId}")
    public ResponseEntity<SessionDTO> getSession(@PathVariable String sessionId) {
        GameState gameState = gameService.getSession(sessionId);
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
        if (!gameService.sessionExists(sessionId)) {
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
        if (!gameService.sessionExists(sessionId)) {
            throw new SessionNotFoundException(sessionId);
        }
        gameService.updateTick(sessionId);
        GameState gameState = gameService.getSession(sessionId);
        SessionDTO sessionDTO = mappingService.toSessionDTO(gameState);
        return ResponseEntity.ok(sessionDTO);
    }
}
