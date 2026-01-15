package com.preponderous.roam.exception;

/**
 * Exception thrown when rate limit is exceeded.
 * 
 * @author Daniel McCoy Stephenson
 */
public class RateLimitExceededException extends RuntimeException {
    
    public RateLimitExceededException(String message) {
        super(message);
    }
}
