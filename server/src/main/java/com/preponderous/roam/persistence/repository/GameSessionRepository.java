package com.preponderous.roam.persistence.repository;

import com.preponderous.roam.persistence.entity.GameSessionEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Repository for managing game session persistence.
 * 
 * @author Daniel McCoy Stephenson
 */
@Repository
public interface GameSessionRepository extends JpaRepository<GameSessionEntity, String> {
    
    /**
     * Find all sessions ordered by most recently updated first.
     */
    List<GameSessionEntity> findAllByOrderByUpdatedAtDesc();
    
    /**
     * Find sessions created after a certain date.
     */
    List<GameSessionEntity> findByCreatedAtAfter(LocalDateTime date);
    
    /**
     * Find sessions updated after a certain date.
     */
    List<GameSessionEntity> findByUpdatedAtAfter(LocalDateTime date);
    
    /**
     * Count total number of sessions.
     */
    @Query("SELECT COUNT(s) FROM GameSessionEntity s")
    long countAllSessions();
}
