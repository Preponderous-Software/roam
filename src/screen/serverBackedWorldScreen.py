"""
Server-Backed World Screen
Simplified world screen that communicates with server for all game logic.
No local world generation or entity management.

@author Daniel McCoy Stephenson (refactored for server-backed architecture)
"""

import pygame
import logging
from config.config import Config
from stats.stats import Stats
from ui.energyBar import EnergyBar
from lib.graphik.src.graphik import Graphik
from player.player import Player
from ui.status import Status
from world.tickCounter import TickCounter
from screen.screenType import ScreenType
from client.api_client import RoamAPIClient

# Import item classes for inventory restoration
from entity.apple import Apple
from entity.banana import Banana
from entity.berry import Berry
from entity.stone import Stone
from entity.coalOre import CoalOre
from entity.ironOre import IronOre
from entity.wood import Wood
from entity.oakWood import OakWood
from entity.jungleWood import JungleWood
from entity.grass import Grass
from entity.leaves import Leaves
from entity.chicken import Chicken
from entity.bear import Bear
from entity.deer import Deer
from entity.chickenMeat import ChickenMeat
from entity.bearMeat import BearMeat
from entity.deerMeat import DeerMeat

# Configure logging for this module
logger = logging.getLogger(__name__)


class ServerBackedWorldScreen:
    """Simplified world screen that uses server for all game logic."""
    
    def __init__(
        self,
        graphik: Graphik,
        config: Config,
        status: Status,
        tickCounter: TickCounter,
        stats: Stats,
        player: Player,
        api_client: RoamAPIClient,
        session_id: str,
    ):
        logger.info(f"Initializing ServerBackedWorldScreen with session_id: {session_id}")
        self.graphik = graphik
        self.config = config
        self.status = status
        self.tickCounter = tickCounter
        self.stats = stats
        self.player = player
        self.api_client = api_client
        self.session_id = session_id
        
        self.running = True
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = False
        
        # Server state
        self.player_data = None
        self.server_tick = 0
        
        # World rendering
        self.current_room = None
        self.current_room_x = 0
        self.current_room_y = 0
        # Size of each tile in pixels; increased from 16 to 32 for better visibility like original
        # Can be overridden via Config.tile_size to match server room dimensions/display size.
        self.tile_size = getattr(self.config, "tile_size", 32)
        
        # Mouse state tracking for continuous gathering
        self.mouse_button_held = {1: False, 3: False}  # Track left and right mouse buttons
        self.last_gather_tile = None
        self.gather_cooldown_frames = 0  # Frames since last gather
        self.gather_cooldown_max = 10  # Gather every 10 frames when holding
        
        # Load player sprites with error handling
        self.player_sprites = {}
        sprite_paths = {
            0: "assets/images/player_up.png",
            1: "assets/images/player_left.png",
            2: "assets/images/player_down.png",
            3: "assets/images/player_right.png"
        }
        
        for direction, path in sprite_paths.items():
            try:
                sprite = pygame.image.load(path)
                # Scale sprites to tile size
                self.player_sprites[direction] = pygame.transform.scale(
                    sprite,
                    (self.tile_size, self.tile_size)
                )
            except (pygame.error, FileNotFoundError) as e:
                logger.warning(f"Failed to load player sprite {path}: {e}")
                # Create a fallback colored square
                fallback = pygame.Surface((self.tile_size, self.tile_size))
                fallback.fill((50, 150, 255))  # Blue color
                self.player_sprites[direction] = fallback
        
        # Load entity sprites
        self.entity_sprites = {}
        entity_sprite_paths = {
            'Bear': "assets/images/bear.png",
            'Chicken': "assets/images/chicken.png",
            'Deer': "assets/images/deer.png",  # NEW: dedicated sprite
            'Tree': "assets/images/oakWood.png",
            'Rock': "assets/images/stone.png",
            'Bush': "assets/images/leaves.png",
            'Apple': "assets/images/apple.png",
            'Berry': "assets/images/berry.png",  # NEW: dedicated sprite
            'Wood': "assets/images/jungleWood.png",
            'Stone': "assets/images/stone_item.png",  # NEW: dedicated sprite
            'Grass': "assets/images/grass.png",
            'Chicken Meat': "assets/images/chickenMeat.png",  # NEW: meat sprite
            'Bear Meat': "assets/images/bearMeat.png",  # NEW: meat sprite
            'Deer Meat': "assets/images/deerMeat.png"  # NEW: meat sprite
        }
        
        for entity_type, path in entity_sprite_paths.items():
            try:
                sprite = pygame.image.load(path)
                # Scale sprites to tile size
                self.entity_sprites[entity_type] = pygame.transform.scale(
                    sprite,
                    (self.tile_size, self.tile_size)
                )
            except (pygame.error, FileNotFoundError) as e:
                logger.warning(f"Failed to load entity sprite {path} for {entity_type}: {e}")
                # Don't create fallback, will use colored squares as before
        
        # Biome colors (fallback only - prefer server-provided colors)
        # These RGB values match the server's hex color definitions as fallback
        self.biome_colors_fallback = {
            "Grassland": (144, 238, 144),  # #90EE90
            "Forest": (34, 139, 34),       # #228B22
            "Desert": (244, 164, 96),      # #F4A460
            "Tundra": (224, 255, 255),     # #E0FFFF
            "Mountain": (128, 128, 128),   # #808080
            "Swamp": (85, 107, 47)         # #556B2F
        }
        
        # Resource/hazard indicators
        self.resource_color = (255, 215, 0)  # Gold for resources
        self.hazard_color = (255, 0, 0)      # Red for hazards
        self.grid_color = (50, 50, 50)       # Grid line color
        self.unknown_biome_color = (100, 100, 100)  # Fallback for unknown biomes
        
        logger.debug("ServerBackedWorldScreen initialized")
        
    def initialize(self):
        """Initialize the world screen."""
        logger.info("Initializing world screen")
        self.energyBar = EnergyBar(self.graphik, self.player)
        self.status.set("entered the world (server-backed)")
        
        # Fetch initial player state from server
        try:
            logger.debug("Fetching initial player state from server")
            self.player_data = self.api_client.get_player()
            logger.info(f"Player state fetched: energy={self.player_data.get('energy')}, direction={self.player_data.get('direction')}")
            self._updatePlayerFromServerData(self.player_data)
        except Exception as e:
            logger.error(f"Failed to fetch player state: {e}", exc_info=True)
            print(f"Failed to fetch player state: {e}")
            self.status.set(f"Server error: {e}")
        
        # Load initial room with simple retry mechanism
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"Loading initial room (0, 0), attempt {attempt}/{max_retries}")
                self.load_room(0, 0)
                break
            except Exception as e:
                logger.error(f"Failed to load initial room on attempt {attempt}: {e}", exc_info=True)
                print(f"Failed to load room (attempt {attempt}): {e}")
                if attempt < max_retries:
                    # Inform the player that a retry will be attempted
                    self.status.set(f"Room load failed (attempt {attempt}/{max_retries}), retrying...")
                    # Small delay before retrying to avoid hammering the server
                    pygame.time.wait(500)
                else:
                    # Final failure message after all retries
                    self.status.set(f"Room load failed after {max_retries} attempts: {e}")
    
    def _updatePlayerFromServerData(self, player_data):
        """Update local player object from server data."""
        if not player_data:
            logger.warning("No player data to update")
            return
        
        # Update player energy
        energy = player_data.get('energy', 100.0)
        logger.debug(f"Updating player energy: {energy}")
        self.player.setEnergy(energy)
        
        # Update player direction
        direction = player_data.get('direction', -1)
        if direction >= 0:
            logger.debug(f"Updating player direction: {direction}")
            self.player.setDirection(direction)
        
        # Update player inventory from server data
        inventory_data = player_data.get('inventory', {})
        self._updateInventoryFromServerData(inventory_data)
    
    def _updateInventoryFromServerData(self, inventory_data):
        """Update player inventory from server data.
        
        Synchronizes the client's inventory with the authoritative server state.
        Creates item objects from server item names and restores inventory slots.
        """
        if not inventory_data:
            logger.debug("No inventory data to sync")
            return
        
        slots_data = inventory_data.get('slots', [])
        selected_slot = inventory_data.get('selectedSlotIndex', 0)
        
        logger.info(f"Syncing inventory: {len(slots_data)} slots, {inventory_data.get('numItems', 0)} total items")
        
        # Map server item names to client item classes
        item_name_to_class = {
            'Apple': Apple,
            'Banana': Banana,
            'Berry': Berry,
            'Stone': Stone,
            'CoalOre': CoalOre,
            'IronOre': IronOre,
            'Wood': Wood,
            'OakWood': OakWood,
            'JungleWood': JungleWood,
            'Grass': Grass,
            'Leaves': Leaves,
            'Chicken': Chicken,
            'Bear': Bear,
            'Deer': Deer,
            'Chicken Meat': ChickenMeat,
            'Bear Meat': BearMeat,
            'Deer Meat': DeerMeat,
        }
        
        # Clear current inventory
        self.player.getInventory().clear()
        
        # Restore each slot from server data
        for slot_index, slot_data in enumerate(slots_data):
            if slot_data.get('empty', True):
                continue
                
            item_name = slot_data.get('itemName')
            num_items = slot_data.get('numItems', 0)
            
            if not item_name or num_items <= 0:
                continue
            
            # Get the item class
            item_class = item_name_to_class.get(item_name)
            if not item_class:
                logger.warning(f"Unknown item type from server: {item_name}")
                continue
            
            # Add items to this slot
            inventory_slot = self.player.getInventory().getInventorySlots()[slot_index]
            for _ in range(num_items):
                item = item_class()
                inventory_slot.add(item)
            
            logger.debug(f"Restored slot {slot_index}: {num_items}x {item_name}")
        
        # Set selected slot
        self.player.getInventory().setSelectedInventorySlotIndex(selected_slot)
        logger.info(f"Inventory sync complete: {self.player.getInventory().getNumItems()} items restored")
    
    def movePlayer(self, direction: int):
        """Send move action to server."""
        direction_names = ["up", "left", "down", "right"]
        logger.debug(f"movePlayer called: direction={direction} ({direction_names[direction]})")
        
        if self.player.isCrouching():
            logger.debug("Movement blocked - player is crouching")
            return
        
        try:
            logger.debug(f"Sending move action to server: direction={direction}")
            self.player_data = self.api_client.perform_player_action(
                "move",
                direction=direction
            )
            logger.info(f"Move successful: new position from server, moving={self.player_data.get('moving')}")
            self._updatePlayerFromServerData(self.player_data)
            
            self.status.set(f"Moving {direction_names[direction]}")
        except Exception as e:
            logger.error(f"Failed to move player: {e}", exc_info=True)
            print(f"Failed to move: {e}")
            self.status.set(f"Move failed: {e}")
    
    def stopPlayer(self):
        """Stop player movement."""
        logger.debug("stopPlayer called")
        try:
            logger.debug("Sending stop action to server")
            self.player_data = self.api_client.perform_player_action("stop")
            logger.info("Stop successful")
            self._updatePlayerFromServerData(self.player_data)
            self.status.set("Stopped")
        except Exception as e:
            logger.error(f"Failed to stop player: {e}", exc_info=True)
            print(f"Failed to stop: {e}")
            self.status.set(f"Stop failed: {e}")
    
    def toggleGathering(self):
        """Toggle gathering state."""
        logger.debug("toggleGathering called")
        try:
            # Safely handle case where player_data may be None
            is_gathering = False
            if self.player_data:
                is_gathering = self.player_data.get('gathering', False)
            
            logger.debug(f"Current gathering state: {is_gathering}, toggling to: {not is_gathering}")
            self.player_data = self.api_client.perform_player_action(
                "gather",
                gathering=not is_gathering
            )
            logger.info(f"Gathering toggle successful: now gathering={not is_gathering}")
            self._updatePlayerFromServerData(self.player_data)
            status = "gathering" if not is_gathering else "stopped gathering"
            self.status.set(f"Player {status}")
        except Exception as e:
            logger.error(f"Failed to toggle gathering: {e}", exc_info=True)
            print(f"Failed to toggle gathering: {e}")
            self.status.set(f"Gathering toggle failed: {e}")
    
    def handleKeyDownEvent(self, key):
        """Handle key press events."""
        logger.debug(f"Key down event: {key}")
        if key == pygame.K_ESCAPE:
            logger.info("ESC pressed - opening options menu")
            # Save session before navigating to menu
            try:
                self.api_client.save_session(self.session_id)
                logger.info("Session saved before menu navigation")
            except Exception as e:
                logger.warning(f"Failed to save session before menu navigation: {e}")
            self.nextScreen = ScreenType.OPTIONS_SCREEN
            self.changeScreen = True
        # Regular arrow key movement
        elif key == pygame.K_w or key == pygame.K_UP:
            self.movePlayer(0)
        elif key == pygame.K_a or key == pygame.K_LEFT:
            self.movePlayer(1)
        elif key == pygame.K_s or key == pygame.K_DOWN:
            self.movePlayer(2)
        elif key == pygame.K_d or key == pygame.K_RIGHT:
            self.movePlayer(3)
        elif key == pygame.K_SPACE:
            self.stopPlayer()
        elif key == pygame.K_i:
            logger.info("I pressed - opening inventory")
            self.nextScreen = ScreenType.INVENTORY_SCREEN
            self.changeScreen = True
        elif key == pygame.K_LSHIFT:
            logger.debug("Shift key pressed - enabling run")
            try:
                self.player_data = self.api_client.perform_player_action(
                    "run",
                    running=True
                )
                self._updatePlayerFromServerData(self.player_data)
                self.status.set("Running")
            except Exception as e:
                logger.error(f"Failed to enable run: {e}")
                self.status.set(f"Run failed: {e}")
        elif key == pygame.K_LCTRL:
            logger.debug("Ctrl key pressed - toggling crouch")
            try:
                # Toggle crouching state
                current_crouching = self.player.isCrouching()
                self.player_data = self.api_client.perform_player_action(
                    "crouch",
                    crouching=not current_crouching
                )
                self._updatePlayerFromServerData(self.player_data)
                self.player.setCrouching(not current_crouching)
                status = "crouching" if not current_crouching else "standing"
                self.status.set(f"Player {status}")
            except Exception as e:
                logger.error(f"Failed to toggle crouch: {e}", exc_info=True)
                self.status.set(f"Crouch toggle failed: {e}")
        elif key == pygame.K_F3:
            # toggle debug mode
            self.config.debug = not self.config.debug
            logger.info(f"Debug mode toggled: {self.config.debug}")
        # Number keys for inventory selection
        elif key == pygame.K_1:
            self._selectInventorySlot(0)
        elif key == pygame.K_2:
            self._selectInventorySlot(1)
        elif key == pygame.K_3:
            self._selectInventorySlot(2)
        elif key == pygame.K_4:
            self._selectInventorySlot(3)
        elif key == pygame.K_5:
            self._selectInventorySlot(4)
        elif key == pygame.K_6:
            self._selectInventorySlot(5)
        elif key == pygame.K_7:
            self._selectInventorySlot(6)
        elif key == pygame.K_8:
            self._selectInventorySlot(7)
        elif key == pygame.K_9:
            self._selectInventorySlot(8)
        elif key == pygame.K_0:
            self._selectInventorySlot(9)
        elif key == pygame.K_e:
            logger.debug("E key pressed - consuming food")
            self._consumeFood()
    
    def _selectInventorySlot(self, slot_index: int):
        """Select an inventory slot."""
        try:
            logger.debug(f"Selecting inventory slot {slot_index}")
            inventory_response = self.api_client.select_inventory_slot(slot_index)
            
            # Update only the inventory portion of player_data to preserve position data
            # This prevents the player from teleporting when switching slots
            if inventory_response:
                if not self.player_data:
                    # If player_data is None, initialize it with just inventory
                    self.player_data = {'inventory': inventory_response}
                else:
                    # Update only the inventory portion to preserve other fields
                    self.player_data['inventory'] = inventory_response
            
            # Only update the selected slot index without rebuilding inventory
            # This prevents the hotbar from flickering when switching slots
            if inventory_response:
                selected_index = inventory_response.get('selectedSlotIndex', slot_index)
                self.player.getInventory().setSelectedInventorySlotIndex(selected_index)
            
            # Show item name in status, or "Empty slot" if no item
            inventory_slot = self.player.getInventory().getInventorySlots()[slot_index]
            if not inventory_slot.isEmpty():
                item_name = inventory_slot.getContents()[0].getName()
                self.status.set(f"Selected {item_name}")
            else:
                self.status.set(f"Selected empty slot")
        except Exception as e:
            logger.error(f"Failed to select slot {slot_index}: {e}", exc_info=True)
            self.status.set(f"Slot selection failed")
    
    def _consumeFood(self):
        """Consume food from inventory."""
        logger.debug("Attempting to consume food")
        try:
            # Ensure we have player data before attempting to consume food
            if not self.player_data:
                logger.warning("Cannot consume food - no player data available")
                self.status.set("No player data available")
                return

            # For now, just try to consume first item (simplified)
            inventory_data = self.player_data.get('inventory') or {}
            slots = inventory_data.get('slots') or []
            
            logger.debug(f"Checking inventory slots: {len(slots)} total")
            for i, slot in enumerate(slots):
                if not slot.get('empty', True):
                    item_name = slot.get('itemName')
                    if item_name:
                        logger.info(f"Found consumable item in slot {i}: {item_name}")
                        logger.debug(f"Calling API: perform_player_action('consume', item_name={item_name})")
                        self.player_data = self.api_client.perform_player_action(
                            "consume",
                            item_name=item_name
                        )
                        logger.info(f"Food consumed successfully: {item_name}")
                        self._updatePlayerFromServerData(self.player_data)
                        self.status.set(f"Consumed {item_name}")
                        return
            
            logger.debug("No consumable food found in inventory")
            self.status.set("No food to consume")
        except Exception as e:
            logger.error(f"Failed to consume food: {e}", exc_info=True)
            print(f"Failed to consume: {e}")
            self.status.set(f"Consume failed: {e}")
    
    def handleMouseButtonDown(self, event):
        """Handle mouse button press events."""
        if event.button == 1:  # Left click - gather
            self.mouse_button_held[1] = True
            logger.debug(f"Left click at position ({event.pos[0]}, {event.pos[1]})")
            self._performGatherAt(event.pos[0], event.pos[1])
        elif event.button == 3:  # Right click - place
            self.mouse_button_held[3] = True
            logger.debug(f"Right click at position ({event.pos[0]}, {event.pos[1]})")
            self._performPlaceAt(event.pos[0], event.pos[1])
    
    def handleMouseButtonUp(self, event):
        """Handle mouse button release events."""
        if event.button == 1:
            self.mouse_button_held[1] = False
            self.last_gather_tile = None
        elif event.button == 3:
            self.mouse_button_held[3] = False
    
    def _performGatherAt(self, screen_x: int, screen_y: int):
        """Perform gather action at screen coordinates."""
        # Convert screen coordinates to tile coordinates
        tile_coords = self._screen_to_tile_coords(screen_x, screen_y)
        if tile_coords:
            tile_x, tile_y = tile_coords
            logger.debug(f"Gathering at tile ({tile_x}, {tile_y})")
            # Trigger gathering action at the clicked tile
            try:
                self.player_data = self.api_client.perform_player_action(
                    "gather",
                    gathering=True,
                    tile_x=tile_x,
                    tile_y=tile_y
                )
                self._updatePlayerFromServerData(self.player_data)
                self.last_gather_tile = (tile_x, tile_y)
                # Don't show status for every gather to avoid spam
                if not self.config.debug:
                    self.status.set("Gathered")
                else:
                    self.status.set(f"Gathered at ({tile_x}, {tile_y})")
            except Exception as e:
                logger.error(f"Failed to gather: {e}", exc_info=True)
                if self.config.debug:
                    self.status.set(f"Gather failed")
    
    def _performPlaceAt(self, screen_x: int, screen_y: int):
        """Perform place action at screen coordinates."""
        # Convert screen coordinates to tile coordinates
        tile_coords = self._screen_to_tile_coords(screen_x, screen_y)
        if tile_coords:
            tile_x, tile_y = tile_coords
            logger.debug(f"Placing on tile ({tile_x}, {tile_y})")
            # Trigger placing action at the clicked tile
            try:
                self.player_data = self.api_client.perform_player_action(
                    "place",
                    placing=True,
                    tile_x=tile_x,
                    tile_y=tile_y
                )
                self._updatePlayerFromServerData(self.player_data)
                if not self.config.debug:
                    self.status.set("Placed")
                else:
                    self.status.set(f"Placed at ({tile_x}, {tile_y})")
            except Exception as e:
                logger.error(f"Failed to place: {e}", exc_info=True)
                if self.config.debug:
                    self.status.set(f"Place failed")
    
    def _screen_to_tile_coords(self, screen_x: int, screen_y: int):
        """
        Convert screen coordinates to tile coordinates within the current room.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            
        Returns:
            Tuple of (tile_x, tile_y) or None if outside the world view
        """
        if not self.current_room:
            return None
        
        width = self.current_room.get('width', 20)
        height = self.current_room.get('height', 20)
        
        # Calculate world view position (centered on screen)
        display_width = self.graphik.getGameDisplay().get_width()
        display_height = self.graphik.getGameDisplay().get_height()
        
        world_pixel_width = width * self.tile_size
        world_pixel_height = height * self.tile_size
        
        world_view_x = (display_width - world_pixel_width) // 2
        world_view_y = (display_height - world_pixel_height) // 2
        
        # Convert to tile coordinates
        tile_x = (screen_x - world_view_x) // self.tile_size
        tile_y = (screen_y - world_view_y) // self.tile_size
        
        # Check if within bounds
        if 0 <= tile_x < width and 0 <= tile_y < height:
            return (tile_x, tile_y)
        
        return None
    
    def _navigate_to_room(self, new_x: int, new_y: int, direction: str):
        """
        Navigate to a room in the specified direction.
        
        Args:
            new_x: X coordinate of the target room
            new_y: Y coordinate of the target room
            direction: Direction name for logging (e.g., "north", "south")
        """
        logger.info(f"Navigating to room {direction}: ({new_x}, {new_y})")
        if not self.load_room(new_x, new_y):
            logger.error(f"Failed to load room at ({new_x}, {new_y}) when navigating {direction}")
    
    def load_room(self, room_x: int, room_y: int) -> bool:
        """
        Load a room from the server.
        
        Returns:
            bool: True if the room was loaded successfully, False otherwise.
        """
        try:
            logger.info(f"Loading room ({room_x}, {room_y})")
            # Fetch room data from the server first, without mutating state
            room = self.api_client.get_room(room_x, room_y)
            
            # Treat a missing/invalid room as a load failure
            if not room:
                raise ValueError(f"Server returned no data for room ({room_x}, {room_y})")
            
            # Only update current room state after a successful, valid load
            self.current_room = room
            self.current_room_x = room_x
            self.current_room_y = room_y
            logger.debug(f"Room loaded successfully: {len(self.current_room.get('tiles', []))} tiles")
            # Only show "Loaded room" message in debug mode
            if self.config.debug:
                self.status.set(f"Loaded room ({room_x}, {room_y})")
            return True
        except Exception as e:
            # Ensure we do not leave a partially loaded or inconsistent room in state
            # Note: We do NOT set current_room to None to keep the previous room visible
            logger.error(f"Failed to load room ({room_x}, {room_y}): {e}", exc_info=True)
            print(f"Failed to load room: {e}")
            self.status.set(f"Room load failed: {e}")
            return False
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """
        Convert hex color string to RGB tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#228B22" or "228B22")
            
        Returns:
            tuple: RGB color as (r, g, b)
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Validate length
        if len(hex_color) != 6:
            logger.warning(f"Invalid hex color length '{hex_color}' (expected 6 characters)")
            return self.unknown_biome_color
        
        # Convert hex to RGB
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid hex color '{hex_color}': {e}")
            return self.unknown_biome_color
    
    def render_world(self):
        """Render the current room as a tile map with entities."""
        if not self.current_room:
            return
        
        tiles = self.current_room.get('tiles', [])
        entities = self.current_room.get('entities', [])
        width = self.current_room.get('width', 32)
        height = self.current_room.get('height', 32)
        
        # Calculate world view position (centered on screen)
        display_width = self.graphik.getGameDisplay().get_width()
        display_height = self.graphik.getGameDisplay().get_height()
        
        world_pixel_width = width * self.tile_size
        world_pixel_height = height * self.tile_size
        
        world_view_x = (display_width - world_pixel_width) // 2
        world_view_y = (display_height - world_pixel_height) // 2
        
        # Draw each tile
        for tile_data in tiles:
            tile_x = tile_data.get('x', 0)
            tile_y = tile_data.get('y', 0)
            biome = tile_data.get('biome', 'Grassland')
            biome_color_hex = tile_data.get('biomeColor')  # Server-provided hex color
            has_resource = tile_data.get('resourceType') is not None
            has_hazard = tile_data.get('hasHazard', False)
            
            # Calculate screen position
            screen_x = world_view_x + tile_x * self.tile_size
            screen_y = world_view_y + tile_y * self.tile_size
            
            # Use grass sprite for Grassland biome, otherwise use color
            if biome == 'Grassland' and 'Grass' in self.entity_sprites:
                self.graphik.getGameDisplay().blit(
                    self.entity_sprites['Grass'],
                    (screen_x, screen_y)
                )
            else:
                # Get biome color - prefer server-provided hex color, fall back to hardcoded
                if biome_color_hex:
                    # Convert hex color string to RGB tuple
                    color = self._hex_to_rgb(biome_color_hex)
                else:
                    # Fallback to hardcoded colors if server doesn't provide one
                    color = self.biome_colors_fallback.get(biome, self.unknown_biome_color)
                
                # Draw tile
                pygame.draw.rect(
                    self.graphik.getGameDisplay(),
                    color,
                    (screen_x, screen_y, self.tile_size, self.tile_size)
                )
            
            # Draw resource indicator (small circle)
            if has_resource:
                center_x = screen_x + self.tile_size // 2
                center_y = screen_y + self.tile_size // 2
                pygame.draw.circle(
                    self.graphik.getGameDisplay(),
                    self.resource_color,
                    (center_x, center_y),
                    3
                )
            
            # Draw hazard indicator (X mark)
            if has_hazard:
                pygame.draw.line(
                    self.graphik.getGameDisplay(),
                    self.hazard_color,
                    (screen_x + 2, screen_y + 2),
                    (screen_x + self.tile_size - 2, screen_y + self.tile_size - 2),
                    2
                )
                pygame.draw.line(
                    self.graphik.getGameDisplay(),
                    self.hazard_color,
                    (screen_x + self.tile_size - 2, screen_y + 2),
                    (screen_x + 2, screen_y + self.tile_size - 2),
                    2
                )
        
        # Draw entities
        for entity in entities:
            location_id = entity.get('locationId', '')
            if not location_id:
                continue
            
            # Parse location: "roomX,roomY,tileX,tileY"
            parts = location_id.split(',')
            if len(parts) >= 4:
                entity_tile_x = int(parts[2])
                entity_tile_y = int(parts[3])
                
                # Calculate screen position
                screen_x = world_view_x + entity_tile_x * self.tile_size
                screen_y = world_view_y + entity_tile_y * self.tile_size
                
                # Draw entity based on type
                entity_type = entity.get('type', '')
                entity_name = entity.get('name', '')
                
                # Try to use sprite first, fall back to colored square
                if entity_type in self.entity_sprites:
                    self.graphik.getGameDisplay().blit(
                        self.entity_sprites[entity_type],
                        (screen_x, screen_y)
                    )
                else:
                    # Log unknown entity types explicitly
                    if entity_type not in ['', 'Unknown']:
                        logger.warning(f"Unknown entity type encountered: '{entity_type}' (name: '{entity_name}'). Using colored square fallback. Consider adding sprite mapping.")
                    
                    # Fall back to colored square
                    entity_color = self._get_entity_color(entity_type)
                    
                    # Draw entity as a filled rectangle with border
                    pygame.draw.rect(
                        self.graphik.getGameDisplay(),
                        entity_color,
                        (screen_x + 2, screen_y + 2, self.tile_size - 4, self.tile_size - 4)
                    )
                    
                    # Draw border for solid entities
                    if entity.get('solid', False):
                        pygame.draw.rect(
                            self.graphik.getGameDisplay(),
                            (0, 0, 0),
                            (screen_x + 2, screen_y + 2, self.tile_size - 4, self.tile_size - 4),
                            2
                        )
        
        # Draw player position indicator if player position is available
        if self.player_data:
            player_room_x = self.player_data.get('roomX', 0)
            player_room_y = self.player_data.get('roomY', 0)
            player_tile_x = self.player_data.get('tileX', 0)
            player_tile_y = self.player_data.get('tileY', 0)
            
            # Only draw if player is in the current room
            if player_room_x == self.current_room_x and player_room_y == self.current_room_y:
                screen_x = world_view_x + player_tile_x * self.tile_size
                screen_y = world_view_y + player_tile_y * self.tile_size
                
                # Draw player sprite based on direction
                direction = self.player_data.get('direction', -1)
                last_direction = self.player_data.get('lastDirection', 2)  # Default to down
                
                # Use last direction if not moving
                display_direction = direction if direction >= 0 else last_direction
                if display_direction < 0:
                    display_direction = 2  # Default to down
                
                # Draw the player sprite
                if display_direction in self.player_sprites:
                    self.graphik.getGameDisplay().blit(
                        self.player_sprites[display_direction],
                        (screen_x, screen_y)
                    )
        
        # Draw grid lines
        for x in range(width + 1):
            start_x = world_view_x + x * self.tile_size
            pygame.draw.line(
                self.graphik.getGameDisplay(),
                self.grid_color,
                (start_x, world_view_y),
                (start_x, world_view_y + height * self.tile_size),
                1
            )
        
        for y in range(height + 1):
            start_y = world_view_y + y * self.tile_size
            pygame.draw.line(
                self.graphik.getGameDisplay(),
                self.grid_color,
                (world_view_x, start_y),
                (world_view_x + width * self.tile_size, start_y),
                1
            )
        
        # Draw room coordinates label
        font = pygame.font.Font(None, 24)
        room_label = font.render(
            f"Room: ({self.current_room_x}, {self.current_room_y})",
            True,
            (255, 255, 255)
        )
        self.graphik.getGameDisplay().blit(room_label, (world_view_x, world_view_y - 25))
    
    def _get_entity_color(self, entity_type: str) -> tuple:
        """Get color for entity type visualization."""
        # Wildlife - shades of brown/red
        if entity_type == 'Bear':
            return (139, 69, 19)  # Brown
        elif entity_type == 'Deer':
            return (210, 180, 140)  # Tan
        elif entity_type == 'Chicken':
            return (255, 228, 196)  # Light tan
        # Interactive objects - shades of green/gray
        elif entity_type == 'Tree':
            return (34, 139, 34)  # Forest green
        elif entity_type == 'Rock':
            return (128, 128, 128)  # Gray
        elif entity_type == 'Bush':
            return (85, 107, 47)  # Dark olive green
        # Resources - shades of yellow/orange
        elif entity_type == 'Apple':
            return (255, 0, 0)  # Red
        elif entity_type == 'Berry':
            return (138, 43, 226)  # Purple
        elif entity_type == 'Wood':
            return (160, 82, 45)  # Sienna
        elif entity_type == 'Stone':
            return (169, 169, 169)  # Dark gray
        # Meat items - shades of red/pink
        elif entity_type == 'Chicken Meat':
            return (255, 182, 193)  # Light pink
        elif entity_type == 'Bear Meat':
            return (178, 34, 34)  # Firebrick
        elif entity_type == 'Deer Meat':
            return (220, 20, 60)  # Crimson
        # Default
        return (200, 200, 200)
    
    def handleKeyUpEvent(self, key):
        """Handle key release events."""
        logger.debug(f"Key up event: {key}")
        if (key == pygame.K_w or key == pygame.K_UP) and self.player.getDirection() == 0:
            logger.debug("Up key released - stopping player")
            self.stopPlayer()
        elif (key == pygame.K_a or key == pygame.K_LEFT) and self.player.getDirection() == 1:
            logger.debug("Left key released - stopping player")
            self.stopPlayer()
        elif (key == pygame.K_s or key == pygame.K_DOWN) and self.player.getDirection() == 2:
            logger.debug("Down key released - stopping player")
            self.stopPlayer()
        elif (key == pygame.K_d or key == pygame.K_RIGHT) and self.player.getDirection() == 3:
            logger.debug("Right key released - stopping player")
            self.stopPlayer()
        elif key == pygame.K_LSHIFT:
            logger.debug("Shift key released - disabling run")
            try:
                self.player_data = self.api_client.perform_player_action(
                    "run",
                    running=False
                )
                self._updatePlayerFromServerData(self.player_data)
                self.status.set("Stopped running")
            except Exception as e:
                logger.error(f"Failed to disable run: {e}")
                self.status.set(f"Stop run failed: {e}")
        elif key == pygame.K_LCTRL:
            logger.debug("Ctrl key released (crouch changes handled server-side)")
            # Crouching state changes are handled by the server in a server-backed world.
            # Do not modify crouch state locally to avoid client-server desynchronization.
            pass
    
    def updateTick(self):
        """Update game tick on server and refresh player and entity state."""
        try:
            logger.debug(f"Updating tick on server (current: {self.server_tick})")
            session_data = self.api_client.update_tick()
            self.server_tick = session_data.get('currentTick', self.server_tick)
            logger.debug(f"Tick updated: {self.server_tick}")
            
            # Fetch updated player data after tick to get new position
            self.player_data = self.api_client.get_player()
            self._updatePlayerFromServerData(self.player_data)
            
            # Always reload current room to get updated entity positions
            if self.player_data:
                player_room_x = self.player_data.get('roomX', 0)
                player_room_y = self.player_data.get('roomY', 0)
                # Reload room every tick to show entity movements
                self.load_room(player_room_x, player_room_y)
        except Exception as e:
            logger.error(f"Failed to update tick: {e}", exc_info=True)
            print(f"Failed to update tick: {e}")
            # Inform the user via the status message as well
            self.status.set("Failed to update server tick")
    
    def draw(self):
        """Draw the world screen."""
        # Clear screen with a nice background
        self.graphik.getGameDisplay().fill((20, 20, 30))  # Dark background
        
        # Render world first (as background) - this takes up most of the screen now
        self.render_world()
        
        # Draw energy bar (top of screen)
        self.energyBar.draw()
        
        # Draw inventory preview (bottom of screen)
        self._drawInventoryPreview()
        
        # Draw status bar
        self.status.draw()
        
        # Draw debug info if enabled
        if self.config.debug:
            self._drawDebugInfo()
        
        pygame.display.update()
    
    def _drawInventoryPreview(self):
        """Draw inventory preview at bottom of screen."""
        display_width = self.graphik.getGameDisplay().get_width()
        display_height = self.graphik.getGameDisplay().get_height()
        
        # Position at bottom center - larger slots for better visibility
        # Moved up to avoid overlapping with energy bar (which is at display_height - ~15)
        slot_size = 60
        spacing = 5
        
        # Get actual inventory slots from player inventory (first 10 for hotbar)
        inventory_slots = self.player.getInventory().getInventorySlots()[:10]
        
        total_width = len(inventory_slots) * (slot_size + spacing)
        start_x = display_width // 2 - total_width // 2
        start_y = display_height - 100  # Moved from -80 to -100 to avoid energy bar overlap
        
        # Draw background bar
        bar_padding = 10
        pygame.draw.rect(
            self.graphik.getGameDisplay(),
            (40, 40, 40),
            (start_x - bar_padding, start_y - bar_padding, 
             total_width + bar_padding * 2, slot_size + bar_padding * 2)
        )
        
        # Draw slots
        small_font = pygame.font.Font(None, 18)
        large_font = pygame.font.Font(None, 32)
        for i, inventory_slot in enumerate(inventory_slots):
            x = start_x + i * (slot_size + spacing)
            
            # Draw slot background
            if inventory_slot.isEmpty():
                color = (80, 80, 80)
                pygame.draw.rect(
                    self.graphik.getGameDisplay(),
                    color,
                    (x, start_y, slot_size, slot_size)
                )
            else:
                # Draw item texture as background
                item = inventory_slot.getContents()[0]
                try:
                    image = item.getImage()
                    scaled_image = pygame.transform.scale(image, (slot_size, slot_size))
                    self.graphik.getGameDisplay().blit(scaled_image, (x, start_y))
                except (pygame.error, FileNotFoundError, AttributeError) as e:
                    # Fallback to grey background if texture can't be loaded
                    logger.warning(f"Failed to load item texture for hotbar slot {i}: {e}")
                    color = (120, 120, 120)
                    pygame.draw.rect(
                        self.graphik.getGameDisplay(),
                        color,
                        (x, start_y, slot_size, slot_size)
                    )
            
            # Draw border
            pygame.draw.rect(
                self.graphik.getGameDisplay(),
                (60, 60, 60),
                (x, start_y, slot_size, slot_size),
                2
            )
            
            # Draw item count in bottom right corner if not empty
            if not inventory_slot.isEmpty():
                num_items = inventory_slot.getNumItems()
                
                # Draw count in bottom right corner with small background for visibility
                count_text = str(num_items)
                count_surface = small_font.render(count_text, True, (255, 255, 255))
                text_width = count_surface.get_width()
                text_height = count_surface.get_height()
                
                # Draw background for text (solid black for visibility)
                text_bg_padding = 2
                pygame.draw.rect(
                    self.graphik.getGameDisplay(),
                    (0, 0, 0),
                    (x + slot_size - text_width - text_bg_padding * 2,
                     start_y + slot_size - text_height - text_bg_padding * 2,
                     text_width + text_bg_padding * 2,
                     text_height + text_bg_padding * 2)
                )
                
                # Draw the count text
                self.graphik.getGameDisplay().blit(
                    count_surface,
                    (x + slot_size - text_width - text_bg_padding, 
                     start_y + slot_size - text_height - text_bg_padding)
                )
            
            # Draw selection indicator (yellow border)
            selected_index = self.player.getInventory().getSelectedInventorySlotIndex()
            if i == selected_index:
                pygame.draw.rect(
                    self.graphik.getGameDisplay(),
                    (255, 255, 0),
                    (x, start_y, slot_size, slot_size),
                    4
                )
    
    def _drawControls(self):
        """Draw controls help text."""
        display_width = self.graphik.getGameDisplay().get_width()
        
        font = pygame.font.Font(None, 20)
        controls = [
            "WASD/Arrows: Move",
            "Space: Stop",
            "Click: Gather",
            "I: Inventory",
            "E: Eat",
            "1-9/0: Select Slot",
            "ESC: Menu",
        ]
        
        x = display_width - 220
        y = 100
        
        for control in controls:
            surface = font.render(control, True, (200, 200, 200))
            self.graphik.getGameDisplay().blit(surface, (x, y))
            y += 25
    
    def _drawDebugInfo(self):
        """Draw debug information."""
        display_width = self.graphik.getGameDisplay().get_width()
        display_height = self.graphik.getGameDisplay().get_height()
        
        font = pygame.font.Font(None, 20)
        debug_texts = [
            f"Tick: {self.tickCounter.getTick()}",
            f"Server Tick: {self.server_tick}",
            f"Session: {self.session_id[:8]}...",
        ]
        
        x = display_width - 200
        y = display_height - 100
        
        for text in debug_texts:
            surface = font.render(text, True, (255, 255, 0))
            self.graphik.getGameDisplay().blit(surface, (x, y))
            y += 20
    
    def run(self):
        """Main game loop."""
        logger.info("Starting ServerBackedWorldScreen main loop")
        tick_counter = 0
        tick_update_frequency = 3  # Update server tick every 3 frames (~20 ticks/sec at 60 FPS, matches server 18 ticks/sec)
        
        clock = pygame.time.Clock()
        target_fps = 60
        
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.info("Quit event received")
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)
                elif event.type == pygame.KEYUP:
                    self.handleKeyUpEvent(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseButtonDown(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handleMouseButtonUp(event)
            
            # Handle continuous gathering if mouse is held
            if self.mouse_button_held[1]:
                self.gather_cooldown_frames += 1
                if self.gather_cooldown_frames >= self.gather_cooldown_max:
                    # Get current mouse position
                    mouse_pos = pygame.mouse.get_pos()
                    self._performGatherAt(mouse_pos[0], mouse_pos[1])
                    self.gather_cooldown_frames = 0
            else:
                self.gather_cooldown_frames = 0
            
            # Update tick periodically
            tick_counter += 1
            if tick_counter >= tick_update_frequency:
                self.updateTick()
                tick_counter = 0
            
            # Check status expiration
            self.status.checkForExpiration(self.tickCounter.getTick())
            
            # Draw
            self.draw()
            
            # Increment local tick counter
            self.tickCounter.incrementTick()
            
            # Control frame rate
            clock.tick(target_fps)
        
        logger.info(f"Exiting ServerBackedWorldScreen, next screen: {self.nextScreen}")
        self.changeScreen = False
        return self.nextScreen
