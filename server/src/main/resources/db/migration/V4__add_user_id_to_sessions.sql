-- Add user_id column to game_sessions table for session ownership
-- Each session now belongs to a specific user

ALTER TABLE game_sessions ADD COLUMN user_id VARCHAR(50) NOT NULL DEFAULT 'default_user';

-- Remove default constraint after adding the column
ALTER TABLE game_sessions ALTER COLUMN user_id DROP DEFAULT;

-- Add index on user_id for efficient queries
CREATE INDEX idx_game_sessions_user_id ON game_sessions(user_id);
