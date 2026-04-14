import json
import os
from uuid import UUID

import jsonschema
from entity.apple import Apple
from entity.banana import Banana
from entity.bed import Bed
from entity.campfire import Campfire
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


class InventoryJsonReaderWriter:
    def __init__(self, config):
        self.config = config

    def saveInventory(self, inventory: Inventory, path):
        print("Saving inventory to " + path)
        toReturn = {}
        toReturn["inventorySlots"] = []
        slotIndex = 0
        for slot in inventory.getInventorySlots():
            slotContents = []
            for entity in slot.getContents():
                toAppend = {}
                toAppend = {
                    "entityId": str(entity.getID()),
                    "entityClass": entity.__class__.__name__,
                    "name": entity.getName(),
                    "assetPath": entity.getImagePath(),
                }
                if isinstance(entity, Food):
                    toAppend["energy"] = entity.getEnergy()
                if isinstance(entity, LivingEntity):
                    toAppend["energy"] = entity.getEnergy()
                    toAppend["tickCreated"] = entity.getTickCreated()
                    toAppend["tickLastReproduced"] = entity.getTickLastReproduced()
                    toAppend["imagePath"] = entity.getImagePath()
                slotContents.append(toAppend)
            toReturn["inventorySlots"].append(
                {"slotIndex": slotIndex, "slotContents": slotContents}
            )
            slotIndex += 1

        # Validate the JSON
        with open("schemas/inventory.json") as f:
            inventorySchema = json.load(f)
        try:
            jsonschema.validate(toReturn, inventorySchema)
        except jsonschema.exceptions.ValidationError as e:
            print(e)

        # create save directory if it doesn't exist
        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)

        # print the JSON to file
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
                entityClass = entityJson["entityClass"]
                if entityClass == "Apple":
                    apple = Apple()
                    apple.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(apple)
                elif entityClass == "CoalOre":
                    coalOre = CoalOre()
                    coalOre.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(coalOre)
                elif entityClass == "Grass":
                    grass = Grass()
                    grass.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(grass)
                elif entityClass == "IronOre":
                    ironOre = IronOre()
                    ironOre.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(ironOre)
                elif entityClass == "JungleWood":
                    jungleWood = JungleWood()
                    jungleWood.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(jungleWood)
                elif entityClass == "Leaves":
                    leaves = Leaves()
                    leaves.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(leaves)
                elif entityClass == "OakWood":
                    oakWood = OakWood()
                    oakWood.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(oakWood)
                elif entityClass == "Stone":
                    stone = Stone()
                    stone.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(stone)
                elif entityClass == "Bear":
                    bear = Bear(entityJson["tickCreated"])
                    bear.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(bear)
                    bear.setEnergy(entityJson["energy"])
                    bear.setTickLastReproduced(entityJson["tickLastReproduced"])
                    bear.setImagePath(entityJson["imagePath"])
                elif entityClass == "Chicken":
                    chicken = Chicken(entityJson["tickCreated"])
                    chicken.setID(UUID(entityJson["entityId"]))
                    chicken.setEnergy(entityJson["energy"])
                    chicken.setTickLastReproduced(entityJson["tickLastReproduced"])
                    chicken.setImagePath(entityJson["imagePath"])
                    inventory.placeIntoFirstAvailableInventorySlot(chicken)
                elif entityClass == "Banana":
                    banana = Banana()
                    banana.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(banana)
                elif entityClass == "WoodFloor":
                    woodFloor = WoodFloor()
                    woodFloor.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(woodFloor)
                elif entityClass == "Bed":
                    bed = Bed()
                    bed.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(bed)
                elif entityClass == "StoneFloor":
                    stoneFloor = StoneFloor()
                    stoneFloor.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(stoneFloor)
                elif entityClass == "StoneBed":
                    stoneBed = StoneBed()
                    stoneBed.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(stoneBed)
                elif entityClass == "Fence":
                    fence = Fence()
                    fence.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(fence)
                elif entityClass == "Campfire":
                    campfire = Campfire()
                    campfire.setID(UUID(entityJson["entityId"]))
                    inventory.placeIntoFirstAvailableInventorySlot(campfire)
                else:
                    raise Exception(
                        "Unknown entity class: " + entityJson["entityClass"]
                    )
        return inventory
