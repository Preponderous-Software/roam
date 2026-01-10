#!/usr/bin/env python3
"""
Roam Client Application
This client application uses the Spring Boot backend for all game logic.
UI rendering and user input handling only.

@author Daniel McCoy Stephenson
"""

import sys
import os
import pygame

# Ensure we can import from current directory (src)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from client.api_client import RoamAPIClient
from config.config import Config
from lib.graphik.src.graphik import Graphik
from ui.status import Status


class RoamClient:
    """
    Client application for Roam that communicates with Spring Boot backend.
    Handles only UI rendering and user input - no business logic.
    """
    
    def __init__(self, config: Config, server_url: str = "http://localhost:8080"):
        """
        Initialize the client application.
        
        Args:
            config: Configuration object
            server_url: URL of the Spring Boot server
        """
        pygame.init()
        pygame.display.set_icon(pygame.image.load("assets/images/player_down.png"))
        
        self.config = config
        self.api_client = RoamAPIClient(server_url)
        self.running = True
        self.session_id = None
        self.player_data = None
        self.current_tick = 0
        
        # Initialize display
        pygame.display.set_caption("Roam Client (Server-Backed)")
        self.game_display = self.initialize_game_display()
        self.graphik = Graphik(self.game_display)
        self.status = Status(self.graphik, None)  # No local tick counter
        
        # Game state
        self.player_direction = -1
        self.player_energy = 100.0
        self.inventory_items = []
        
        # UI settings
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.clock = pygame.time.Clock()
        
    def initialize_game_display(self):
        """Initialize the pygame display."""
        if self.config.fullscreen:
            return pygame.display.set_mode(
                (self.config.displayWidth, self.config.displayHeight), 
                pygame.FULLSCREEN
            )
        else:
            return pygame.display.set_mode(
                (self.config.displayWidth, self.config.displayHeight), 
                pygame.RESIZABLE
            )
    
    def start_session(self):
        """Start a new game session on the server."""
        try:
            session_data = self.api_client.init_session()
            self.session_id = session_data['sessionId']
            self.player_data = session_data['player']
            self.current_tick = session_data['currentTick']
            self.update_local_state_from_player_data()
            self.status.set("Connected to server - Session started")
            return True
        except Exception as e:
            print(f"Failed to start session: {e}")
            self.status.set(f"Connection failed: {e}")
            return False
    
    def update_local_state_from_player_data(self):
        """Update local state from server player data."""
        if self.player_data:
            self.player_energy = self.player_data.get('energy', 100.0)
            self.player_direction = self.player_data.get('direction', -1)
            inventory = self.player_data.get('inventory', {})
            self.inventory_items = []
            for slot in inventory.get('slots', []):
                if not slot.get('empty', True):
                    self.inventory_items.append({
                        'name': slot.get('itemName'),
                        'count': slot.get('numItems', 0)
                    })
    
    def handle_input(self):
        """Handle user input and send to server."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                try:
                    # Movement keys
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        self.move_player(0)  # Up
                    elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.move_player(1)  # Left
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        self.move_player(2)  # Down
                    elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.move_player(3)  # Right
                    
                    # Stop movement
                    elif event.key == pygame.K_SPACE:
                        self.stop_player()
                    
                    # Gathering
                    elif event.key == pygame.K_g:
                        self.toggle_gathering()
                    
                    # Add test items to inventory
                    elif event.key == pygame.K_1:
                        self.add_item("apple")
                    elif event.key == pygame.K_2:
                        self.add_item("banana")
                    elif event.key == pygame.K_3:
                        self.add_item("stone")
                    
                    # Consume food (eat first item)
                    elif event.key == pygame.K_e:
                        self.consume_food()
                    
                    # Quit
                    elif event.key == pygame.K_ESCAPE:
                        return False
                        
                except Exception as e:
                    print(f"Error handling input: {e}")
                    self.status.set(f"Action failed: {e}")
        
        return True
    
    def move_player(self, direction: int):
        """Send move action to server."""
        try:
            self.player_data = self.api_client.perform_player_action(
                "move", 
                direction=direction
            )
            self.update_local_state_from_player_data()
            self.status.set(f"Moving {['up', 'left', 'down', 'right'][direction]}")
        except Exception as e:
            print(f"Failed to move: {e}")
            self.status.set(f"Move failed: {e}")
    
    def stop_player(self):
        """Stop player movement."""
        try:
            self.player_data = self.api_client.perform_player_action("stop")
            self.update_local_state_from_player_data()
            self.status.set("Stopped")
        except Exception as e:
            print(f"Failed to stop: {e}")
    
    def toggle_gathering(self):
        """Toggle gathering state."""
        try:
            is_gathering = self.player_data.get('gathering', False)
            self.player_data = self.api_client.perform_player_action(
                "gather",
                gathering=not is_gathering
            )
            self.update_local_state_from_player_data()
            status = "gathering" if not is_gathering else "stopped gathering"
            self.status.set(f"Player {status}")
        except Exception as e:
            print(f"Failed to toggle gathering: {e}")
    
    def add_item(self, item_name: str):
        """Add item to inventory."""
        try:
            inventory = self.api_client.add_item_to_inventory(item_name)
            # Refresh player data to get updated inventory
            self.player_data = self.api_client.get_player()
            self.update_local_state_from_player_data()
            self.status.set(f"Added {item_name} to inventory")
        except Exception as e:
            print(f"Failed to add item: {e}")
            self.status.set(f"Add failed: {e}")
    
    def consume_food(self):
        """Consume first food item in inventory."""
        if not self.inventory_items:
            self.status.set("No items to consume")
            return
        
        try:
            first_item = self.inventory_items[0]['name']
            self.player_data = self.api_client.perform_player_action(
                "consume",
                item_name=first_item
            )
            self.update_local_state_from_player_data()
            self.status.set(f"Consumed {first_item}")
        except Exception as e:
            print(f"Failed to consume: {e}")
            self.status.set(f"Consume failed: {e}")
    
    def update_tick(self):
        """Update game tick on server."""
        try:
            session_data = self.api_client.update_tick()
            self.current_tick = session_data.get('currentTick', self.current_tick)
        except Exception as e:
            print(f"Failed to update tick: {e}")
    
    def render(self):
        """Render the game UI."""
        # Clear screen
        self.game_display.fill((20, 20, 30))
        
        # Title
        title = self.font.render("Roam Client (Server-Backed)", True, (255, 255, 255))
        self.game_display.blit(title, (20, 20))
        
        # Server status
        server_status = f"Server: {self.api_client.base_url}"
        server_text = self.small_font.render(server_status, True, (200, 200, 200))
        self.game_display.blit(server_text, (20, 60))
        
        # Session info
        if self.session_id:
            session_text = self.small_font.render(
                f"Session: {self.session_id[:8]}... | Tick: {self.current_tick}", 
                True, (200, 200, 200)
            )
            self.game_display.blit(session_text, (20, 85))
        
        # Player info
        y_offset = 130
        player_title = self.font.render("Player Status", True, (100, 200, 100))
        self.game_display.blit(player_title, (20, y_offset))
        
        y_offset += 40
        energy_text = self.small_font.render(
            f"Energy: {self.player_energy:.1f}/100.0", 
            True, (255, 200, 100)
        )
        self.game_display.blit(energy_text, (40, y_offset))
        
        # Energy bar
        bar_width = 200
        bar_height = 20
        energy_ratio = self.player_energy / 100.0
        pygame.draw.rect(
            self.game_display, 
            (100, 100, 100), 
            (40, y_offset + 30, bar_width, bar_height)
        )
        pygame.draw.rect(
            self.game_display, 
            (255, 200, 100), 
            (40, y_offset + 30, int(bar_width * energy_ratio), bar_height)
        )
        
        y_offset += 70
        direction_names = ["Up", "Left", "Down", "Right"]
        direction = direction_names[self.player_direction] if 0 <= self.player_direction <= 3 else "None"
        direction_text = self.small_font.render(
            f"Direction: {direction}", 
            True, (200, 200, 255)
        )
        self.game_display.blit(direction_text, (40, y_offset))
        
        y_offset += 30
        moving = self.player_data.get('moving', False) if self.player_data else False
        moving_text = self.small_font.render(
            f"Moving: {moving}", 
            True, (200, 200, 255)
        )
        self.game_display.blit(moving_text, (40, y_offset))
        
        y_offset += 30
        gathering = self.player_data.get('gathering', False) if self.player_data else False
        gathering_text = self.small_font.render(
            f"Gathering: {gathering}", 
            True, (200, 200, 255)
        )
        self.game_display.blit(gathering_text, (40, y_offset))
        
        # Inventory
        y_offset += 60
        inv_title = self.font.render("Inventory", True, (100, 200, 100))
        self.game_display.blit(inv_title, (20, y_offset))
        
        y_offset += 40
        if self.inventory_items:
            for item in self.inventory_items:
                item_text = self.small_font.render(
                    f"- {item['name']} x{item['count']}", 
                    True, (200, 255, 200)
                )
                self.game_display.blit(item_text, (40, y_offset))
                y_offset += 25
        else:
            empty_text = self.small_font.render("(empty)", True, (150, 150, 150))
            self.game_display.blit(empty_text, (40, y_offset))
        
        # Controls
        y_offset = self.config.displayHeight - 200
        controls_title = self.font.render("Controls", True, (255, 200, 100))
        self.game_display.blit(controls_title, (20, y_offset))
        
        y_offset += 40
        controls = [
            "WASD/Arrows: Move",
            "Space: Stop",
            "G: Toggle Gathering",
            "1/2/3: Add Items (test)",
            "E: Consume Food",
            "ESC: Quit"
        ]
        
        for control in controls:
            control_text = self.small_font.render(control, True, (200, 200, 200))
            self.game_display.blit(control_text, (40, y_offset))
            y_offset += 25
        
        # Status bar at bottom
        if self.status:
            status_text = self.small_font.render(
                self.status.getText(), 
                True, (255, 255, 100)
            )
            self.game_display.blit(
                status_text, 
                (20, self.config.displayHeight - 30)
            )
        
        pygame.display.update()
    
    def run(self):
        """Main game loop."""
        # Start session
        if not self.start_session():
            print("Failed to connect to server. Make sure the server is running.")
            return
        
        # Main loop
        tick_counter = 0
        tick_update_frequency = 60  # Update server tick every 60 frames
        
        while self.running:
            # Handle input
            if not self.handle_input():
                self.running = False
                break
            
            # Update tick periodically
            tick_counter += 1
            if tick_counter >= tick_update_frequency:
                self.update_tick()
                tick_counter = 0
            
            # Render
            self.render()
            
            # Cap frame rate
            self.clock.tick(60)
        
        # Cleanup
        try:
            if self.session_id:
                self.api_client.delete_session()
                print("Session ended")
        except Exception as e:
            print(f"Error ending session: {e}")
        
        pygame.quit()


def main():
    """Main entry point."""
    # Check for server URL argument
    server_url = "http://localhost:8080"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    print("=" * 60)
    print("Roam Client - Server-Backed Application")
    print("=" * 60)
    print(f"Server URL: {server_url}")
    print("Make sure the Spring Boot server is running!")
    print("=" * 60)
    print()
    
    # Create config and client
    config = Config()
    client = RoamClient(config, server_url)
    
    # Run
    try:
        client.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
