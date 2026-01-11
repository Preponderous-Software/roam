package com.preponderous.roam.persistence.repository;

import com.preponderous.roam.persistence.entity.PlayerEntityData;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Repository for managing player persistence.
 * 
 * @author Daniel McCoy Stephenson
 */
@Repository
public interface PlayerRepository extends JpaRepository<PlayerEntityData, String> {
    
    /**
     * Find player by session ID.
     */
    @Query("SELECT p FROM PlayerEntityData p WHERE p.session.sessionId = :sessionId")
    Optional<PlayerEntityData> findBySessionId(@Param("sessionId") String sessionId);
    
    /**
     * Delete player by session ID.
     */
    void deleteBySessionSessionId(String sessionId);
}
