package com.preponderous.roam.persistence.repository;

import com.preponderous.roam.model.TokenBlacklist;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.Instant;

/**
 * Repository for TokenBlacklist entity operations.
 * 
 * @author Daniel McCoy Stephenson
 */
@Repository
public interface TokenBlacklistRepository extends JpaRepository<TokenBlacklist, Long> {
    
    boolean existsByToken(String token);
    
    void deleteByExpiresAtBefore(Instant now);
}
