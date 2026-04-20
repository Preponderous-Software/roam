# @author Copilot
# @since April 20th, 2026
import json
import os
from math import ceil

import jsonschema

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from player.player import Player

_logger = getLogger(__name__)


@component
class PlayerRepository:
    """Handles all persistence for player state (location, attributes, inventory)."""

    def __init__(self, config: Config, player: Player):
        self.config = config
        self.player = player

    def saveLocation(self, currentRoom):
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

    def loadLocation(self, mapInstance):
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

    def saveAttributes(self):
        jsonPlayerAttributes = {"energy": ceil(self.player.getEnergy())}

        with open("schemas/playerAttributes.json") as f:
            playerAttributesSchema = json.load(f)
        jsonschema.validate(jsonPlayerAttributes, playerAttributesSchema)

        path = self.config.pathToSaveDirectory + "/playerAttributes.json"
        _logger.info("saving player attributes", path=path)
        with open(path, "w") as f:
            json.dump(jsonPlayerAttributes, f, indent=4)

    def loadAttributes(self):
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

    def saveInventory(self, inventoryJsonReaderWriter):
        inventoryJsonReaderWriter.saveInventory(
            self.player.getInventory(),
            self.config.pathToSaveDirectory + "/playerInventory.json",
        )

    def loadInventory(self, inventoryJsonReaderWriter):
        inventory = inventoryJsonReaderWriter.loadInventory(
            self.config.pathToSaveDirectory + "/playerInventory.json"
        )
        if inventory is not None:
            self.player.setInventory(inventory)
