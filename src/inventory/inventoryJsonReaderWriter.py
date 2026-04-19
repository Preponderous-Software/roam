import json
import os
from uuid import UUID

import jsonschema
from entity.apple import Apple
from entity.banana import Banana
from entity.bearMeat import BearMeat
from entity.bed import Bed
from entity.campfire import Campfire
from entity.chickenMeat import ChickenMeat
from entity.coalOre import CoalOre
from entity.fence import Fence
from entity.food import Food
from entity.grass import Grass
from entity.ironOre import IronOre
from entity.jungleWood import JungleWood
from entity.leaves import Leaves
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.stoneBed import StoneBed
from entity.stoneFloor import StoneFloor
from entity.woodFloor import WoodFloor
from inventory.inventory import Inventory

# Simple entity classes that require no special constructor arguments
_SIMPLE_ENTITY_CONSTRUCTORS = {
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
}

# Food entity classes that have a restorable energy value
_FOOD_ENTITY_CLASSES = {"Apple", "Banana", "ChickenMeat", "BearMeat"}

# Living entity classes that need a tickCreated constructor argument
_LIVING_ENTITY_CONSTRUCTORS = {
    "Bear": Bear,
    "Chicken": Chicken,
}


class InventoryJsonReaderWriter:
    def __init__(self, config):
        self.config = config

    def saveInventory(self, inventory: Inventory, path):
        print("Saving inventory to " + path)
        toReturn = {"inventorySlots": []}
        slotIndex = 0
        for slot in inventory.getInventorySlots():
            slotContents = []
            for entity in slot.getContents():
                entityData = {
                    "entityId": str(entity.getID()),
                    "entityClass": entity.__class__.__name__,
                    "name": entity.getName(),
                    "assetPath": entity.getImagePath(),
                }
                if isinstance(entity, Food):
                    entityData["energy"] = entity.getEnergy()
                if isinstance(entity, LivingEntity):
                    entityData["energy"] = entity.getEnergy()
                    entityData["tickCreated"] = entity.getTickCreated()
                    entityData["tickLastReproduced"] = entity.getTickLastReproduced()
                    entityData["imagePath"] = entity.getImagePath()
                slotContents.append(entityData)
            toReturn["inventorySlots"].append(
                {"slotIndex": slotIndex, "slotContents": slotContents}
            )
            slotIndex += 1

        with open("schemas/inventory.json") as f:
            inventorySchema = json.load(f)
        try:
            jsonschema.validate(toReturn, inventorySchema)
        except jsonschema.exceptions.ValidationError as e:
            print(e)

        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)

        with open(path, "w") as f:
            json.dump(toReturn, f, indent=4)

    def loadInventory(self, path):
        print("Loading inventory from " + path)
        inventory = Inventory()
        if not os.path.exists(path):
            return inventory
        with open(path) as f:
            inventoryJson = json.load(f)
        for slot in inventoryJson["inventorySlots"]:
            for entityJson in slot["slotContents"]:
                entity = self._createEntityFromJson(entityJson)
                inventory.placeIntoFirstAvailableInventorySlot(entity)
        return inventory

    def _createEntityFromJson(self, entityJson):
        entityClass = entityJson["entityClass"]

        if entityClass in _LIVING_ENTITY_CONSTRUCTORS:
            return self._createLivingEntity(entityClass, entityJson)

        if entityClass in _SIMPLE_ENTITY_CONSTRUCTORS:
            return self._createSimpleEntity(entityClass, entityJson)

        raise Exception("Unknown entity class: " + entityClass)

    def _createSimpleEntity(self, entityClass, entityJson):
        constructor = _SIMPLE_ENTITY_CONSTRUCTORS[entityClass]
        entity = constructor()
        entity.setID(UUID(entityJson["entityId"]))
        if entityClass in _FOOD_ENTITY_CLASSES and "energy" in entityJson:
            entity.setEnergy(entityJson["energy"])
        return entity

    def _createLivingEntity(self, entityClass, entityJson):
        constructor = _LIVING_ENTITY_CONSTRUCTORS[entityClass]
        entity = constructor(entityJson["tickCreated"])
        entity.setID(UUID(entityJson["entityId"]))
        entity.setEnergy(entityJson["energy"])
        entity.setTickLastReproduced(entityJson["tickLastReproduced"])
        entity.setImagePath(entityJson["imagePath"])
        return entity
