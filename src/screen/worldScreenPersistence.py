import json
import os
import jsonschema
from math import ceil
from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from player.player import Player
from stats.stats import Stats
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


@component
class WorldScreenPersistence:
    """Handles all save/load operations for WorldScreen."""

    def __init__(
        self,
        config: Config,
        player: Player,
        stats: Stats,
        tickCounter: TickCounter,
        roomJsonReaderWriter: RoomJsonReaderWriter,
    ):
        self.config = config
        self.player = player
        self.stats = stats
        self.tickCounter = tickCounter
        self.roomJsonReaderWriter = roomJsonReaderWriter

    def savePlayerLocationToFile(self, currentRoom):
        jsonPlayerLocation = {
            "roomX": currentRoom.getX(),
            "roomY": currentRoom.getY(),
            "locationId": str(self.player.getLocationID()),
        }

        with open("schemas/playerLocation.json") as f:
            playerLocationSchema = json.load(f)
        jsonschema.validate(jsonPlayerLocation, playerLocationSchema)

        path = self.config.pathToSaveDirectory + "/playerLocation.json"
        _logger.info("saving player location", path=path)
        with open(path, "w") as f:
            json.dump(jsonPlayerLocation, f, indent=4)

    def loadPlayerLocationFromFile(self, mapInstance):
        path = self.config.pathToSaveDirectory + "/playerLocation.json"
        if not os.path.exists(path):
            return None

        _logger.info("loading player location", path=path)
        with open(path) as f:
            jsonPlayerLocation = json.load(f)

        with open("schemas/playerLocation.json") as f:
            playerLocationSchema = json.load(f)
        jsonschema.validate(jsonPlayerLocation, playerLocationSchema)

        roomX = jsonPlayerLocation["roomX"]
        roomY = jsonPlayerLocation["roomY"]
        currentRoom = mapInstance.getRoom(roomX, roomY)

        if currentRoom == -1:
            _logger.warning(
                "saved room not found, falling back to spawn",
                roomX=roomX,
                roomY=roomY,
            )
            return None

        locationId = jsonPlayerLocation["locationId"]
        try:
            location = currentRoom.getGrid().getLocation(locationId)
        except KeyError:
            _logger.warning(
                "saved location not found in room, falling back to spawn",
                locationId=locationId,
                roomX=roomX,
                roomY=roomY,
            )
            return None

        currentRoom.addEntityToLocation(self.player, location)
        return currentRoom

    def savePlayerAttributesToFile(self):
        jsonPlayerAttributes = {"energy": ceil(self.player.getEnergy())}

        with open("schemas/playerAttributes.json") as f:
            playerAttributesSchema = json.load(f)
        jsonschema.validate(jsonPlayerAttributes, playerAttributesSchema)

        path = self.config.pathToSaveDirectory + "/playerAttributes.json"
        _logger.info("saving player attributes", path=path)
        with open(path, "w") as f:
            json.dump(jsonPlayerAttributes, f, indent=4)

    def loadPlayerAttributesFromFile(self):
        path = self.config.pathToSaveDirectory + "/playerAttributes.json"
        if not os.path.exists(path):
            return

        _logger.info("loading player attributes", path=path)
        with open(path) as f:
            jsonPlayerAttributes = json.load(f)

        with open("schemas/playerAttributes.json") as f:
            playerAttributesSchema = json.load(f)
        jsonschema.validate(jsonPlayerAttributes, playerAttributesSchema)

        energy = jsonPlayerAttributes["energy"]
        self.player.setEnergy(energy)

    def savePlayerInventoryToFile(self, inventoryJsonReaderWriter):
        return inventoryJsonReaderWriter.saveInventory(
            self.player.getInventory(),
            self.config.pathToSaveDirectory + "/playerInventory.json",
        )

    def loadPlayerInventoryFromFile(self, inventoryJsonReaderWriter):
        inventory = inventoryJsonReaderWriter.loadInventory(
            self.config.pathToSaveDirectory + "/playerInventory.json"
        )
        if inventory is not None:
            self.player.setInventory(inventory)

    def saveRoomToFile(self, room):
        roomPath = self.config.getRoomFilePath(room.getX(), room.getY())
        _logger.info("saving room", path=roomPath)
        os.makedirs(self.config.getRoomsDirectory(), exist_ok=True)

        jsonRoom = self.roomJsonReaderWriter.generateJsonForRoom(room)
        with open(roomPath, "w") as outfile:
            json.dump(jsonRoom, outfile, indent=4)
