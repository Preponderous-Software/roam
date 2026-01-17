-- Add running field to players table
-- Version 1.1.0 - WI-003: Implement Run Speed Modifier

ALTER TABLE players ADD COLUMN running BOOLEAN NOT NULL DEFAULT FALSE;
