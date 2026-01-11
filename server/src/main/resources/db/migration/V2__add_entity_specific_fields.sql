-- Add entity-specific fields to support full entity persistence
-- Version 2.0.0

-- Add columns for harvestable entities (Tree, Rock, Bush)
ALTER TABLE game_entities ADD COLUMN harvest_count INTEGER;
ALTER TABLE game_entities ADD COLUMN max_harvest_count INTEGER;

-- Add columns for consumable entities (Apple, Berry, Wood, Stone)
ALTER TABLE game_entities ADD COLUMN energy_value DOUBLE PRECISION;
ALTER TABLE game_entities ADD COLUMN quantity INTEGER;

-- Add columns for animal entities (Deer, Bear, Chicken)
ALTER TABLE game_entities ADD COLUMN move_speed INTEGER;
ALTER TABLE game_entities ADD COLUMN flee_range DOUBLE PRECISION;
ALTER TABLE game_entities ADD COLUMN aggression_range DOUBLE PRECISION;
ALTER TABLE game_entities ADD COLUMN aggressive BOOLEAN;

CREATE INDEX idx_game_entities_type_room ON game_entities(entity_type, room_id);
