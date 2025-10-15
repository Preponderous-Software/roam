import datetime
import json
import os
import time
import sys
import select
from config.config import Config
from screen.screenType import ScreenType
from stats.stats import Stats
from ui.textUI import TextUI
from world.tickCounter import TickCounter
from world.map import Map
from player.player import Player
from lib.graphik.src.graphik import Graphik


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
        graphik: Graphik = None,
    ):
        self.config = config
        self.tickCounter = tickCounter
        self.stats = stats
        self.player = player
        self.graphik = graphik  # Keep for compatibility but may be None
        self.running = True
        self.nextScreen = ScreenType.NONE
        self.changeScreen = False
        self.textUI = TextUI(self.tickCounter)
        
        # Import room utilities
        from world.roomJsonReaderWriter import RoomJsonReaderWriter
        self.roomJsonReaderWriter = RoomJsonReaderWriter(
            self.config.gridSize, self.graphik, self.tickCounter, self.config
        )
    
    def initialize(self):
        """Initialize the world screen."""
        self.map = Map(
            self.config.gridSize, self.graphik, self.tickCounter, self.config
        )
        
        # Load player location if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/playerLocation.json"):
            self.loadPlayerLocationFromFile()
        else:
            self.currentRoom = self.map.getRoom(0, 0)
            if self.currentRoom == -1:
                self.currentRoom = self.map.generateNewRoom(0, 0)
            self.currentRoom.addEntity(self.player)
            self.stats.incrementRoomsExplored()
        
        # Load player attributes if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/playerAttributes.json"):
            self.loadPlayerAttributesFromFile()
        
        # Load stats if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/stats.json"):
            self.stats.load()
        
        # Load tick if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/tick.json"):
            self.tickCounter.load()
        
        # Load player inventory if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/playerInventory.json"):
            self.loadPlayerInventoryFromFile()
        
        self.textUI.setStatus("entered the world")
    
    def loadPlayerLocationFromFile(self):
        """Load player location from file."""
        with open(self.config.pathToSaveDirectory + "/playerLocation.json", "r") as file:
            data = json.load(file)
            roomX = data["roomX"]
            roomY = data["roomY"]
            locationID = data["locationID"]
            
            self.currentRoom = self.map.getRoom(roomX, roomY)
            if self.currentRoom == -1:
                self.currentRoom = self.roomJsonReaderWriter.loadRoomFromFile(roomX, roomY)
                if self.currentRoom != -1:
                    self.map.addRoom(self.currentRoom)
            
            location = self.currentRoom.getGrid().getLocation(locationID)
            self.currentRoom.addEntityToLocation(self.player, location)
    
    def loadPlayerAttributesFromFile(self):
        """Load player attributes from file."""
        with open(self.config.pathToSaveDirectory + "/playerAttributes.json", "r") as file:
            data = json.load(file)
            self.player.setEnergy(data["energy"])
            self.player.setDirection(data["direction"])
    
    def loadPlayerInventoryFromFile(self):
        """Load player inventory from file."""
        from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
        inventoryJsonReaderWriter = InventoryJsonReaderWriter()
        inventory = inventoryJsonReaderWriter.loadInventoryFromFile(
            self.config.pathToSaveDirectory + "/playerInventory.json"
        )
        if inventory != -1:
            self.player.setInventory(inventory)
    
    def save(self):
        """Save game state."""
        # Create save directory if it doesn't exist
        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)
        
        # Save player location
        self.savePlayerLocationToFile()
        
        # Save player attributes
        self.savePlayerAttributesToFile()
        
        # Save player inventory
        self.savePlayerInventoryToFile()
        
        # Save stats
        self.stats.save()
        
        # Save tick
        self.tickCounter.save()
        
        # Save current room
        self.saveRoomToFile(self.currentRoom)
    
    def savePlayerLocationToFile(self):
        """Save player location to file."""
        data = {
            "roomX": self.currentRoom.getX(),
            "roomY": self.currentRoom.getY(),
            "locationID": self.player.getLocationID(),
        }
        with open(self.config.pathToSaveDirectory + "/playerLocation.json", "w") as file:
            json.dump(data, file)
    
    def savePlayerAttributesToFile(self):
        """Save player attributes to file."""
        data = {
            "energy": self.player.getEnergy(),
            "direction": self.player.getDirection(),
        }
        with open(self.config.pathToSaveDirectory + "/playerAttributes.json", "w") as file:
            json.dump(data, file)
    
    def savePlayerInventoryToFile(self):
        """Save player inventory to file."""
        from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
        inventoryJsonReaderWriter = InventoryJsonReaderWriter()
        inventoryJsonReaderWriter.saveInventoryToFile(
            self.player.getInventory(),
            self.config.pathToSaveDirectory + "/playerInventory.json",
        )
    
    def saveRoomToFile(self, room):
        """Save room to file."""
        self.roomJsonReaderWriter.saveRoomToFile(room)
    
    def handleInput(self, key):
        """Handle keyboard input."""
        from lib.pyenvlib.location import Location
        
        # Movement
        if key == 'w':
            self.movePlayer(0)  # up
        elif key == 's':
            self.movePlayer(2)  # down
        elif key == 'a':
            self.movePlayer(1)  # left
        elif key == 'd':
            self.movePlayer(3)  # right
        
        # Inventory selection (1-0 keys)
        elif key in '1234567890':
            idx = int(key) - 1 if key != '0' else 9
            self.player.getInventory().setSelectedInventorySlotIndex(idx)
        
        # Actions
        elif key == 'g':
            self.gatherAtPlayerLocation()
        elif key == 'p':
            self.placeAtPlayerLocation()
        
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
    
    def movePlayer(self, direction):
        """Move player in given direction."""
        self.player.setDirection(direction)
        
        location = self.getLocationOfPlayer()
        grid = self.currentRoom.getGrid()
        
        newLocation = None
        if direction == 0:  # up
            newLocation = grid.getUp(location)
        elif direction == 1:  # left
            newLocation = grid.getLeft(location)
        elif direction == 2:  # down
            newLocation = grid.getDown(location)
        elif direction == 3:  # right
            newLocation = grid.getRight(location)
        
        if newLocation != -1:
            self.currentRoom.removeEntity(self.player)
            self.currentRoom.addEntityToLocation(self.player, newLocation)
            self.player.removeEnergy(self.config.playerMovementEnergyCost)
            
            # Check if we need to move to a new room
            if self.isPlayerAtEdge(newLocation):
                self.handleRoomTransition(direction)
    
    def getLocationOfPlayer(self):
        """Get current location of player."""
        return self.map.getLocationOfEntity(self.player, self.currentRoom)
    
    def isPlayerAtEdge(self, location):
        """Check if player is at edge of room."""
        gridSize = self.config.gridSize
        x, y = location.getX(), location.getY()
        return x == 0 or x == gridSize - 1 or y == 0 or y == gridSize - 1
    
    def handleRoomTransition(self, direction):
        """Handle transition to adjacent room."""
        x, y = self.currentRoom.getX(), self.currentRoom.getY()
        location = self.getLocationOfPlayer()
        
        # Determine new room coordinates based on player location
        if location.getX() == 0:
            x -= 1
        elif location.getX() == self.config.gridSize - 1:
            x += 1
        elif location.getY() == 0:
            y -= 1
        elif location.getY() == self.config.gridSize - 1:
            y += 1
        
        # Get or generate new room
        newRoom = self.map.getRoom(x, y)
        if newRoom == -1:
            newRoom = self.map.generateNewRoom(x, y)
            self.textUI.setStatus("new area discovered")
            self.stats.incrementScore()
            self.stats.incrementRoomsExplored()
        
        # Move player to new room at opposite edge
        self.currentRoom.removeEntity(self.player)
        
        # Calculate new location in new room
        newX, newY = location.getX(), location.getY()
        if location.getX() == 0:
            newX = self.config.gridSize - 1
        elif location.getX() == self.config.gridSize - 1:
            newX = 0
        elif location.getY() == 0:
            newY = self.config.gridSize - 1
        elif location.getY() == self.config.gridSize - 1:
            newY = 0
        
        newLocation = newRoom.getGrid().getLocationByCoordinates(newX, newY)
        newRoom.addEntityToLocation(self.player, newLocation)
        self.currentRoom = newRoom
    
    def gatherAtPlayerLocation(self):
        """Gather resources at player location."""
        location = self.getLocationOfPlayer()
        entities = self.currentRoom.getEntitiesAtLocation(location)
        
        for entity in entities:
            if entity != self.player and hasattr(entity, 'isGatherable') and entity.isGatherable():
                # Try to add to inventory
                if self.player.getInventory().add(entity):
                    self.currentRoom.removeEntity(entity)
                    self.textUI.setStatus(f"gathered {entity.getName()}")
                    self.player.removeEnergy(self.config.playerInteractionEnergyCost)
                    return
                else:
                    self.textUI.setStatus("inventory full")
                    return
        
        self.textUI.setStatus("nothing to gather here")
    
    def placeAtPlayerLocation(self):
        """Place selected item at player location."""
        inventory = self.player.getInventory()
        selectedIdx = inventory.getSelectedInventorySlotIndex()
        slot = inventory.getInventorySlot(selectedIdx)
        
        if slot.isEmpty():
            self.textUI.setStatus("no item selected")
            return
        
        item = slot.removeItem()
        location = self.getLocationOfPlayer()
        self.currentRoom.addEntityToLocation(item, location)
        self.textUI.setStatus(f"placed {item.getName()}")
        self.player.removeEnergy(self.config.playerInteractionEnergyCost)
    
    def checkForPlayerDeath(self):
        """Check if player has died."""
        if self.player.getEnergy() <= 0:
            self.player.kill()
            self.textUI.setStatus("You died!")
            self.stats.incrementNumberOfDeaths()
            return True
        return False
    
    def respawnPlayer(self):
        """Respawn player at spawn location."""
        self.player.setEnergy(self.player.getMaxEnergy())
        self.player.setDead(False)
        self.currentRoom = self.map.getRoom(0, 0)
        if self.currentRoom == -1:
            self.currentRoom = self.map.generateNewRoom(0, 0)
        location = self.currentRoom.getGrid().getLocation(0)
        self.currentRoom.addEntityToLocation(self.player, location)
        self.textUI.setStatus("respawned")
    
    def getInput(self, timeout=0.1):
        """Get keyboard input with timeout (non-blocking)."""
        if sys.platform == 'win32':
            # Windows doesn't support select on stdin
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8').lower()
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
                    return sys.stdin.read(1).lower()
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
                # Remove energy over time
                self.player.removeEnergy(self.config.energyDepletionRate)
                
                # Check for player death
                if self.checkForPlayerDeath():
                    time.sleep(2)
                    self.respawnPlayer()
                
                # Move living entities
                self.currentRoom.moveLivingEntities(self.tickCounter.getTick())
                
                # Reproduce living entities
                self.currentRoom.reproduceLivingEntities(self.tickCounter.getTick())
                
                # Increment tick
                self.tickCounter.incrementTick()
                lastTickTime = currentTime
            
            # Draw
            self.textUI.drawWorld(self.currentRoom, self.player)
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.01)
        
        # Save game state
        self.save()
        
        self.changeScreen = False
        return self.nextScreen
