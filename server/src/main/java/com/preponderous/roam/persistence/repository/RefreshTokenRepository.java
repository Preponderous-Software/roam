package com.preponderous.roam.persistence.repository;

import com.preponderous.roam.model.RefreshToken;
import com.preponderous.roam.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.Optional;

/**
 * Repository for RefreshToken entity operations.
 * 
 * @author Daniel McCoy Stephenson
 */
@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {
    
    Optional<RefreshToken> findByToken(String token);
    
    void deleteByUser(User user);
    
    void deleteByExpiresAtBefore(Instant now);
}
