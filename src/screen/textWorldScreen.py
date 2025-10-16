import sys
import select
import time
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
        self.textUI = TextUI(tickCounter)
        
        # Use WorldController for all gameplay logic
        self.worldController = WorldController(
            config,
            tickCounter,
            stats,
            player,
            graphik,
        )
    
    def initialize(self):
        """Initialize the world screen."""
        self.worldController.initialize()
        self.textUI.setStatus("entered the world")
    
    def handleInput(self, key):
        """Handle keyboard input."""
        # Movement - WASD keys and arrow keys
        if key == 'w' or key == 'up':
            self.worldController.movePlayer(0)  # up
        elif key == 's' or key == 'down':
            self.worldController.movePlayer(2)  # down
        elif key == 'a' or key == 'left':
            self.worldController.movePlayer(1)  # left
        elif key == 'd' or key == 'right':
            self.worldController.movePlayer(3)  # right
        
        # Inventory selection (1-0 keys)
        elif key in '1234567890':
            idx = int(key) - 1 if key != '0' else 9
            self.worldController.getPlayer().getInventory().setSelectedInventorySlotIndex(idx)
        
        # Actions
        elif key == 'g':
            success, message, _ = self.worldController.gatherAtPlayerLocation()
            self.textUI.setStatus(message)
        elif key == 'p':
            success, message, _ = self.worldController.placeAtPlayerLocation()
            self.textUI.setStatus(message)
        
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
    
    def getInput(self, timeout=0.1):
        """Get keyboard input with timeout (non-blocking)."""
        if sys.platform == 'win32':
            # Windows doesn't support select on stdin
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                # Handle arrow keys on Windows
                if key == b'\xe0':  # Arrow key prefix on Windows
                    key = msvcrt.getch()
                    if key == b'H':  # Up arrow
                        return 'up'
                    elif key == b'P':  # Down arrow
                        return 'down'
                    elif key == b'K':  # Left arrow
                        return 'left'
                    elif key == b'M':  # Right arrow
                        return 'right'
                return key.decode('utf-8').lower()
            return None
        else:
            # Unix-like systems
            import termios
            import tty
            
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                if rlist:
                    char = sys.stdin.read(1)
                    # Handle escape sequences (arrow keys)
                    if char == '\x1b':  # ESC
                        # Try to read the rest of the arrow key sequence
                        rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
                        if rlist:
                            char2 = sys.stdin.read(1)
                            if char2 == '[':
                                rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
                                if rlist:
                                    char3 = sys.stdin.read(1)
                                    if char3 == 'A':  # Up arrow
                                        return 'up'
                                    elif char3 == 'B':  # Down arrow
                                        return 'down'
                                    elif char3 == 'C':  # Right arrow
                                        return 'right'
                                    elif char3 == 'D':  # Left arrow
                                        return 'left'
                    return char.lower()
                return None
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    
    def run(self):
        """Main game loop for text-based UI."""
        tickDelay = 1.0 / self.config.ticksPerSecond
        lastTickTime = time.time()
        
        while not self.changeScreen:
            # Handle input
            key = self.getInput(timeout=tickDelay)
            if key:
                self.handleInput(key)
            
            # Update game state
            currentTime = time.time()
            if currentTime - lastTickTime >= tickDelay:
                # Update world (AI, energy depletion, etc.)
                self.worldController.updateWorld()
                
                # Check for player death
                if self.worldController.checkForPlayerDeath():
                    self.textUI.setStatus("You died!")
                    time.sleep(2)
                    self.worldController.respawnPlayer()
                    self.textUI.setStatus("respawned")
                
                # Increment tick
                self.worldController.getTickCounter().incrementTick()
                lastTickTime = currentTime
            
            # Draw UI
            self.textUI.drawWorld(
                self.worldController.getCurrentRoom(),
                self.worldController.getPlayer()
            )
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)
        
        # Save game state
        self.worldController.save()
        
        self.changeScreen = False
        return self.nextScreen
