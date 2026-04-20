import json
import os
from uuid import UUID

import jsonschema
from config.config import Config
from entity.apple import Apple
from entity.banana import Banana
from entity.bearMeat import BearMeat
from entity.bed import Bed
from entity.campfire import Campfire
from entity.chickenMeat import ChickenMeat
from entity.coalOre import CoalOre
from entity.excrement import Excrement
from entity.fence import Fence
from entity.food import Food
from entity.grass import Grass
from entity.ironOre import IronOre
from entity.jungleWood import JungleWood
from entity.leaves import Leaves
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from entity.matureCrop import MatureCrop
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.stoneBed import StoneBed
from entity.stoneFloor import StoneFloor
from entity.wheat import Wheat
from entity.wheatSeed import WheatSeed
from entity.woodFloor import WoodFloor
from entity.youngCrop import YoungCrop
from lib.graphik.src.graphik import Graphik
from lib.pyenvlib.grid import Grid
from lib.pyenvlib.location import Location
from gameLogging.logger import getLogger

from world.room import Room
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


class RoomJsonReaderWriter:
    def __init__(
        self, gridSize, graphik: Graphik, tickCounter: TickCounter, config: Config
    ):
        self.gridSize = gridSize
        self.graphik = graphik
        self.tickCounter = tickCounter
        self.config = config
        with open("schemas/room.json", encoding="utf-8") as roomSchemaFile:
            self.roomSchema = json.load(roomSchemaFile)
        self.livingEntities = dict()
        self.entityConstructors = {
            "Apple": Apple,
            "CoalOre": CoalOre,
            "Grass": Grass,
            "IronOre": IronOre,
            "JungleWood": JungleWood,
            "Leaves": Leaves,
            "OakWood": OakWood,
            "Stone": Stone,
            "Banana": Banana,
            "ChickenMeat": ChickenMeat,
            "BearMeat": BearMeat,
            "WoodFloor": WoodFloor,
            "Bed": Bed,
            "StoneFloor": StoneFloor,
            "StoneBed": StoneBed,
            "Fence": Fence,
            "Campfire": Campfire,
            "WheatSeed": WheatSeed,
            "Wheat": Wheat,
        }

    def saveRoom(self, room, path):
        _logger.info("saving room", path=path, roomX=room.getX(), roomY=room.getY())
        roomJson = self.generateJsonForRoom(room)
        if not os.path.exists(self.config.pathToSaveDirectory + "/rooms"):
            os.makedirs(self.config.pathToSaveDirectory + "/rooms")
        with open(path, "w") as outfile:
            json.dump(roomJson, outfile, indent=4)

    def loadRoom(self, path):
        _logger.info("loading room", path=path)
        with open(path) as json_file:
            roomJson = json.load(json_file)
            return self.generateRoomFromJson(roomJson)

    def generateJsonForRoom(self, room):
        roomJson = {}
        roomJson["backgroundColor"] = str(room.getBackgroundColor())
        roomJson["x"] = room.getX()
        roomJson["y"] = room.getY()
        roomJson["name"] = room.getName()
        roomJson["id"] = str(room.getID())
        roomJson["livingEntityIds"] = [
            str(entityId) for entityId in room.getLivingEntities().keys()
        ]
        roomJson["grid"] = self.generateJsonForGrid(room.getGrid())
        roomJson["creationDate"] = str(room.getCreationDate())

        # validate json with schema
        jsonschema.validate(roomJson, self.roomSchema)
        return roomJson

    def generateJsonForGrid(self, grid):
        gridJson = {}
        gridJson["id"] = str(grid.getID())
        gridJson["columns"] = grid.getColumns()
        gridJson["rows"] = grid.getRows()
        gridJson["locations"] = self.generateJsonForLocations(grid.getLocations())
        return gridJson

    def generateJsonForLocations(self, locations):
        locationsJson = []
        for locationId in locations:
            location = locations[locationId]
            locationsJson.append(self.generateJsonForLocation(location))
        return locationsJson

    def generateJsonForLocation(self, location):
        locationJson = {}
        locationJson["id"] = str(location.getID())
        locationJson["x"] = location.getX()
        locationJson["y"] = location.getY()
        locationJson["entities"] = self.generateJsonForEntities(location.getEntities())
        return locationJson

    def generateJsonForEntities(self, entities):
        entitiesJson = []
        for entityId in entities:
            entity = entities[entityId]
            entitiesJson.append(self.generateJsonForEntity(entity))
        return entitiesJson

    def generateJsonForEntity(self, entity):
        entityJson = {}
        entityJson["id"] = str(entity.getID())
        entityJson["entityClass"] = entity.__class__.__name__
        entityJson["name"] = entity.getName()
        entityJson["creationDate"] = str(entity.getCreationDate())
        entityJson["environmentId"] = str(entity.getEnvironmentID())
        entityJson["gridId"] = str(entity.getGridID())
        entityJson["locationId"] = str(entity.getLocationID())
        if isinstance(entity, Food):
            entityJson["energy"] = entity.getEnergy()
        elif isinstance(entity, LivingEntity):
            entityJson["energy"] = entity.getEnergy()
            entityJson["tickCreated"] = entity.getTickCreated()
            entityJson["tickLastReproduced"] = entity.getTickLastReproduced()
            entityJson["imagePath"] = entity.getImagePath()
        elif isinstance(entity, Excrement):
            entityJson["tickCreated"] = entity.getTickCreated()
        elif isinstance(entity, (YoungCrop, MatureCrop)):
            entityJson["tickPlanted"] = entity.getTickPlanted()
        return entityJson

    def generateRoomFromJson(self, roomJson):
        backgroundColor = self._parseBackgroundColor(roomJson["backgroundColor"])
        room = Room(
            roomJson["name"],
            self.gridSize,
            backgroundColor,
            roomJson["x"],
            roomJson["y"],
            self.graphik,
        )
        room.setID(roomJson["id"])
        room.setGrid(self.generateGridFromJson(roomJson["grid"]))

        # add living entities
        room.setLivingEntities(self.livingEntities)
        self.livingEntities = dict()
        return room

    def generateGridFromJson(self, gridJson):
        grid = Grid(self.gridSize, self.gridSize)
        grid.setID(gridJson["id"])
        grid.setLocations(self.generateLocationsFromJson(gridJson["locations"]))
        return grid

    def generateLocationsFromJson(self, locationsJson):
        locations = {}
        for locationJson in locationsJson:
            location = self.generateLocationFromJson(locationJson)
            locations[location.getID()] = location
        return locations

    def generateLocationFromJson(self, locationJson):
        location = Location(locationJson["x"], locationJson["y"])
        location.setID(locationJson["id"])
        location.setEntities(self.generateEntitiesFromJson(locationJson["entities"]))
        return location

    def generateEntitiesFromJson(self, entitiesJson):
        entities = {}
        for entityJson in entitiesJson:
            entity = self.generateEntityFromJson(entityJson)
            if entity is None:
                continue
            entities[entity.getID()] = entity

            if isinstance(entity, LivingEntity):
                self.livingEntities[entity.getID()] = entity
        return entities

    def generateEntityFromJson(self, entityJson):
        entityClass = entityJson["entityClass"]
        if entityClass == "Player":
            return None

        entity = self._createEntity(entityClass, entityJson)
        if entity is None:
            raise ValueError("Unknown entity class: " + entityClass)

        entity.setID(UUID(entityJson["id"]))

        if isinstance(entity, LivingEntity):
            entity.setEnergy(entityJson["energy"])
            entity.setTickCreated(entityJson["tickCreated"])
            entity.setTickLastReproduced(entityJson["tickLastReproduced"])
            entity.setImagePath(entityJson["imagePath"])
        elif isinstance(entity, Food) and "energy" in entityJson:
            entity.setEnergy(entityJson["energy"])

        entity.setEnvironmentID(UUID(entityJson["environmentId"]))
        entity.setGridID(UUID(entityJson["gridId"]))
        entity.setLocationID(entityJson["locationId"])
        entity.setName(entityJson["name"])
        return entity

    def _parseBackgroundColor(self, backgroundColorText):
        colorParts = backgroundColorText.replace("(", "").replace(")", "").split(",")
        red = int(colorParts[0])
        green = int(colorParts[1])
        blue = int(colorParts[2])
        return red, green, blue

    def _createEntity(self, entityClass, entityJson):
        if entityClass == "Bear":
            return Bear(entityJson["tickCreated"])
        if entityClass == "Chicken":
            return Chicken(entityJson["tickCreated"])
        if entityClass == "Excrement":
            return Excrement(entityJson["tickCreated"])
        if entityClass == "YoungCrop":
            return YoungCrop(entityJson["tickPlanted"])
        if entityClass == "MatureCrop":
            return MatureCrop(entityJson["tickPlanted"])

        constructor = self.entityConstructors.get(entityClass)
        if constructor is None:
            return None
        return constructor()
