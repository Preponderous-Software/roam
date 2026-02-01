-- Add stats tracking fields to players table
ALTER TABLE players ADD COLUMN score INTEGER NOT NULL DEFAULT 0;
ALTER TABLE players ADD COLUMN rooms_explored INTEGER NOT NULL DEFAULT 0;
ALTER TABLE players ADD COLUMN food_eaten INTEGER NOT NULL DEFAULT 0;
ALTER TABLE players ADD COLUMN number_of_deaths INTEGER NOT NULL DEFAULT 0;
