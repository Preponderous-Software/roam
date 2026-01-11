package com.preponderous.roam.persistence.repository;

import com.preponderous.roam.persistence.entity.RoomEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository for managing room persistence.
 * 
 * @author Daniel McCoy Stephenson
 */
@Repository
public interface RoomRepository extends JpaRepository<RoomEntity, Long> {
    
    /**
     * Find a room by session ID and coordinates.
     */
    @Query("SELECT r FROM RoomEntity r WHERE r.session.sessionId = :sessionId AND r.roomX = :roomX AND r.roomY = :roomY")
    Optional<RoomEntity> findBySessionIdAndCoordinates(
        @Param("sessionId") String sessionId,
        @Param("roomX") int roomX,
        @Param("roomY") int roomY
    );
    
    /**
     * Find all rooms for a session.
     */
    @Query("SELECT r FROM RoomEntity r WHERE r.session.sessionId = :sessionId")
    List<RoomEntity> findBySessionId(@Param("sessionId") String sessionId);
    
    /**
     * Delete all rooms for a session.
     */
    void deleteBySessionSessionId(String sessionId);
}
