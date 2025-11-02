# @author Daniel McCoy Stephenson
# @since October 15th, 2025
# Text-based UI for Roam

import sys
import time
from world.tickCounter import TickCounter


class TextUI:
    """Text-based UI renderer for Roam game."""

    def __init__(self, tickCounter: TickCounter, target_fps: int = 3):
        self.tickCounter = tickCounter
        self.statusText = ""
        self.lastStatusTick = -1
        self.statusDuration = 60  # ticks to show status

        # Frame rate limiting - default to 3 FPS for stable text display
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps
        self.last_frame_time = 0.0
        self.frame_count = 0

    def clearScreen(self):
        """Clear the terminal screen using ANSI escape codes."""
        # Hide cursor, clear screen, and move cursor to top-left
        # This reduces flicker by hiding cursor during redraw
        print('\033[?25l\033[2J\033[H', end='', flush=True)

    def setStatus(self, text):
        """Set status message to display."""
        self.statusText = text
        self.lastStatusTick = self.tickCounter.getTick()

    def getStatus(self):
        """Get current status message if not expired."""
        if self.lastStatusTick == -1:
            return ""
        currentTick = self.tickCounter.getTick()
        if currentTick - self.lastStatusTick < self.statusDuration:
            return self.statusText
        return ""

    def shouldRender(self):
        """Check if enough time has passed to render the next frame."""
        current_time = time.time()
        elapsed = current_time - self.last_frame_time

        if elapsed >= self.frame_time:
            self.last_frame_time = current_time
            self.frame_count += 1
            return True
        return False

    def setTargetFPS(self, fps: int):
        """Set the target frame rate for rendering."""
        self.target_fps = max(1, min(fps, 60))  # Clamp between 1-60 FPS
        self.frame_time = 1.0 / self.target_fps

    def getTargetFPS(self):
        """Get the current target FPS."""
        return self.target_fps

    def drawWorld(self, room, player, viewport_size=None):
        """Draw the game world in text format.
        
        Args:
            room: The current room
            player: The player entity
            viewport_size: Size of viewport (None = full grid, or int for NxN centered view)
        """
        self.clearScreen()

        # Compact header for mobile
        print("ROAM")
        
        # Display status if available (compact)
        status = self.getStatus()
        if status:
            print(f"[{status}]")

        # Display player info (compact)
        energy = player.getEnergy()
        maxEnergy = 100  # Maximum energy is hardcoded to 100 in LivingEntity
        energyPercent = int((energy / maxEnergy) * 100) if maxEnergy > 0 else 0
        energyBar = "█" * (energyPercent // 10) + "░" * (10 - energyPercent // 10)
        print(f"E:[{energyBar}]{energy:.0f}")

        # Display grid
        grid = room.getGrid()
        gridSize = grid.getRows()

        # Find player location
        playerLoc = None
        for loc in grid.getLocations().values():
            entities = loc.getEntities()
            for _, entity in entities.items():
                if entity == player:
                    playerLoc = loc
                    break
            if playerLoc:
                break

        # Calculate viewport if specified
        if viewport_size and viewport_size < gridSize:
            # Center viewport on player
            px, py = playerLoc.getX(), playerLoc.getY()
            half_view = viewport_size // 2
            
            start_x = max(0, min(gridSize - viewport_size, px - half_view))
            start_y = max(0, min(gridSize - viewport_size, py - half_view))
            end_x = start_x + viewport_size
            end_y = start_y + viewport_size
        else:
            # Show full grid
            start_x, start_y = 0, 0
            end_x, end_y = gridSize, gridSize

        print("─" * ((end_x - start_x) * 2 + 1))

        for y in range(start_y, end_y):
            row = "│"
            for x in range(start_x, end_x):
                loc = grid.getLocationByCoordinates(x, y)
                if loc == -1:
                    row += "? "
                    continue

                entities = loc.getEntities()

                # Check if player is at this location
                if playerLoc and loc.getX() == playerLoc.getX() and loc.getY() == playerLoc.getY():
                    row += "@ "
                elif len(entities) > 0:
                    # Show first non-player entity
                    entity = None
                    for _, ent in entities.items():
                        if ent != player:
                            entity = ent
                            break
                    if entity:
                        name = entity.getName().lower()
                        if "grass" in name:
                            row += ", "
                        elif "tree" in name or "wood" in name:
                            row += "T "
                        elif "stone" in name or "ore" in name:
                            row += "* "
                        elif "apple" in name or "banana" in name:
                            row += "o "
                        elif "bear" in name or "chicken" in name:
                            row += "A "
                        else:
                            row += "? "
                    else:
                        row += ". "
                else:
                    row += ". "
            row += "│"
            print(row)

        print("─" * ((end_x - start_x) * 2 + 1))

        # Display inventory (compact - single line)
        inventory = player.getInventory()
        firstTen = inventory.getFirstTenInventorySlots()
        selectedIdx = inventory.getSelectedInventorySlotIndex()

        invLine = "["
        for i in range(10):
            if i < len(firstTen):
                slot = firstTen[i]
                if slot.isEmpty():
                    invLine += " " if i != selectedIdx else ">"
                else:
                    item = slot.getContents()[0]
                    itemName = item.getName()[0].upper()  # First letter only
                    invLine += itemName if i != selectedIdx else f">{itemName}<"[1]
            else:
                invLine += " "
        invLine += "]"
        print(invLine)

        # Compact controls
        print("wasd/↑↓←→:move g:get p:put q:quit")
        # Show cursor at the end of each frame
        print('\033[?25h', end='', flush=True)
    
    def cleanup(self):
        """Clean up terminal state on exit."""
        # Show cursor
        print('\033[?25h', end='', flush=True)