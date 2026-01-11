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

        NOTE: The server inventory structure is currently different from the local
        representation, and full synchronization logic has not yet been defined.
        To avoid accidentally wiping the client's inventory without being able to
        faithfully reconstruct it, this method is intentionally a no-op until the
        inventory model between client and server is finalized.
        """
        if not inventory_data:
            logger.debug("No inventory data to sync")
            return
        
        logger.debug(f"Inventory sync skipped (intentional no-op): {inventory_data.get('numItems', 0)} items on server")
        # TODO: Implement non-destructive inventory synchronization once the server's
        #       inventory/item model is stable and the local inventory API is aligned.
        #       For now, we avoid clearing or modifying the existing inventory.
    
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
            self.nextScreen = ScreenType.OPTIONS_SCREEN
            self.changeScreen = True
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
        elif key == pygame.K_g:
            self.toggleGathering()
        elif key == pygame.K_i:
            logger.info("I pressed - opening inventory")
            self.nextScreen = ScreenType.INVENTORY_SCREEN
            self.changeScreen = True
        elif key == pygame.K_LSHIFT:
            logger.debug("Shift key pressed (speed changes handled server-side)")
            # Movement speed changes are handled by the server in a server-backed world.
            # Do not modify player speed locally to avoid client-server desynchronization.
            pass
        elif key == pygame.K_LCTRL:
            logger.debug("Ctrl key pressed (crouch changes handled server-side)")
            # Crouching state changes are handled by the server in a server-backed world.
            # Do not modify crouch state locally to avoid client-server desynchronization.
            pass
        elif key == pygame.K_F3:
            # toggle debug mode
            self.config.debug = not self.config.debug
            logger.info(f"Debug mode toggled: {self.config.debug}")
        # Test keys for adding items (temporary)
        elif key == pygame.K_1:
            logger.debug("Test key 1 - adding apple")
            self._addTestItem("apple")
        elif key == pygame.K_2:
            logger.debug("Test key 2 - adding banana")
            self._addTestItem("banana")
        elif key == pygame.K_3:
            logger.debug("Test key 3 - adding stone")
            self._addTestItem("stone")
        elif key == pygame.K_e:
            logger.debug("E key pressed - consuming food")
            self._consumeFood()
    
    def _addTestItem(self, item_name: str):
        """Add test item to inventory (for testing)."""
        logger.debug(f"Adding test item to inventory: {item_name}")
        try:
            logger.debug(f"Calling API: add_item_to_inventory({item_name})")
            self.api_client.add_item_to_inventory(item_name)
            logger.debug("Fetching updated player state")
            self.player_data = self.api_client.get_player()
            logger.info(f"Item added successfully: {item_name}")
            self._updatePlayerFromServerData(self.player_data)
            self.status.set(f"Added {item_name}")
        except Exception as e:
            logger.error(f"Failed to add item {item_name}: {e}", exc_info=True)
            print(f"Failed to add item: {e}")
            self.status.set(f"Failed to add {item_name}")
    
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
            logger.debug("Shift key released (speed changes handled server-side)")
            # Movement speed changes are handled by the server in a server-backed world.
            # Do not modify player speed locally to avoid client-server desynchronization.
            pass
        elif key == pygame.K_LCTRL:
            logger.debug("Ctrl key released (crouch changes handled server-side)")
            # Crouching state changes are handled by the server in a server-backed world.
            # Do not modify crouch state locally to avoid client-server desynchronization.
            pass
    
    def updateTick(self):
        """Update game tick on server."""
        try:
            logger.debug(f"Updating tick on server (current: {self.server_tick})")
            session_data = self.api_client.update_tick()
            self.server_tick = session_data.get('currentTick', self.server_tick)
            logger.debug(f"Tick updated: {self.server_tick}")
        except Exception as e:
            logger.error(f"Failed to update tick: {e}", exc_info=True)
            print(f"Failed to update tick: {e}")
            # Inform the user via the status message as well
            self.status.set("Failed to update server tick")
    
    def draw(self):
        """Draw the world screen."""
        # Clear screen with a nice background
        self.graphik.getGameDisplay().fill((34, 139, 34))  # Forest green background
        
        # Draw title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("Roam (Server-Backed)", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.graphik.getGameDisplay().get_width() // 2, 40))
        self.graphik.getGameDisplay().blit(title, title_rect)
        
        # Draw player visualization (centered)
        display_width = self.graphik.getGameDisplay().get_width()
        display_height = self.graphik.getGameDisplay().get_height()
        
        # Player representation
        player_size = 64
        player_x = display_width // 2 - player_size // 2
        player_y = display_height // 2 - player_size // 2
        
        # Draw player circle
        pygame.draw.circle(
            self.graphik.getGameDisplay(),
            (255, 200, 100),
            (player_x + player_size // 2, player_y + player_size // 2),
            player_size // 2
        )
        
        # Draw direction indicator
        direction = self.player.getDirection()
        if direction >= 0:
            arrow_length = 30
            center_x = player_x + player_size // 2
            center_y = player_y + player_size // 2
            
            if direction == 0:  # Up
                end_x, end_y = center_x, center_y - arrow_length
            elif direction == 1:  # Left
                end_x, end_y = center_x - arrow_length, center_y
            elif direction == 2:  # Down
                end_x, end_y = center_x, center_y + arrow_length
            elif direction == 3:  # Right
                end_x, end_y = center_x + arrow_length, center_y
            
            pygame.draw.line(
                self.graphik.getGameDisplay(),
                (255, 255, 0),
                (center_x, center_y),
                (end_x, end_y),
                5
            )
        
        # Draw player info panel
        info_x = 20
        info_y = 100
        font = pygame.font.Font(None, 28)
        
        info_texts = [
            f"Energy: {self.player.getEnergy():.1f}/{self.player.getTargetEnergy()}",
            f"Direction: {['Up', 'Left', 'Down', 'Right', 'None'][direction] if direction >= 0 else 'None'}",
            f"Moving: {self.player_data.get('moving', False) if self.player_data else False}",
            f"Gathering: {self.player_data.get('gathering', False) if self.player_data else False}",
            f"Crouching: {self.player.isCrouching()}",
        ]
        
        for i, text in enumerate(info_texts):
            surface = font.render(text, True, (255, 255, 255))
            self.graphik.getGameDisplay().blit(surface, (info_x, info_y + i * 35))
        
        # Draw energy bar
        self.energyBar.draw()
        
        # Draw inventory preview
        self._drawInventoryPreview()
        
        # Draw controls help
        self._drawControls()
        
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
        
        # Get inventory data from server
        if not self.player_data:
            return
        
        inventory_data = self.player_data.get('inventory', {})
        slots = inventory_data.get('slots', [])[:10]  # First 10 slots
        
        # Position at bottom center
        slot_size = 50
        spacing = 5
        total_width = len(slots) * (slot_size + spacing)
        start_x = display_width // 2 - total_width // 2
        start_y = display_height - 100
        
        # Draw background bar
        bar_padding = 10
        pygame.draw.rect(
            self.graphik.getGameDisplay(),
            (50, 50, 50),
            (start_x - bar_padding, start_y - bar_padding, 
             total_width + bar_padding * 2, slot_size + bar_padding * 2)
        )
        
        # Draw slots
        font = pygame.font.Font(None, 20)
        for i, slot in enumerate(slots):
            x = start_x + i * (slot_size + spacing)
            
            # Draw slot background
            color = (100, 100, 100) if slot.get('empty', True) else (150, 150, 150)
            pygame.draw.rect(
                self.graphik.getGameDisplay(),
                color,
                (x, start_y, slot_size, slot_size)
            )
            
            # Draw item info if not empty
            if not slot.get('empty', True):
                item_name = slot.get('itemName', '')
                num_items = slot.get('numItems', 0)
                
                # Draw item name (truncated)
                name_surface = font.render(item_name[:8], True, (255, 255, 255))
                self.graphik.getGameDisplay().blit(name_surface, (x + 2, start_y + 2))
                
                # Draw count
                count_surface = font.render(str(num_items), True, (255, 255, 100))
                self.graphik.getGameDisplay().blit(
                    count_surface, 
                    (x + slot_size - 20, start_y + slot_size - 20)
                )
            
            # Draw selection indicator
            selected_index = inventory_data.get('selectedSlotIndex', 0)
            if i == selected_index:
                pygame.draw.rect(
                    self.graphik.getGameDisplay(),
                    (255, 255, 0),
                    (x, start_y, slot_size, slot_size),
                    3
                )
    
    def _drawControls(self):
        """Draw controls help text."""
        display_width = self.graphik.getGameDisplay().get_width()
        
        font = pygame.font.Font(None, 20)
        controls = [
            "WASD/Arrows: Move",
            "Space: Stop",
            "G: Gather",
            "I: Inventory",
            "E: Eat",
            "1/2/3: Add Items (test)",
            "ESC: Menu",
        ]
        
        x = display_width - 200
        y = 100
        
        for control in controls:
            surface = font.render(control, True, (200, 200, 200))
            self.graphik.getGameDisplay().blit(surface, (x, y))
            y += 25
    
    def _drawDebugInfo(self):
        """Draw debug information."""
        display_width = self.graphik.getGameDisplay().get_width()
        
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
        tick_update_frequency = 60  # Update server tick every 60 frames
        
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
        
        logger.info(f"Exiting ServerBackedWorldScreen, next screen: {self.nextScreen}")
        self.changeScreen = False
        return self.nextScreen
