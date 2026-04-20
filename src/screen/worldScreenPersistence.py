import json
import os
import jsonschema
from math import ceil
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


class WorldScreenPersistence:
    """Handles all save/load operations for WorldScreen."""

    def __init__(self, config, player, stats, tickCounter, roomJsonReaderWriter):
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
        inventoryJsonReaderWriter.saveInventory(
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
        roomPath = (
            self.config.pathToSaveDirectory
            + "/rooms/room_"
            + str(room.getX())
            + "_"
            + str(room.getY())
            + ".json"
        )
        _logger.info("saving room", path=roomPath)
        if not os.path.exists(self.config.pathToSaveDirectory + "/rooms"):
            os.makedirs(self.config.pathToSaveDirectory + "/rooms")

        jsonRoom = self.roomJsonReaderWriter.generateJsonForRoom(room)
        with open(roomPath, "w") as outfile:
            json.dump(jsonRoom, outfile, indent=4)

    def buildRoomPath(self, roomX, roomY):
        return (
            self.config.pathToSaveDirectory
            + "/rooms/room_"
            + str(roomX)
            + "_"
            + str(roomY)
            + ".json"
        )
