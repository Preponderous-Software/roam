package com.preponderous.roam.exception;

/**
 * Exception thrown when a user registration conflict occurs
 * (e.g., duplicate username or email).
 *
 * @author Daniel McCoy Stephenson
 */
public class UserAlreadyExistsException extends RuntimeException {
    public UserAlreadyExistsException(String message) {
        super(message);
    }
}
