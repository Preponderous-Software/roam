package com.preponderous.roam.exception;

/**
 * Exception thrown when a session is not found.
 * 
 * @author Daniel McCoy Stephenson
 */
public class SessionNotFoundException extends RuntimeException {
    public SessionNotFoundException(String sessionId) {
        super("Session not found: " + sessionId);
    }
}
