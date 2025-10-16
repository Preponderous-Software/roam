import json
import os
from config.config import Config
from entity.apple import Apple
from entity.banana import Banana
from entity.coalOre import CoalOre
from entity.grass import Grass
from entity.ironOre import IronOre
from entity.jungleWood import JungleWood
from entity.leaves import Leaves
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from entity.oakWood import OakWood
from entity.stone import Stone
from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
from player.player import Player
from stats.stats import Stats
from world.map import Map
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.tickCounter import TickCounter


# @author Daniel McCoy Stephenson
# @since October 16th, 2025
class WorldController:
    """
    Handles all gameplay logic independent of UI implementation.
    This class manages game state, player actions, world generation, and persistence.
    """
    
    def __init__(
        self,
        config: Config,
        tickCounter: TickCounter,
        stats: Stats,
        player: Player,
        graphik=None,
    ):
        self.config = config
        self.tickCounter = tickCounter
        self.stats = stats
        self.player = player
        self.graphik = graphik  # Optional for compatibility
        self.map = None
        self.currentRoom = None
        self.roomJsonReaderWriter = RoomJsonReaderWriter(
            self.config.gridSize, self.graphik, self.tickCounter, self.config
        )
    
    def initialize(self):
        """Initialize the game world."""
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
    
    # ===== Persistence Methods =====
    
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
        inventoryJsonReaderWriter = InventoryJsonReaderWriter()
        inventory = inventoryJsonReaderWriter.loadInventoryFromFile(
            self.config.pathToSaveDirectory + "/playerInventory.json"
        )
        if inventory != -1:
            self.player.setInventory(inventory)
    
    def save(self):
        """Save game state."""
        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)
        
        self.savePlayerLocationToFile()
        self.savePlayerAttributesToFile()
        self.savePlayerInventoryToFile()
        self.stats.save()
        self.tickCounter.save()
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
        inventoryJsonReaderWriter = InventoryJsonReaderWriter()
        inventoryJsonReaderWriter.saveInventoryToFile(
            self.player.getInventory(),
            self.config.pathToSaveDirectory + "/playerInventory.json",
        )
    
    def saveRoomToFile(self, room):
        """Save room to file."""
        self.roomJsonReaderWriter.saveRoomToFile(room)
    
    # ===== Gameplay Methods =====
    
    def getLocationOfPlayer(self):
        """Get current location of player."""
        return self.map.getLocationOfEntity(self.player, self.currentRoom)
    
    def isPlayerAtEdge(self, location):
        """Check if player is at edge of room."""
        gridSize = self.config.gridSize
        x, y = location.getX(), location.getY()
        return x == 0 or x == gridSize - 1 or y == 0 or y == gridSize - 1
    
    def movePlayer(self, direction):
        """
        Move player in given direction.
        Returns True if move was successful, False otherwise.
        """
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
            
            return True
        return False
    
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
            self.stats.incrementScore()
            self.stats.incrementRoomsExplored()
            return "new_room_discovered"
        
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
        return "room_transition"
    
    def canBePickedUp(self, entity):
        """Check if an entity can be picked up."""
        itemTypes = [
            OakWood,
            JungleWood,
            Leaves,
            Grass,
            Apple,
            Stone,
            CoalOre,
            IronOre,
            Chicken,
            Bear,
            Banana,
        ]
        for itemType in itemTypes:
            if isinstance(entity, itemType):
                return True
        return False
    
    def gatherAtPlayerLocation(self):
        """
        Gather resources at player location.
        Returns a tuple (success: bool, message: str, entity: object or None)
        """
        location = self.getLocationOfPlayer()
        entities = location.getEntities()
        
        for _, entity in entities.items():
            if entity != self.player and self.canBePickedUp(entity):
                result = self.player.getInventory().placeIntoFirstAvailableInventorySlot(entity)
                if result:
                    self.currentRoom.removeEntity(entity)
                    if isinstance(entity, LivingEntity):
                        self.currentRoom.removeLivingEntity(entity)
                    self.player.removeEnergy(self.config.playerInteractionEnergyCost)
                    return (True, f"gathered {entity.getName()}", entity)
                else:
                    return (False, "inventory full", None)
        
        return (False, "nothing to gather here", None)
    
    def placeAtPlayerLocation(self):
        """
        Place selected item at player location.
        Returns a tuple (success: bool, message: str, item: object or None)
        """
        inventory = self.player.getInventory()
        inventorySlot = inventory.getSelectedInventorySlot()
        
        if inventorySlot.isEmpty():
            return (False, "no item selected", None)
        
        item = inventory.removeSelectedItem()
        if item == -1:
            return (False, "no item selected", None)
        
        location = self.getLocationOfPlayer()
        self.currentRoom.addEntityToLocation(item, location)
        self.player.removeEnergy(self.config.playerInteractionEnergyCost)
        return (True, f"placed {item.getName()}", item)
    
    def checkForPlayerDeath(self):
        """
        Check if player has died.
        Returns True if player died, False otherwise.
        """
        if self.player.getEnergy() <= 0:
            self.player.kill()
            self.stats.incrementNumberOfDeaths()
            return True
        return False
    
    def respawnPlayer(self):
        """Respawn player at spawn location."""
        self.player.setEnergy(100)
        self.player.setDead(False)
        self.currentRoom = self.map.getRoom(0, 0)
        if self.currentRoom == -1:
            self.currentRoom = self.map.generateNewRoom(0, 0)
        location = self.currentRoom.getGrid().getLocation(0)
        self.currentRoom.addEntityToLocation(self.player, location)
    
    def updateWorld(self):
        """
        Update world state (AI, reproduction, etc.).
        Should be called once per game tick.
        """
        # Remove energy over time
        self.player.removeEnergy(self.config.energyDepletionRate)
        
        # Move living entities
        self.currentRoom.moveLivingEntities(self.tickCounter.getTick())
        
        # Reproduce living entities
        self.currentRoom.reproduceLivingEntities(self.tickCounter.getTick())
        
        # Remove dead entities if configured
        if self.config.removeDeadEntities:
            # This would need to be implemented in Room class
            pass
    
    def getCurrentRoom(self):
        """Get the current room."""
        return self.currentRoom
    
    def getPlayer(self):
        """Get the player."""
        return self.player
    
    def getStats(self):
        """Get the stats."""
        return self.stats
    
    def getTickCounter(self):
        """Get the tick counter."""
        return self.tickCounter
