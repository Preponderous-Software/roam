import sys
import select
import time
import threading
import queue
from config.config import Config
from screen.screenType import ScreenType
from stats.stats import Stats
from ui.textUI import TextUI
from world.tickCounter import TickCounter
from player.player import Player
from world.worldController import WorldController


# @author Daniel McCoy Stephenson
# @since October 15th, 2025
class TextWorldScreen:
    """Text-based version of the world screen."""

    def __init__(
            self,
            config: Config,
            tickCounter: TickCounter,
            stats: Stats,
            player: Player,
            graphik=None,
    ):
        self.config = config
        self.running = True
        self.nextScreen = ScreenType.NONE
        self.changeScreen = False
        self.textUI = TextUI(tickCounter, target_fps=3)  # 3 FPS for stable text display
        
        # Viewport size for mobile-friendly display (None = full grid, 9 = 9x9 viewport)
        self.viewport_size = 9  # Smaller viewport for mobile

        # Input handling optimization
        self.input_queue = queue.Queue()
        self.input_thread = None
        self.stop_input = False

        # Use WorldController for all gameplay logic
        self.worldController = WorldController(
            config,
            tickCounter,
            stats,
            player,
            graphik,
        )

        # Track if we need to redraw
        self.needs_redraw = True
        self.last_player_pos = None
        self.last_inventory_state = None
        self.last_energy = None  # Track energy for periodic redraws

    def initialize(self):
        """Initialize the world screen."""
        self.worldController.initialize()
        self.textUI.setStatus("entered the world")
        self.needs_redraw = True

        # Start input thread for better responsiveness
        self.start_input_thread()

    def start_input_thread(self):
        """Start background thread for input handling."""
        self.stop_input = False
        self.input_thread = threading.Thread(target=self._input_worker)
        self.input_thread.daemon = True
        self.input_thread.start()

    def stop_input_thread(self):
        """Stop the input thread."""
        self.stop_input = True
        if self.input_thread:
            self.input_thread.join(timeout=0.1)

    def _input_worker(self):
        """Background thread for capturing input."""
        if sys.platform == 'win32':
            self._windows_input_worker()
        else:
            self._unix_input_worker()

    def _windows_input_worker(self):
        """Windows-specific input handling."""
        import msvcrt
        while not self.stop_input:
            try:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\xe0':  # Arrow key prefix
                        key = msvcrt.getch()
                        if key == b'H':
                            self.input_queue.put('up')
                        elif key == b'P':
                            self.input_queue.put('down')
                        elif key == b'K':
                            self.input_queue.put('left')
                        elif key == b'M':
                            self.input_queue.put('right')
                    else:
                        try:
                            char = key.decode('utf-8').lower()
                            self.input_queue.put(char)
                        except:
                            pass
                else:
                    time.sleep(0.01)  # Small delay when no input
            except:
                break

    def _unix_input_worker(self):
        """Unix-specific input handling with persistent terminal settings."""
        import termios
        import tty

        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())

            while not self.stop_input:
                try:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if rlist:
                        char = sys.stdin.read(1)
                        if char == '\x1b':  # ESC sequence
                            # Quick read for arrow keys
                            rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
                            if rlist:
                                char2 = sys.stdin.read(1)
                                if char2 == '[':
                                    rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
                                    if rlist:
                                        char3 = sys.stdin.read(1)
                                        if char3 == 'A':
                                            self.input_queue.put('up')
                                        elif char3 == 'B':
                                            self.input_queue.put('down')
                                        elif char3 == 'C':
                                            self.input_queue.put('right')
                                        elif char3 == 'D':
                                            self.input_queue.put('left')
                        else:
                            self.input_queue.put(char.lower())
                except:
                    break
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def get_queued_input(self):
        """Get input from queue (non-blocking)."""
        try:
            return self.input_queue.get_nowait()
        except queue.Empty:
            return None

    def handleInput(self, key):
        """Handle keyboard input."""
        old_pos = self.get_player_position()
        old_inv_state = self.get_inventory_state()

        # Movement - WASD keys and arrow keys
        if key == 'w' or key == 'up':
            self.worldController.movePlayer(0)  # up
            self.needs_redraw = True
        elif key == 's' or key == 'down':
            self.worldController.movePlayer(2)  # down
            self.needs_redraw = True
        elif key == 'a' or key == 'left':
            self.worldController.movePlayer(1)  # left
            self.needs_redraw = True
        elif key == 'd' or key == 'right':
            self.worldController.movePlayer(3)  # right
            self.needs_redraw = True

        # Inventory selection (1-0 keys)
        elif key in '1234567890':
            idx = int(key) - 1 if key != '0' else 9
            self.worldController.getPlayer().getInventory().setSelectedInventorySlotIndex(idx)
            self.needs_redraw = True

        # Actions
        elif key == 'g':
            success, message, _ = self.worldController.gatherAtPlayerLocation()
            self.textUI.setStatus(message)
            self.needs_redraw = True
        elif key == 'p':
            success, message, _ = self.worldController.placeAtPlayerLocation()
            self.textUI.setStatus(message)
            self.needs_redraw = True

        # Screen changes
        elif key == 'i':
            self.nextScreen = ScreenType.INVENTORY_SCREEN
            self.changeScreen = True
        elif key == 'o':
            self.nextScreen = ScreenType.OPTIONS_SCREEN
            self.changeScreen = True
        elif key == 'q':
            self.nextScreen = ScreenType.NONE
            self.changeScreen = True

    def get_player_position(self):
        """Get current player position for change detection."""
        player = self.worldController.getPlayer()
        room = self.worldController.getCurrentRoom()
        grid = room.getGrid()

        for loc in grid.getLocations().values():
            entities = loc.getEntities()
            for _, entity in entities.items():
                if entity == player:
                    return (loc.getX(), loc.getY())
        return None

    def get_inventory_state(self):
        """Get inventory state for change detection."""
        inventory = self.worldController.getPlayer().getInventory()
        selected = inventory.getSelectedInventorySlotIndex()
        slots = inventory.getFirstTenInventorySlots()

        # Simple hash of inventory state
        state = [selected]
        for slot in slots[:10]:
            if slot.isEmpty():
                state.append(None)
            else:
                item = slot.getContents()[0]
                state.append((item.getName(), slot.getNumItems()))
        return tuple(state)

    def check_if_redraw_needed(self):
        """Check if screen needs redrawing due to game state changes."""
        current_pos = self.get_player_position()
        current_inv = self.get_inventory_state()
        current_status = self.textUI.getStatus()
        current_energy = int(self.worldController.getPlayer().getEnergy())

        # Only redraw if position, inventory, status changed, or energy changed by 1 or more
        if (current_pos != self.last_player_pos or
                current_inv != self.last_inventory_state or
                current_status != getattr(self, 'last_status', '') or
                self.last_energy is None or
                abs(current_energy - self.last_energy) >= 1):
            self.last_player_pos = current_pos
            self.last_inventory_state = current_inv
            self.last_status = current_status
            self.last_energy = current_energy
            self.needs_redraw = True

    def run(self):
        """Main game loop for text-based UI."""
        tickDelay = 1.0 / self.config.ticksPerSecond
        lastTickTime = time.time()

        try:
            while not self.changeScreen:
                # Handle all queued input
                while True:
                    key = self.get_queued_input()
                    if key is None:
                        break
                    self.handleInput(key)

                # Update game state
                currentTime = time.time()
                if currentTime - lastTickTime >= tickDelay:
                    # Update world (AI, energy depletion, etc.)
                    self.worldController.updateWorld()

                    # Check for player death
                    if self.worldController.checkForPlayerDeath():
                        self.textUI.setStatus("You died!")
                        self.needs_redraw = True
                        self.textUI.drawWorld(
                            self.worldController.getCurrentRoom(),
                            self.worldController.getPlayer(),
                            self.viewport_size
                        )
                        time.sleep(2)
                        self.worldController.respawnPlayer()
                        self.textUI.setStatus("respawned")
                        self.needs_redraw = True

                    # Increment tick
                    self.worldController.getTickCounter().incrementTick()
                    lastTickTime = currentTime

                    # Check if game state changed
                    self.check_if_redraw_needed()

                # Draw UI only when needed and frame rate allows
                if self.needs_redraw and self.textUI.shouldRender():
                    self.textUI.drawWorld(
                        self.worldController.getCurrentRoom(),
                        self.worldController.getPlayer(),
                        self.viewport_size
                    )
                    self.needs_redraw = False

                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)

        finally:
            # Clean up
            self.stop_input_thread()
            self.textUI.cleanup()

        # Save game state
        self.worldController.save()

        self.changeScreen = False
        return self.nextScreen