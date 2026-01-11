-- Initial database schema for Roam game
-- Version 1.0.0

-- Game Sessions table
CREATE TABLE game_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    current_tick BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    world_seed BIGINT NOT NULL,
    world_room_width INTEGER NOT NULL,
    world_room_height INTEGER NOT NULL,
    world_resource_density DOUBLE PRECISION NOT NULL,
    world_hazard_density DOUBLE PRECISION NOT NULL
);

CREATE INDEX idx_game_sessions_created_at ON game_sessions(created_at);
CREATE INDEX idx_game_sessions_updated_at ON game_sessions(updated_at);

-- Players table
CREATE TABLE players (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    energy DOUBLE PRECISION NOT NULL,
    target_energy DOUBLE PRECISION NOT NULL,
    tick_created BIGINT NOT NULL,
    direction INTEGER NOT NULL,
    last_direction INTEGER NOT NULL,
    gathering BOOLEAN NOT NULL,
    placing BOOLEAN NOT NULL,
    crouching BOOLEAN NOT NULL,
    tick_last_moved BIGINT NOT NULL,
    tick_last_gathered BIGINT NOT NULL,
    tick_last_placed BIGINT NOT NULL,
    movement_speed INTEGER NOT NULL,
    gather_speed INTEGER NOT NULL,
    place_speed INTEGER NOT NULL,
    room_x INTEGER NOT NULL,
    room_y INTEGER NOT NULL,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    selected_inventory_slot_index INTEGER NOT NULL,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_players_session_id ON players(session_id);

-- Inventory Slots table
CREATE TABLE inventory_slots (
    id BIGSERIAL PRIMARY KEY,
    player_id VARCHAR(36) NOT NULL,
    slot_index INTEGER NOT NULL,
    item_name VARCHAR(100),
    num_items INTEGER NOT NULL,
    max_stack_size INTEGER NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE INDEX idx_inventory_slots_player_id ON inventory_slots(player_id);
CREATE INDEX idx_inventory_slots_player_slot ON inventory_slots(player_id, slot_index);

-- Rooms table
CREATE TABLE rooms (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    room_x INTEGER NOT NULL,
    room_y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    UNIQUE (session_id, room_x, room_y)
);

CREATE INDEX idx_rooms_session_id ON rooms(session_id);
CREATE INDEX idx_rooms_coordinates ON rooms(session_id, room_x, room_y);

-- Tiles table
CREATE TABLE tiles (
    id BIGSERIAL PRIMARY KEY,
    room_id BIGINT NOT NULL,
    tile_x INTEGER NOT NULL,
    tile_y INTEGER NOT NULL,
    biome VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100),
    resource_amount INTEGER NOT NULL,
    has_hazard BOOLEAN NOT NULL,
    hazard_type VARCHAR(100),
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
    UNIQUE (room_id, tile_x, tile_y)
);

CREATE INDEX idx_tiles_room_id ON tiles(room_id);
CREATE INDEX idx_tiles_coordinates ON tiles(room_id, tile_x, tile_y);

-- Game Entities table (trees, rocks, animals, etc.)
CREATE TABLE game_entities (
    db_id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(36) NOT NULL,
    room_id BIGINT NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    location_id VARCHAR(100),
    solid BOOLEAN NOT NULL,
    energy DOUBLE PRECISION,
    target_energy DOUBLE PRECISION,
    tick_created BIGINT,
    tick_last_reproduced BIGINT,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
);

CREATE INDEX idx_game_entities_room_id ON game_entities(room_id);
CREATE INDEX idx_game_entities_entity_id ON game_entities(entity_id);
CREATE INDEX idx_game_entities_type ON game_entities(entity_type);
CREATE INDEX idx_game_entities_location ON game_entities(location_id);
