-- Add visited_rooms column to track which rooms a player has explored
ALTER TABLE players ADD COLUMN visited_rooms TEXT;
