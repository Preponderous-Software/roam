import json
import math
from math import ceil
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import jsonschema
import pygame
from appContainer import component
from di import Container
from entity.apple import Apple
from entity.bed import Bed
from entity.campfire import Campfire
from config.config import Config
from config.keyBindings import KeyBindings
from entity.banana import Banana
from entity.bearMeat import BearMeat
from entity.chickenMeat import ChickenMeat
from entity.coalOre import CoalOre
from entity.fence import Fence
from entity.ironOre import IronOre
from entity.jungleWood import JungleWood
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
from inventory.inventorySlot import InventorySlot
from mapimage.mapImageUpdater import MapImageUpdater
from screen.screenType import ScreenType
from screen.screenshotHelper import takeScreenshot
from stats.stats import Stats
from ui.energyBar import EnergyBar
from lib.graphik.src.graphik import Graphik
from entity.grass import Grass
from lib.pyenvlib.grid import Grid
from entity.stone import Stone
from entity.stoneBed import StoneBed
from entity.stoneFloor import StoneFloor
from entity.leaves import Leaves
from lib.pyenvlib.location import Location
from world.room import Room
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.roomPreloader import RoomPreloader
from world.tickCounter import TickCounter
from world.map import Map
from player.player import Player
from ui.status import Status
from ui.hotbarLayout import (
    HOTBAR_SLOT_SIZE,
    HOTBAR_SLOT_GAP,
    HOTBAR_PADDING,
    HOTBAR_BOTTOM_OFFSET,
)
from ui.hudDragManager import HudDragManager
from entity.oakWood import OakWood
from entity.wheat import Wheat
from entity.wheatSeed import WheatSeed
from entity.woodFloor import WoodFloor
from entity.youngCrop import YoungCrop
from entity.matureCrop import MatureCrop
from gameLogging.logger import getLogger

_logger = getLogger(__name__)

MIDDLE_MOUSE_BUTTON = 2


# @author Daniel McCoy Stephenson
# @since August 16th, 2022
@component
class WorldScreen:
    def __init__(
        self,
        graphik: Graphik,
        config: Config,
        status: Status,
        tickCounter: TickCounter,
        stats: Stats,
        player: Player,
        container: Container,
        keyBindings: KeyBindings,
    ):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.tickCounter = tickCounter
        self.stats = stats
        self.player = player
        self.container = container
        self.keyBindings = keyBindings
        self.running = True
        self.showInventory = False
        self.nextScreen = ScreenType.OPTIONS_SCREEN
        self.changeScreen = False
        self.roomJsonReaderWriter = self.container.resolve(RoomJsonReaderWriter)
        self.roomPreloader = self.container.resolve(RoomPreloader)
        self.mapImageUpdater = self.container.resolve(MapImageUpdater)
        self.hudDragManager = self.container.resolve(HudDragManager)
        self.minimapScaleFactor = 0.10
        self.minimapX = 5
        self.minimapY = 5
        self._cachedMiniMapImage = None
        self._miniMapLastLoadTick = 0
        self._saveExecutor = ThreadPoolExecutor(
            max_workers=1
        )  # serialize save operations off main thread
        self._saveInProgress = False
        self._saveLock = threading.Lock()
        self._pngSavePending = set()
        self.cursorSlot = InventorySlot()
        self.clock = pygame.time.Clock()
        self.showHelp = False

    def initialize(self):
        self.map = self.container.resolve(Map)

        # load player location if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/playerLocation.json"):
            self.loadPlayerLocationFromFile()
        else:
            self.currentRoom = self.map.getRoom(0, 0)
            if self.currentRoom == -1:
                self.currentRoom = self.map.generateNewRoom(0, 0)
            self.currentRoom.addEntity(self.player)
            self.stats.incrementRoomsExplored()

        # load player attributes if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/playerAttributes.json"):
            self.loadPlayerAttributesFromFile()

        # load stats if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/stats.json"):
            self.stats.load()

        # load tick if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/tick.json"):
            self.tickCounter.load()

        # load player inventory if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/playerInventory.json"):
            self.loadPlayerInventoryFromFile()

        self.initializeLocationWidthAndHeight()

        # pre-load nearby rooms in the background
        self.roomPreloader.preloadNearbyRooms(
            self.currentRoom.getX(), self.currentRoom.getY(), self.map
        )

        self.status.set("Entered the world")
        self.energyBar = self.container.resolve(EnergyBar)

        self.hudDragManager.register("hotbar", self._getHotbarDefaultRect)
        self.hudDragManager.register("status", lambda: self.status.getDefaultRect())
        self.hudDragManager.register(
            "energyBar", lambda: self.energyBar.getDefaultRect()
        )
        self.hudDragManager.register("minimap", self._getMinimapDefaultRect)

        _logger.info(
            "world screen initialized",
            roomX=self.currentRoom.getX(),
            roomY=self.currentRoom.getY(),
        )

    def initializeLocationWidthAndHeight(self):
        gameArea = self.graphik.getGameAreaRect()
        locationWidth = gameArea.width / self.currentRoom.getGrid().getRows()
        locationHeight = gameArea.height / self.currentRoom.getGrid().getColumns()

        locationSizeChanged = (
            not hasattr(self, "locationWidth")
            or not hasattr(self, "locationHeight")
            or self.locationWidth != locationWidth
            or self.locationHeight != locationHeight
        )

        self.locationWidth = locationWidth
        self.locationHeight = locationHeight

        if locationSizeChanged:
            Room._scaledImageCache.clear()

    def updateConfigWindowSize(self):
        w, h = self.graphik.getGameDisplay().get_size()
        minSize = self.config.MIN_WINDOW_SIZE
        self.config.displayWidth = max(w, minSize)
        self.config.displayHeight = max(h, minSize)

    def getOrLoadRoom(self, x, y):
        room = self.map.getRoom(x, y)
        if room == -1:
            room = self.map.generateNewRoom(x, y)
        return room

    def printStatsToConsole(self):
        _logger.info(
            "statistics",
            score=self.stats.getScore(),
            roomsExplored=self.stats.getRoomsExplored(),
            foodEaten=self.stats.getFoodEaten(),
            deaths=self.stats.getNumberOfDeaths(),
        )
    def getLocationOfPlayer(self):
        return self.map.getLocationOfEntity(self.player, self.currentRoom)

    def getLocationDirection(self, direction: int, grid: Grid, location: Location):
        if direction == 0:
            return grid.getUp(location)
        elif direction == 1:
            return grid.getLeft(location)
        elif direction == 2:
            return grid.getDown(location)
        elif direction == 3:
            return grid.getRight(location)
        elif direction == -1:
            return -1

    def getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection(self):
        location = self.getLocationOfPlayer()
        x = self.currentRoom.getX()
        y = self.currentRoom.getY()

        if self.ifCorner(location):
            direction = self.player.getDirection()
            if location.getX() == 0 and location.getY() == 0:
                if direction == 0:
                    y -= 1
                elif direction == 1:
                    x -= 1
            elif location.getX() == self.config.gridSize - 1 and location.getY() == 0:
                if direction == 0:
                    y -= 1
                elif direction == 3:
                    x += 1
            elif location.getX() == 0 and location.getY() == self.config.gridSize - 1:
                if direction == 2:
                    y += 1
                elif direction == 1:
                    x -= 1
            elif (
                location.getX() == self.config.gridSize - 1
                and location.getY() == self.config.gridSize - 1
            ):
                if direction == 2:
                    y += 1
                elif direction == 3:
                    x += 1
        else:
            if location.getX() == self.config.gridSize - 1:
                x += 1
            elif location.getX() == 0:
                x -= 1
            elif location.getY() == self.config.gridSize - 1:
                y += 1
            elif location.getY() == 0:
                y -= 1
        return x, y

    def getCoordinatesForNewRoomBasedOnLivingEntityLocation(self, livingEntity):
        locationId = livingEntity.getLocationID()
        location = self.currentRoom.getGrid().getLocation(locationId)

        x = self.currentRoom.getX()
        y = self.currentRoom.getY()
        if self.ifCorner(location):
            raise Exception("corner movement not implemented yet")
        else:
            if location.getX() == self.config.gridSize - 1:
                x += 1
            elif location.getX() == 0:
                x -= 1
            elif location.getY() == self.config.gridSize - 1:
                y += 1
            elif location.getY() == 0:
                y -= 1
        return x, y

    def ifCorner(self, location: Location):
        return (
            (location.getX() == 0 and location.getY() == 0)
            or (location.getX() == self.config.gridSize - 1 and location.getY() == 0)
            or (location.getX() == 0 and location.getY() == self.config.gridSize - 1)
            or (
                location.getX() == self.config.gridSize - 1
                and location.getY() == self.config.gridSize - 1
            )
        )

    def saveCurrentRoomToFile(self):
        self.saveRoomToFile(self.currentRoom)

    def saveRoomToFile(self, room: Room):
        roomPath = (
            self.config.pathToSaveDirectory
            + "/rooms/room_"
            + str(room.getX())
            + "_"
            + str(room.getY())
            + ".json"
        )
        self.roomJsonReaderWriter.saveRoom(room, roomPath)

    def saveRoomToFileAsync(self, room: Room):
        """Save a room to file on the background thread (non-blocking).
        Prepares the JSON snapshot on the main thread to avoid dict-iteration
        races, then writes the file in the background."""
        roomPath = (
            self.config.pathToSaveDirectory
            + "/rooms/room_"
            + str(room.getX())
            + "_"
            + str(room.getY())
            + ".json"
        )
        try:
            roomJson = self.roomJsonReaderWriter.generateJsonForRoom(room)
        except Exception as e:
            _logger.error("error preparing room snapshot", error=str(e))
            return
        self._saveExecutor.submit(self._writeJsonToFile, roomJson, roomPath)

    def _writeJsonToFile(self, data, path):
        """Write a pre-built JSON dict to disk. Runs on background thread."""
        try:
            dirPath = os.path.dirname(path)
            if not os.path.exists(dirPath):
                os.makedirs(dirPath, exist_ok=True)
            with open(path, "w") as outfile:
                json.dump(data, outfile, indent=4)
        except Exception as e:
            _logger.error("error writing JSON file", error=str(e), path=path)

    def changeRooms(self):
        x, y = self.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection()

        if self.config.worldBorder != 0 and (
            abs(x) > self.config.worldBorder or abs(y) > self.config.worldBorder
        ):
            self.status.set("Reached world border")
            return

        playerLocation = self.getLocationOfPlayer()
        self.currentRoom.removeEntity(self.player)

        room = self.map.getRoom(x, y)
        if room == -1:
            # attempt to load room if file exists, otherwise generate new room
            nextRoomPath = (
                self.config.pathToSaveDirectory
                + "/rooms/room_"
                + str(x)
                + "_"
                + str(y)
                + ".json"
            )
            if os.path.exists(nextRoomPath):
                roomJsonReaderWriter = RoomJsonReaderWriter(
                    self.config.gridSize, self.graphik, self.tickCounter, self.config
                )
                room = roomJsonReaderWriter.loadRoom(nextRoomPath)
                self.map.addRoom(room)
                self.currentRoom = room
                self.status.set("Area loaded")
            else:
                x, y = self.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection()
                self.currentRoom = self.map.generateNewRoom(x, y)
                self.status.set("New area discovered")
                self.stats.incrementScore()
                self.stats.incrementRoomsExplored()
        else:
            self.currentRoom = room

        targetX = playerLocation.getX()
        targetY = playerLocation.getY()

        minCoord = 0
        maxCoord = self.config.gridSize - 1

        # if in corner
        if self.ifCorner(playerLocation):
            playerDirection = self.player.getDirection()
            # if top left corner
            if playerLocation.getX() == 0 and playerLocation.getY() == 0:
                if playerDirection == 0:
                    targetY = maxCoord
                elif playerDirection == 1:
                    targetX = maxCoord
            # if top right corner
            elif playerLocation.getX() == maxCoord and playerLocation.getY() == 0:
                if playerDirection == 0:
                    targetY = maxCoord
                elif playerDirection == 3:
                    targetX = minCoord
            # if bottom left corner
            elif playerLocation.getX() == 0 and playerLocation.getY() == maxCoord:
                if playerDirection == 2:
                    targetY = minCoord
                elif playerDirection == 1:
                    targetX = maxCoord
            # if bottom right corner
            elif (
                playerLocation.getX() == maxCoord and playerLocation.getY() == maxCoord
            ):
                if playerDirection == 2:
                    targetY = minCoord
                elif playerDirection == 3:
                    targetX = minCoord
        else:
            if playerLocation.getX() == 0:
                targetX = maxCoord
            elif playerLocation.getX() == maxCoord:
                targetX = minCoord
            elif playerLocation.getY() == 0:
                targetY = maxCoord
            elif playerLocation.getY() == maxCoord:
                targetY = minCoord

        targetLocation = self.currentRoom.getGrid().getLocationByCoordinates(
            targetX, targetY
        )
        self.currentRoom.addEntityToLocation(self.player, targetLocation)
        self.initializeLocationWidthAndHeight()

        _logger.info(
            "room transition",
            roomX=self.currentRoom.getX(),
            roomY=self.currentRoom.getY(),
        )

        # pre-load nearby rooms in the background
        self.roomPreloader.preloadNearbyRooms(
            self.currentRoom.getX(), self.currentRoom.getY(), self.map
        )

    def movePlayer(self, direction: int):
        if self.player.isCrouching():
            return

        location = self.getLocationOfPlayer()
        newLocation = self.getLocationDirection(
            direction, self.currentRoom.getGrid(), location
        )

        if newLocation == -1:
            # we're at a border
            self.changeRooms()
            self.save()
            return

        if self.locationContainsSolidEntity(newLocation):
            if self.config.pushableStone and self.tryPushStone(newLocation, direction):
                if self.locationContainsSolidEntity(newLocation):
                    return
            else:
                return

        # if bear is in the new location, kill the player
        for entityId in list(newLocation.getEntities().keys()):
            entity = newLocation.getEntity(entityId)
            if isinstance(entity, Bear):
                self.player.kill()
                return

        if self.player.needsEnergy():
            # search for food to eat
            for entityId in list(newLocation.getEntities().keys()):
                entity = newLocation.getEntity(entityId)
                if self.player.canEat(entity):
                    newLocation.removeEntity(entity)
                    self.player.addEnergy(entity.getEnergy())

                    self.stats.incrementFoodEaten()

                    self.status.set("Ate " + entity.getName())

                    self.stats.incrementScore()

        # move player
        location.removeEntity(self.player)
        newLocation.addEntity(self.player)

        # decrease energy
        self.player.removeEnergy(self.config.playerMovementEnergyCost)
        self.player.setTickLastMoved(self.tickCounter.getTick())

    def canBePickedUp(self, entity):
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
            ChickenMeat,
            BearMeat,
            WoodFloor,
            Bed,
            StoneFloor,
            StoneBed,
            Fence,
            Campfire,
            WheatSeed,
            YoungCrop,
            MatureCrop,
            Wheat,
        ]
        for itemType in itemTypes:
            if isinstance(entity, itemType):
                return True
        return False

    def getLocationAndRoomAtMousePosition(self):
        x, y = pygame.mouse.get_pos()
        gameArea = self.graphik.getGameAreaRect()
        if self.config.cameraFollowPlayer:
            playerLocation = self.getLocationOfPlayer()
            playerPixelX = (
                playerLocation.getX() * self.locationWidth + self.locationWidth / 2
            )
            playerPixelY = (
                playerLocation.getY() * self.locationHeight + self.locationHeight / 2
            )
            centerX = gameArea.x + gameArea.width / 2
            centerY = gameArea.y + gameArea.height / 2
            offsetX = centerX - playerPixelX
            offsetY = centerY - playerPixelY
            worldGridX = int((x - offsetX) // self.locationWidth)
            worldGridY = int((y - offsetY) // self.locationHeight)

            gridSize = self.config.gridSize
            roomDX = math.floor(worldGridX / gridSize)
            roomDY = math.floor(worldGridY / gridSize)
            localX = worldGridX - roomDX * gridSize
            localY = worldGridY - roomDY * gridSize

            if roomDX == 0 and roomDY == 0:
                targetRoom = self.currentRoom
            else:
                currentRoomX = self.currentRoom.getX()
                currentRoomY = self.currentRoom.getY()
                targetRoomX = currentRoomX + roomDX
                targetRoomY = currentRoomY + roomDY

                if self.config.worldBorder != 0 and (
                    abs(targetRoomX) > self.config.worldBorder
                    or abs(targetRoomY) > self.config.worldBorder
                ):
                    return (-1, None)
                targetRoom = self.getOrLoadRoom(targetRoomX, targetRoomY)

            location = targetRoom.getGrid().getLocationByCoordinates(localX, localY)
            return (location, targetRoom)
        else:
            gridX = int((x - gameArea.x) // self.locationWidth)
            gridY = int((y - gameArea.y) // self.locationHeight)
            location = self.currentRoom.getGrid().getLocationByCoordinates(gridX, gridY)
            return (location, self.currentRoom)

    def getLocationAtMousePosition(self):
        location, room = self.getLocationAndRoomAtMousePosition()
        return location

    def isLocationTooFar(self, targetLocation, targetRoom):
        distanceLimit = self.config.playerInteractionDistanceLimit
        playerLocation = self.getLocationOfPlayer()
        gridSize = self.config.gridSize
        worldTargetX = targetRoom.getX() * gridSize + targetLocation.getX()
        worldTargetY = targetRoom.getY() * gridSize + targetLocation.getY()
        worldPlayerX = self.currentRoom.getX() * gridSize + playerLocation.getX()
        worldPlayerY = self.currentRoom.getY() * gridSize + playerLocation.getY()
        return (
            abs(worldTargetX - worldPlayerX) > distanceLimit
            or abs(worldTargetY - worldPlayerY) > distanceLimit
        )

    def executeGatherAction(self):
        targetLocation, targetRoom = self.getLocationAndRoomAtMousePosition()

        if targetLocation == -1:
            self.status.set("Nothing to pick up here")
            return

        if self.isLocationTooFar(targetLocation, targetRoom):
            self.status.set("Too far away")
            return

        # Check for crop interactions first
        for entityId in list(reversed(targetLocation.getEntities())):
            entity = targetLocation.getEntity(entityId)
            if isinstance(entity, YoungCrop):
                self.status.set("Crop is not ready")
                return
            if isinstance(entity, MatureCrop):
                wheat = Wheat()
                result = self.player.getInventory().placeIntoFirstAvailableInventorySlot(
                    wheat
                )
                if result == False:
                    self.status.set("Inventory full")
                    return
                targetRoom.removeEntity(entity)
                self.status.set("Harvested Wheat")
                self.player.removeEnergy(self.config.playerInteractionEnergyCost)
                self.player.setTickLastGathered(self.tickCounter.getTick())
                return

        toRemove = -1
        reversedEntityIdList = list(reversed(targetLocation.getEntities()))
        for entityId in reversedEntityIdList:
            entity = targetLocation.getEntity(entityId)
            if self.canBePickedUp(entity):
                toRemove = entity
                break

        if toRemove == -1:
            return

        result = self.player.getInventory().placeIntoFirstAvailableInventorySlot(
            toRemove
        )
        if result == False:
            self.status.set("Inventory full")
            return
        targetRoom.removeEntity(toRemove)
        if isinstance(toRemove, LivingEntity):
            targetRoom.removeLivingEntity(toRemove)
        self.status.set("Picked up " + entity.getName())
        self.player.removeEnergy(self.config.playerInteractionEnergyCost)
        self.player.setTickLastGathered(self.tickCounter.getTick())

    def getLocationInFrontOfPlayer(self):
        lastDirectionPlayerWasFacing = self.player.getLastDirection()
        directionPlayerIsFacing = self.player.getDirection()
        direction = lastDirectionPlayerWasFacing
        if direction == -1:
            # player was standing still
            direction = directionPlayerIsFacing
        playerLocation = self.getLocationOfPlayer()
        return self.getLocationDirection(
            direction, self.currentRoom.grid, playerLocation
        )

    def locationContainsSolidEntity(self, location):
        for entityId in list(location.getEntities().keys()):
            entity = location.getEntity(entityId)
            if entity.isSolid():
                return True
        return False

    def tryPushStone(self, location, direction):
        # find a Stone entity in the location
        stoneEntity = None
        for entityId in list(location.getEntities().keys()):
            entity = location.getEntity(entityId)
            if isinstance(entity, Stone):
                stoneEntity = entity
                break

        if stoneEntity is None:
            return False

        # get the location beyond the stone in the same direction
        pushDestination = self.getLocationDirection(
            direction, self.currentRoom.getGrid(), location
        )

        if pushDestination == -1:
            # stone is at a room border, try to push into adjacent room
            return self.tryPushStoneToAdjacentRoom(stoneEntity, location, direction)

        if self.locationContainsSolidEntity(pushDestination):
            return False

        # push the stone
        location.removeEntity(stoneEntity)
        pushDestination.addEntity(stoneEntity)
        return True

    def tryPushStoneToAdjacentRoom(self, stoneEntity, location, direction):
        # compute adjacent room coordinates based on push direction
        roomX = self.currentRoom.getX()
        roomY = self.currentRoom.getY()
        if direction == 0:
            roomY -= 1
        elif direction == 1:
            roomX -= 1
        elif direction == 2:
            roomY += 1
        elif direction == 3:
            roomX += 1

        # check world border
        if self.config.worldBorder != 0 and (
            abs(roomX) > self.config.worldBorder or abs(roomY) > self.config.worldBorder
        ):
            return False

        adjacentRoom = self.getOrLoadRoom(roomX, roomY)

        # compute entry location on the opposite side of the adjacent room
        maxCoord = self.config.gridSize - 1
        targetX = location.getX()
        targetY = location.getY()
        if direction == 0:
            targetY = maxCoord
        elif direction == 1:
            targetX = maxCoord
        elif direction == 2:
            targetY = 0
        elif direction == 3:
            targetX = 0

        targetLocation = adjacentRoom.getGrid().getLocationByCoordinates(
            targetX, targetY
        )

        if targetLocation == -1:
            return False

        if self.locationContainsSolidEntity(targetLocation):
            return False

        # push stone into adjacent room
        location.removeEntity(stoneEntity)
        targetLocation.addEntity(stoneEntity)
        self.saveRoomToFileAsync(adjacentRoom)
        return True

    def executePlaceAction(self):
        if self.player.getInventory().getNumTakenInventorySlots() == 0:
            self.status.set("No items to place")
            return

        targetLocation, targetRoom = self.getLocationAndRoomAtMousePosition()
        if targetLocation == -1:
            self.status.set("Cannot place here")
            return
        if targetLocation == -2:
            self.status.set("Stop moving to place items")
            return
        if self.locationContainsSolidEntity(targetLocation):
            self.status.set("Location is blocked")
            return

        if self.isLocationTooFar(targetLocation, targetRoom):
            self.status.set("Too far away")
            return

        # if living entity is in the location, don't place
        for entityId in list(targetLocation.getEntities().keys()):
            entity = targetLocation.getEntity(entityId)
            if isinstance(entity, LivingEntity):
                self.status.set("Blocked by " + entity.getName())
                return

        self.player.removeEnergy(self.config.playerInteractionEnergyCost)

        inventorySlot = self.player.getInventory().getSelectedInventorySlot()
        if inventorySlot.isEmpty():
            self.status.set("Select an item first (1-0)")
            return

        # Handle wheat seed planting
        selectedItem = inventorySlot.getContents()[0]
        if isinstance(selectedItem, WheatSeed):
            hasGrass = False
            for entityId in list(targetLocation.getEntities().keys()):
                entity = targetLocation.getEntity(entityId)
                if isinstance(entity, Grass):
                    hasGrass = True
                    break
            if not hasGrass:
                self.status.set("Must plant on grass")
                return
            # Remove grass from location
            for entityId in list(targetLocation.getEntities().keys()):
                entity = targetLocation.getEntity(entityId)
                if isinstance(entity, Grass):
                    targetLocation.removeEntity(entity)
                    break
            # Consume seed from inventory
            self.player.getInventory().removeSelectedItem()
            # Place young crop
            youngCrop = YoungCrop(self.tickCounter.getTick())
            targetRoom.addEntityToLocation(youngCrop, targetLocation)
            self.status.set("Planted Wheat Seed")
            self.player.setTickLastPlaced(self.tickCounter.getTick())
            return

        toPlace = self.player.getInventory().removeSelectedItem()

        if toPlace == -1:
            return

        targetRoom.addEntityToLocation(toPlace, targetLocation)
        if isinstance(toPlace, LivingEntity):
            targetRoom.addLivingEntity(toPlace)
        self.status.set("Placed " + toPlace.getName())
        self.player.setTickLastPlaced(self.tickCounter.getTick())

    def changeSelectedInventorySlot(self, index):
        self.player.getInventory().setSelectedInventorySlotIndex(index)
        inventorySlot = self.player.getInventory().getSelectedInventorySlot()
        if inventorySlot.isEmpty():
            self.status.set("Empty slot")
            return
        item = inventorySlot.getContents()[0]
        self.status.set("Selected " + item.getName())

    def handleKeyDownEvent(self, key):
        kb = self.keyBindings
        if key == pygame.K_ESCAPE:
            self.nextScreen = ScreenType.OPTIONS_SCREEN
            self.changeScreen = True
        elif key == kb.getKey("move_up") or key == kb.getKey("alt_move_up"):
            self.player.setDirection(0)
            if self.checkPlayerMovementCooldown(self.player.getTickLastMoved()):
                self.movePlayer(self.player.direction)
        elif key == kb.getKey("move_left") or key == kb.getKey("alt_move_left"):
            self.player.setDirection(1)
            if self.checkPlayerMovementCooldown(self.player.getTickLastMoved()):
                self.movePlayer(self.player.direction)
        elif key == kb.getKey("move_down") or key == kb.getKey("alt_move_down"):
            self.player.setDirection(2)
            if self.checkPlayerMovementCooldown(self.player.getTickLastMoved()):
                self.movePlayer(self.player.direction)
        elif key == kb.getKey("move_right") or key == kb.getKey("alt_move_right"):
            self.player.setDirection(3)
            if self.checkPlayerMovementCooldown(self.player.getTickLastMoved()):
                self.movePlayer(self.player.direction)
        elif key == kb.getKey("screenshot"):
            takeScreenshot(self.graphik.getGameDisplay())
            self.status.set("Screenshot saved")
        elif key == kb.getKey("run"):
            self.player.setMovementSpeed(
                self.player.getMovementSpeed() * self.config.runSpeedFactor
            )
        elif key == kb.getKey("crouch"):
            self.player.setCrouching(True)
        elif key == kb.getKey("inventory"):
            self.switchToInventoryScreen()
            if self.player.isGathering():
                self.player.setGathering(False)
            if self.player.isPlacing():
                self.player.setPlacing(False)
        elif key == kb.getKey("hotbar_1"):
            self.changeSelectedInventorySlot(0)
        elif key == kb.getKey("hotbar_2"):
            self.changeSelectedInventorySlot(1)
        elif key == kb.getKey("hotbar_3"):
            self.changeSelectedInventorySlot(2)
        elif key == kb.getKey("hotbar_4"):
            self.changeSelectedInventorySlot(3)
        elif key == kb.getKey("hotbar_5"):
            self.changeSelectedInventorySlot(4)
        elif key == kb.getKey("hotbar_6"):
            self.changeSelectedInventorySlot(5)
        elif key == kb.getKey("hotbar_7"):
            self.changeSelectedInventorySlot(6)
        elif key == kb.getKey("hotbar_8"):
            self.changeSelectedInventorySlot(7)
        elif key == kb.getKey("hotbar_9"):
            self.changeSelectedInventorySlot(8)
        elif key == kb.getKey("hotbar_0"):
            self.changeSelectedInventorySlot(9)
        elif key == kb.getKey("toggle_debug"):
            self.config.debug = not self.config.debug
        elif key == kb.getKey("toggle_minimap"):
            self.config.showMiniMap = not self.config.showMiniMap
        elif key == kb.getKey("minimap_zoom_in"):
            if self.minimapScaleFactor < 1.0:
                self.minimapScaleFactor += 0.1
        elif key == kb.getKey("minimap_zoom_out"):
            if self.minimapScaleFactor > 0:
                self.minimapScaleFactor -= 0.1
        elif key == kb.getKey("toggle_camera_follow"):
            self.config.cameraFollowPlayer = not self.config.cameraFollowPlayer
        elif key == kb.getKey("toggle_help"):
            self.showHelp = not self.showHelp

    def handleKeyUpEvent(self, key):
        kb = self.keyBindings
        if (
            key == kb.getKey("move_up") or key == kb.getKey("alt_move_up")
        ) and self.player.getDirection() == 0:
            self.player.setDirection(-1)
        elif (
            key == kb.getKey("move_left") or key == kb.getKey("alt_move_left")
        ) and self.player.getDirection() == 1:
            self.player.setDirection(-1)
        elif (
            key == kb.getKey("move_down") or key == kb.getKey("alt_move_down")
        ) and self.player.getDirection() == 2:
            self.player.setDirection(-1)
        elif (
            key == kb.getKey("move_right") or key == kb.getKey("alt_move_right")
        ) and self.player.getDirection() == 3:
            self.player.setDirection(-1)
        elif key == kb.getKey("run"):
            self.player.setMovementSpeed(
                self.player.getMovementSpeed() / self.config.runSpeedFactor
            )
        elif key == kb.getKey("crouch"):
            self.player.setCrouching(False)

    def respawnPlayer(self):
        # drop all items and clear inventory
        playerLocationId = self.player.getLocationID()
        playerLocation = self.currentRoom.getGrid().getLocation(playerLocationId)
        for inventorySlot in self.player.getInventory().getInventorySlots():
            if inventorySlot.isEmpty():
                continue
            for item in inventorySlot.getContents():
                self.currentRoom.addEntityToLocation(item, playerLocation)
                if isinstance(item, LivingEntity):
                    self.currentRoom.addLivingEntity(item)
        self.player.getInventory().clear()

        self.currentRoom.removeEntity(self.player)
        self.map.getRoom(0, 0).addEntity(self.player)

        self.save()

        self.currentRoom = self.map.getRoom(0, 0)
        self.player.energy = self.player.targetEnergy
        self.status.set("Respawned")
        self.player.setTickCreated(self.tickCounter.getTick())

    def checkPlayerMovementCooldown(self, tickToCheck):
        ticksPerSecond = self.config.ticksPerSecond
        return (
            tickToCheck + ticksPerSecond / self.player.getMovementSpeed()
            < self.tickCounter.getTick()
        )

    def checkPlayerGatherCooldown(self, tickToCheck):
        ticksPerSecond = self.config.ticksPerSecond
        return (
            tickToCheck + ticksPerSecond / self.player.getGatherSpeed()
            < self.tickCounter.getTick()
        )

    def checkPlayerPlaceCooldown(self, tickToCheck):
        ticksPerSecond = self.config.ticksPerSecond
        return (
            tickToCheck + ticksPerSecond / self.player.getPlaceSpeed()
            < self.tickCounter.getTick()
        )

    def eatFoodInInventory(self):
        for itemSlot in self.player.getInventory().getInventorySlots():
            if itemSlot.isEmpty():
                continue
            item = itemSlot.getContents()[0]
            if self.player.canEat(item) and item.getEnergy() > 0:
                self.player.addEnergy(item.getEnergy())
                self.player.getInventory().removeByItem(item)
                self.stats.incrementFoodEaten()

                self.status.set("Ate " + item.getName() + " from inventory")

                self.stats.incrementScore()
                return

    def handlePlayerActions(self):
        if self.player.isMoving() and self.checkPlayerMovementCooldown(
            self.player.getTickLastMoved()
        ):
            self.movePlayer(self.player.direction)

        if self.player.isGathering() and self.checkPlayerGatherCooldown(
            self.player.getTickLastGathered()
        ):
            self.executeGatherAction()
        elif self.player.isPlacing() and self.checkPlayerPlaceCooldown(
            self.player.getTickLastPlaced()
        ):
            self.executePlaceAction()

        if self.player.needsEnergy() and self.config.autoEatFoodInInventory:
            self.eatFoodInInventory()

    def removeEnergyAndCheckForPlayerDeath(self):
        self.player.removeEnergy(self.config.energyDepletionRate)
        if self.player.getEnergy() < self.player.getTargetEnergy() * 0.10:
            self.status.set("Low on energy!")
        if self.player.isDead():
            self.status.set("You died! Respawning...")
            self.stats.setScore(ceil(self.stats.getScore() * 0.9))
            self.stats.incrementNumberOfDeaths()

    def switchToInventoryScreen(self):
        self.returnCursorSlotToInventory()
        self.nextScreen = ScreenType.INVENTORY_SCREEN
        self.changeScreen = True

    def isCurrentRoomSavedAsPNG(self):
        path = (
            self.config.pathToSaveDirectory
            + "/roompngs/"
            + str(self.currentRoom.getX())
            + "_"
            + str(self.currentRoom.getY())
            + ".png"
        )
        return os.path.isfile(path)

    def saveCurrentRoomAsPNG(self):
        roomKey = (self.currentRoom.getX(), self.currentRoom.getY())
        if roomKey in self._pngSavePending:
            return

        if not os.path.exists(self.config.pathToSaveDirectory + "/roompngs"):
            os.makedirs(self.config.pathToSaveDirectory + "/roompngs")

        # remove player
        locationOfPlayer = self.currentRoom.getGrid().getLocation(
            self.player.getLocationID()
        )
        self.currentRoom.removeEntity(self.player)
        self.currentRoom.draw(self.locationWidth, self.locationHeight)

        path = (
            self.config.pathToSaveDirectory
            + "/roompngs/"
            + str(self.currentRoom.getX())
            + "_"
            + str(self.currentRoom.getY())
            + ".png"
        )
        # capture only the square room area (location sizes are based on game area)
        gameArea = self.graphik.getGameAreaRect()
        size = (int(gameArea.width), int(gameArea.height))
        # capture surface on main thread (pygame requirement), save to disk async
        image = pygame.Surface(size)
        image.blit(
            self.graphik.getGameDisplay(),
            (0, 0),
            ((int(gameArea.x), int(gameArea.y)), size),
        )
        self._pngSavePending.add(roomKey)
        self._saveExecutor.submit(self._saveSurfaceToDisk, image, path, roomKey)

        # add player back
        self.currentRoom.addEntityToLocation(self.player, locationOfPlayer)

    def _saveSurfaceToDisk(self, surface, path, roomKey):
        """Save a pygame surface to disk. Runs on a background thread.
        Acquires roompngsLock to avoid racing with clearRoomImages()."""
        try:
            with self.mapImageUpdater.roompngsLock:
                pygame.image.save(surface, path)
        except Exception as e:
            _logger.error("error saving room PNG", error=str(e), path=path)
        finally:
            self._pngSavePending.discard(roomKey)

    def drawMiniMap(self):
        # if map image doesn't exist, use cache or skip
        mapImagePath = self.config.pathToSaveDirectory + "/mapImage.png"
        if not os.path.isfile(mapImagePath):
            if self._cachedMiniMapImage is not None:
                mapImage = self._cachedMiniMapImage
            else:
                return
        else:
            # only reload from disk every 60 ticks to avoid I/O every frame
            currentTick = self.tickCounter.getTick()
            if (
                self._cachedMiniMapImage is None
                or currentTick - self._miniMapLastLoadTick >= 60
            ):
                try:
                    mapImage = pygame.image.load(mapImagePath)
                    self._cachedMiniMapImage = mapImage
                    self._miniMapLastLoadTick = currentTick
                except (FileNotFoundError, pygame.error):
                    if self._cachedMiniMapImage is not None:
                        mapImage = self._cachedMiniMapImage
                    else:
                        return
            else:
                mapImage = self._cachedMiniMapImage

        # scale as a square using the game area size
        gameArea = self.graphik.getGameAreaRect()
        minimapSize = gameArea.width * self.minimapScaleFactor
        mapImage = pygame.transform.scale(
            mapImage,
            (
                minimapSize,
                minimapSize,
            ),
        )

        minimapOx, minimapOy = self.hudDragManager.getOffset("minimap")
        drawX = self.minimapX + minimapOx
        drawY = self.minimapY + minimapOy

        # draw rectangle
        backgroundColor = (200, 200, 200)
        self.graphik.drawRectangle(
            drawX,
            drawY,
            mapImage.get_width() + 20,
            mapImage.get_height() + 20,
            backgroundColor,
        )

        # blit in top left corner with 10px padding
        self.graphik.getGameDisplay().blit(mapImage, (drawX + 10, drawY + 10))

    def drawFollowMode(self):
        gameArea = self.graphik.getGameAreaRect()

        # get player position in current room grid
        playerLocation = self.getLocationOfPlayer()
        playerGridX = playerLocation.getX()
        playerGridY = playerLocation.getY()
        gridSize = self.config.gridSize

        # calculate the pixel size of a single room
        roomPixelWidth = gridSize * self.locationWidth
        roomPixelHeight = gridSize * self.locationHeight

        # calculate center of the game area on screen
        centerX = gameArea.x + gameArea.width / 2
        centerY = gameArea.y + gameArea.height / 2

        # world-pixel position of the player within the current room
        playerPixelX = playerGridX * self.locationWidth + self.locationWidth / 2
        playerPixelY = playerGridY * self.locationHeight + self.locationHeight / 2

        # offset to center the current room's player on the game area center
        baseOffsetX = centerX - playerPixelX
        baseOffsetY = centerY - playerPixelY

        # determine which neighboring rooms are visible
        currentRoomX = self.currentRoom.getX()
        currentRoomY = self.currentRoom.getY()

        # calculate how many rooms could be visible in each direction
        halfWidth = gameArea.width / 2
        halfHeight = gameArea.height / 2
        roomsLeft = int(halfWidth / roomPixelWidth) + 1
        roomsRight = int(halfWidth / roomPixelWidth) + 1
        roomsUp = int(halfHeight / roomPixelHeight) + 1
        roomsDown = int(halfHeight / roomPixelHeight) + 1

        for dx in range(-roomsLeft, roomsRight + 1):
            for dy in range(-roomsUp, roomsDown + 1):
                roomX = currentRoomX + dx
                roomY = currentRoomY + dy

                # check world border
                if self.config.worldBorder != 0 and (
                    abs(roomX) > self.config.worldBorder
                    or abs(roomY) > self.config.worldBorder
                ):
                    continue

                # calculate screen offset for this room
                roomOffsetX = baseOffsetX + dx * roomPixelWidth
                roomOffsetY = baseOffsetY + dy * roomPixelHeight

                # skip if the room is entirely outside the game area
                if (
                    roomOffsetX + roomPixelWidth < gameArea.x
                    or roomOffsetX > gameArea.right
                    or roomOffsetY + roomPixelHeight < gameArea.y
                    or roomOffsetY > gameArea.bottom
                ):
                    continue

                room = self.getOrLoadRoom(roomX, roomY)
                room.drawWithOffset(
                    self.locationWidth,
                    self.locationHeight,
                    roomOffsetX,
                    roomOffsetY,
                    gameArea.right,
                    gameArea.bottom,
                )

    def drawHelpOverlay(self):
        x, y = self.graphik.getGameDisplay().get_size()
        overlayWidth = x * 0.6
        overlayHeight = y * 0.75
        overlayX = x / 2 - overlayWidth / 2
        overlayY = y / 2 - overlayHeight / 2

        # dark background
        self.graphik.drawRectangle(
            overlayX, overlayY, overlayWidth, overlayHeight, (30, 30, 30)
        )

        titleY = overlayY + 25
        self.graphik.drawText(
            "Controls  (F1 to close)", x / 2, titleY, 28, (255, 255, 255)
        )

        helpLines = [
            "W/A/S/D or Arrows  -  Move",
            "Left Click  -  Gather / Pick up",
            "Right Click  -  Place item",
            "1-0  -  Select hotbar slot",
            "Scroll Wheel  -  Cycle hotbar",
            "I  -  Open / Close inventory",
            "Shift  -  Run",
            "Ctrl  -  Crouch",
            "M  -  Toggle minimap",
            "+/-  -  Resize minimap",
            "C  -  Toggle camera follow",
            "F3  -  Toggle debug info",
            "Print Screen  -  Take screenshot",
            "Esc  -  Open menu",
            "F1  -  Toggle this help",
        ]

        lineY = titleY + 40
        lineSpacing = 24
        for line in helpLines:
            self.graphik.drawText(line, x / 2, lineY, 20, (220, 220, 220))
            lineY += lineSpacing

    def _getHotbarDefaultRect(self):
        """Return the default bounding rect for the hotbar (no drag offset)."""
        displayWidth = self.graphik.getGameDisplay().get_width()
        displayHeight = self.graphik.getGameDisplay().get_height()
        itemPreviewXPos = displayWidth / 2 - HOTBAR_SLOT_SIZE * 5 - HOTBAR_SLOT_SIZE / 2
        itemPreviewYPos = displayHeight - HOTBAR_BOTTOM_OFFSET
        barXPos = itemPreviewXPos - HOTBAR_PADDING
        barYPos = itemPreviewYPos - HOTBAR_PADDING
        barWidth = HOTBAR_SLOT_SIZE * 11 + HOTBAR_PADDING
        barHeight = HOTBAR_SLOT_SIZE + HOTBAR_PADDING * 2
        return pygame.Rect(barXPos, barYPos, barWidth, barHeight)

    def _getMinimapDefaultRect(self):
        """Return the default bounding rect for the minimap (no drag offset)."""
        gameArea = self.graphik.getGameAreaRect()
        minimapSize = gameArea.width * self.minimapScaleFactor
        return pygame.Rect(
            self.minimapX,
            self.minimapY,
            minimapSize + 20,
            minimapSize + 20,
        )

    def draw(self):
        gameArea = self.graphik.getGameAreaRect()

        # save room PNG if needed (before clipping, so it draws unclipped)
        if self.config.showMiniMap and not self.isCurrentRoomSavedAsPNG():
            self.saveCurrentRoomAsPNG()

        # fill entire display with black (letterbox bars)
        self.graphik.getGameDisplay().fill((0, 0, 0))

        # clip drawing to the game area and fill with room background
        self.graphik.getGameDisplay().set_clip(gameArea)
        self.graphik.getGameDisplay().fill(self.currentRoom.getBackgroundColor())

        if self.config.cameraFollowPlayer:
            self.drawFollowMode()
        else:
            self.currentRoom.drawWithOffset(
                self.locationWidth, self.locationHeight, gameArea.x, gameArea.y
            )

        # remove clip so UI draws over the full display
        self.graphik.getGameDisplay().set_clip(None)

        statusOx, statusOy = self.hudDragManager.getOffset("status")
        self.status.draw(statusOx, statusOy)
        energyOx, energyOy = self.hudDragManager.getOffset("energyBar")
        self.energyBar.draw(energyOx, energyOy)

        hotbarOx, hotbarOy = self.hudDragManager.getOffset("hotbar")
        itemPreviewXPos = (
            self.graphik.getGameDisplay().get_width() / 2
            - HOTBAR_SLOT_SIZE * 5
            - HOTBAR_SLOT_SIZE / 2
        ) + hotbarOx
        itemPreviewYPos = (
            self.graphik.getGameDisplay().get_height() - HOTBAR_BOTTOM_OFFSET + hotbarOy
        )
        itemPreviewWidth = HOTBAR_SLOT_SIZE
        itemPreviewHeight = HOTBAR_SLOT_SIZE

        barXPos = itemPreviewXPos - HOTBAR_PADDING
        barYPos = itemPreviewYPos - HOTBAR_PADDING
        barWidth = itemPreviewWidth * 11 + HOTBAR_PADDING
        barHeight = itemPreviewHeight + HOTBAR_PADDING * 2

        # draw rectangle slightly bigger than item images
        self.graphik.drawRectangle(barXPos, barYPos, barWidth, barHeight, (0, 0, 0))

        # draw first 10 items in player inventory in bottom center
        firstTenInventorySlots = self.player.getInventory().getFirstTenInventorySlots()
        for i in range(len(firstTenInventorySlots)):
            inventorySlot = firstTenInventorySlots[i]
            if inventorySlot.isEmpty():
                # draw white square if item slot is empty
                self.graphik.drawRectangle(
                    itemPreviewXPos,
                    itemPreviewYPos,
                    itemPreviewWidth,
                    itemPreviewHeight,
                    (255, 255, 255),
                )
                if i == self.player.getInventory().getSelectedInventorySlotIndex():
                    # draw yellow square in the middle of the selected inventory slot
                    self.graphik.drawRectangle(
                        itemPreviewXPos + itemPreviewWidth / 2 - 5,
                        itemPreviewYPos + itemPreviewHeight / 2 - 5,
                        10,
                        10,
                        (255, 255, 0),
                    )
                itemPreviewXPos += HOTBAR_SLOT_SIZE + HOTBAR_SLOT_GAP
                continue
            item = inventorySlot.getContents()[0]
            image = item.getImage()
            scaledImage = pygame.transform.scale(
                image, (HOTBAR_SLOT_SIZE, HOTBAR_SLOT_SIZE)
            )
            self.graphik.gameDisplay.blit(
                scaledImage, (itemPreviewXPos, itemPreviewYPos)
            )

            if i == self.player.getInventory().getSelectedInventorySlotIndex():
                # draw yellow square in the middle of the selected inventory slot
                self.graphik.drawRectangle(
                    itemPreviewXPos + itemPreviewWidth / 2 - 5,
                    itemPreviewYPos + itemPreviewHeight / 2 - 5,
                    10,
                    10,
                    (255, 255, 0),
                )

            # draw item amount in bottom right corner of inventory slot
            self.graphik.drawText(
                str(inventorySlot.getNumItems()),
                itemPreviewXPos + itemPreviewWidth - 20,
                itemPreviewYPos + itemPreviewHeight - 20,
                20,
                (255, 255, 255),
            )

            itemPreviewXPos += HOTBAR_SLOT_SIZE + HOTBAR_SLOT_GAP

        if self.config.debug:
            # display tick count in top right corner
            tickValue = self.tickCounter.getTick()
            measuredTicksPerSecond = self.tickCounter.getMeasuredTicksPerSecond()
            xpos = self.graphik.getGameDisplay().get_width() - 100
            ypos = 20
            self.graphik.drawText(
                "Tick: "
                + str(tickValue)
                + " ("
                + str(int(measuredTicksPerSecond))
                + " TPS)",
                xpos,
                ypos,
                20,
                (255, 255, 255),
            )

            # display max measured ticks per second in top right corner
            highestmtps = self.tickCounter.getHighestMeasuredTicksPerSecond()
            xpos = self.graphik.getGameDisplay().get_width() - 100
            ypos = 40
            self.graphik.drawText(
                "Peak TPS: " + str(int(highestmtps)), xpos, ypos, 20, (255, 255, 255)
            )

            # draw room coordinates in top left corner
            coordinatesText = (
                "("
                + str(self.currentRoom.getX())
                + ", "
                + str(self.currentRoom.getY() * -1)
                + ")"
            )
            ypos = 20
            if self.config.showMiniMap:
                # move to bottom left
                ypos = self.graphik.getGameDisplay().get_height() - 40
            self.graphik.drawText(coordinatesText, 30, ypos, 20, (255, 255, 255))

        if self.config.showMiniMap and self.minimapScaleFactor > 0:
            self.drawMiniMap()

        # show help hint in bottom-right corner
        if not self.showHelp:
            hintX = self.graphik.getGameDisplay().get_width() - 50
            hintY = self.graphik.getGameDisplay().get_height() - 20
            self.graphik.drawText("F1: Help", hintX, hintY, 16, (180, 180, 180))

        self.drawCursorSlot()

        if self.showHelp:
            self.drawHelpOverlay()

        pygame.display.update()

    def getHotbarSlotAtMousePosition(self):
        x, y = pygame.mouse.get_pos()
        displayWidth = self.graphik.getGameDisplay().get_width()
        displayHeight = self.graphik.getGameDisplay().get_height()
        hotbarOx, hotbarOy = self.hudDragManager.getOffset("hotbar")
        itemPreviewXPos = (
            displayWidth / 2 - HOTBAR_SLOT_SIZE * 5 - HOTBAR_SLOT_SIZE / 2 + hotbarOx
        )
        itemPreviewYPos = displayHeight - HOTBAR_BOTTOM_OFFSET + hotbarOy
        itemPreviewWidth = HOTBAR_SLOT_SIZE
        itemPreviewHeight = HOTBAR_SLOT_SIZE
        for i in range(10):
            slotX = itemPreviewXPos + i * (itemPreviewWidth + HOTBAR_SLOT_GAP)
            if (
                x >= slotX
                and x < slotX + itemPreviewWidth
                and y >= itemPreviewYPos
                and y < itemPreviewYPos + itemPreviewHeight
            ):
                return i
        return -1

    def returnCursorSlotToInventory(self):
        if self.cursorSlot.isEmpty():
            return

        remainingItems = []
        for item in self.cursorSlot.getContents():
            if not self.player.getInventory().placeIntoFirstAvailableInventorySlot(
                item
            ):
                remainingItems.append(item)

        self.cursorSlot.setContents(remainingItems)
        if len(remainingItems) > 0:
            self.status.set("Inventory full")

    def drawCursorSlot(self):
        if self.cursorSlot.isEmpty():
            return
        item = self.cursorSlot.getContents()[0]
        image = item.getImage()
        scaledImage = pygame.transform.scale(image, (50, 50))
        self.graphik.gameDisplay.blit(scaledImage, pygame.mouse.get_pos())
        numItems = self.cursorSlot.getNumItems()
        if numItems > 1:
            mouseX, mouseY = pygame.mouse.get_pos()
            self.graphik.drawText(
                str(numItems),
                mouseX + 30,
                mouseY + 30,
                20,
                (255, 255, 255),
            )

    def handleMouseDownEvent(self, event):
        # Middle-click initiates HUD drag
        if event.button == MIDDLE_MOUSE_BUTTON:
            mx, my = pygame.mouse.get_pos()
            self.hudDragManager.handleMouseDown(mx, my)
            return

        if self.showInventory:
            # disallow player to interact with the world while inventory is open
            self.status.set("Close inventory first (I)")
            return

        hotbarIndex = self.getHotbarSlotAtMousePosition()
        if hotbarIndex != -1:
            inventory = self.player.getInventory()
            hotbarSlot = inventory.getInventorySlots()[hotbarIndex]
            if pygame.mouse.get_pressed()[2]:  # right click
                if not self.cursorSlot.isEmpty():
                    # place cursor item into clicked hotbar slot
                    if hotbarSlot.isEmpty():
                        hotbarSlot.setContents(self.cursorSlot.getContents())
                        self.cursorSlot.setContents([])
                    elif (
                        self.cursorSlot.getContents()[0].getName()
                        == hotbarSlot.getContents()[0].getName()
                    ):
                        inventory.mergeIntoSlot(self.cursorSlot, hotbarSlot)
                    else:
                        temp = hotbarSlot.getContents()
                        hotbarSlot.setContents(self.cursorSlot.getContents())
                        self.cursorSlot.setContents(temp)
                elif not hotbarSlot.isEmpty():
                    # move hotbar item to first available non-hotbar inventory slot
                    items = list(hotbarSlot.getContents())
                    hotbarSlot.setContents([])
                    remaining = []
                    for item in items:
                        if not inventory.placeIntoFirstAvailableNonHotbarSlot(item):
                            remaining.append(item)
                    if len(remaining) > 0:
                        hotbarSlot.setContents(remaining)
                        self.status.set("Inventory full")
                    else:
                        self.status.set("Moved to inventory")
            elif pygame.mouse.get_pressed()[0]:  # left click
                if self.cursorSlot.isEmpty():
                    if not hotbarSlot.isEmpty():
                        self.cursorSlot.setContents(hotbarSlot.getContents())
                        hotbarSlot.setContents([])
                elif (
                    not hotbarSlot.isEmpty()
                    and self.cursorSlot.getContents()[0].getName()
                    == hotbarSlot.getContents()[0].getName()
                ):
                    inventory.mergeIntoSlot(self.cursorSlot, hotbarSlot)
                else:
                    temp = hotbarSlot.getContents()
                    hotbarSlot.setContents(self.cursorSlot.getContents())
                    self.cursorSlot.setContents(temp)
            return

        if not self.cursorSlot.isEmpty():
            # clicking outside hotbar with cursor item returns it to inventory
            self.returnCursorSlotToInventory()
            return

        if pygame.mouse.get_pressed()[0]:  # left click
            self.player.setGathering(True)
        elif pygame.mouse.get_pressed()[2]:  # right click
            self.player.setPlacing(True)

    def handleMouseUpEvent(self, event):
        # Finish HUD drag on middle-button release
        if event.button == MIDDLE_MOUSE_BUTTON and self.hudDragManager.isDragging():
            mx, my = pygame.mouse.get_pos()
            sw = self.graphik.getGameDisplay().get_width()
            sh = self.graphik.getGameDisplay().get_height()
            self.hudDragManager.handleMouseUp(mx, my, sw, sh)
            return
        if not pygame.mouse.get_pressed()[0]:
            self.player.setGathering(False)
        if not pygame.mouse.get_pressed()[2]:
            self.player.setPlacing(False)

    def handleMouseMotionEvent(self):
        if self.hudDragManager.isDragging():
            mx, my = pygame.mouse.get_pos()
            sw = self.graphik.getGameDisplay().get_width()
            sh = self.graphik.getGameDisplay().get_height()
            self.hudDragManager.handleMouseMotion(mx, my, sw, sh)

    def handleMouseWheelEvent(self, event):
        if event.y > 0:
            currentSelectedInventorySlotIndex = (
                self.player.getInventory().getSelectedInventorySlotIndex()
            )
            newSelectedInventorySlotIndex = currentSelectedInventorySlotIndex - 1
            if newSelectedInventorySlotIndex < 0:
                newSelectedInventorySlotIndex = 9
            self.player.getInventory().setSelectedInventorySlotIndex(
                newSelectedInventorySlotIndex
            )
        elif event.y < 0:
            currentSelectedInventorySlotIndex = (
                self.player.getInventory().getSelectedInventorySlotIndex()
            )
            newSelectedInventorySlotIndex = currentSelectedInventorySlotIndex + 1
            if newSelectedInventorySlotIndex > 9:
                newSelectedInventorySlotIndex = 0
            self.player.getInventory().setSelectedInventorySlotIndex(
                newSelectedInventorySlotIndex
            )

    def handleMouseOver(self):
        location = self.getLocationAtMousePosition()
        if location == -1:
            # mouse is not over a location
            return
        for entityId in location.getEntities():
            entity = location.getEntity(entityId)
            if isinstance(entity, LivingEntity):
                statusString = entity.getName()
                if self.config.debug:
                    # include energy and age
                    statusString += (
                        " (energy="
                        + str(entity.getEnergy())
                        + "/"
                        + str(entity.getTargetEnergy())
                        + ", age="
                        + str(entity.getAge(self.tickCounter.getTick()))
                        + ")"
                    )
                self.status.set(statusString)

    def savePlayerLocationToFile(self):
        jsonPlayerLocation = {}

        jsonPlayerLocation["roomX"] = self.currentRoom.getX()
        jsonPlayerLocation["roomY"] = self.currentRoom.getY()

        playerLocationId = self.player.getLocationID()
        jsonPlayerLocation["locationId"] = str(playerLocationId)

        with open("schemas/playerLocation.json") as f:
            playerLocationSchema = json.load(f)
        jsonschema.validate(jsonPlayerLocation, playerLocationSchema)

        path = self.config.pathToSaveDirectory + "/playerLocation.json"
        _logger.info("saving player location", path=path)
        with open(path, "w") as f:
            json.dump(jsonPlayerLocation, f, indent=4)

    def loadPlayerLocationFromFile(self):
        path = self.config.pathToSaveDirectory + "/playerLocation.json"
        if not os.path.exists(path):
            return

        _logger.info("loading player location", path=path)
        with open(path) as f:
            jsonPlayerLocation = json.load(f)

        with open("schemas/playerLocation.json") as f:
            playerLocationSchema = json.load(f)
        jsonschema.validate(jsonPlayerLocation, playerLocationSchema)

        roomX = jsonPlayerLocation["roomX"]
        roomY = jsonPlayerLocation["roomY"]
        self.currentRoom = self.map.getRoom(roomX, roomY)

        locationId = jsonPlayerLocation["locationId"]
        location = self.currentRoom.getGrid().getLocation(locationId)
        self.currentRoom.addEntityToLocation(self.player, location)

    def savePlayerAttributesToFile(self):
        jsonPlayerAttributes = {}
        jsonPlayerAttributes["energy"] = ceil(self.player.getEnergy())

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

    def savePlayerInventoryToFile(self):
        inventoryJsonReaderWriter = InventoryJsonReaderWriter(self.config)
        inventoryJsonReaderWriter.saveInventory(
            self.player.getInventory(),
            self.config.pathToSaveDirectory + "/playerInventory.json",
        )

    def loadPlayerInventoryFromFile(self):
        inventoryJsonReaderWriter = InventoryJsonReaderWriter(self.config)
        inventory = inventoryJsonReaderWriter.loadInventory(
            self.config.pathToSaveDirectory + "/playerInventory.json"
        )
        if inventory is not None:
            self.player.setInventory(inventory)

    def getNewLocationCoordinatesForLivingEntityBasedOnLocation(self, currentLocation):
        newLocationX = None
        newLocationY = None

        # get current location coordinates
        currentLocationX = currentLocation.getX()
        currentLocationY = currentLocation.getY()

        # if corner
        if self.ifCorner(currentLocation):
            raise Exception("corner movement not supported yet")
        else:
            # if left
            if currentLocationX == 0:
                newLocationX = self.currentRoom.getGrid().getRows() - 1
                newLocationY = currentLocationY
            # if right
            elif currentLocationX == self.currentRoom.getGrid().getRows() - 1:
                newLocationX = 0
                newLocationY = currentLocationY
            # if top
            elif currentLocationY == 0:
                newLocationX = currentLocationX
                newLocationY = self.currentRoom.getGrid().getRows() - 1
            # if bottom
            elif currentLocationY == self.currentRoom.getGrid().getRows() - 1:
                newLocationX = currentLocationX
                newLocationY = 0
            # if middle
            else:
                # throw error
                raise Exception("Living entity is not on the edge of the room")
        return newLocationX, newLocationY

    def checkForLivingEntityDeaths(self):
        toRemove = []
        for livingEntityId in self.currentRoom.getLivingEntities():
            livingEntity = self.currentRoom.getEntity(livingEntityId)
            if livingEntity is None:
                _logger.debug(
                    "living entity not found in room",
                    entityId=str(livingEntityId),
                    roomName=self.currentRoom.getName(),
                )
                toRemove.append(livingEntityId)
                continue
            if livingEntity.getEnergy() == 0:
                toRemove.append(livingEntityId)

        for livingEntityId in toRemove:
            livingEntity = self.currentRoom.getEntity(livingEntityId)
            if livingEntity is None:
                self.currentRoom.removeLivingEntityById(livingEntityId)
                continue

            # spawn meat at the living entity's location before removing it
            locationId = livingEntity.getLocationID()
            if str(locationId) != "-1":
                try:
                    location = self.currentRoom.getGrid().getLocation(locationId)
                    if isinstance(livingEntity, Chicken):
                        meat = ChickenMeat()
                        self.currentRoom.addEntityToLocation(meat, location)
                    elif isinstance(livingEntity, Bear):
                        meat = BearMeat()
                        self.currentRoom.addEntityToLocation(meat, location)
                except KeyError as ex:
                    _logger.debug(
                        "could not spawn meat for entity",
                        entityName=livingEntity.getName(),
                        locationId=str(locationId),
                        error=str(ex),
                    )

            self.currentRoom.removeEntity(livingEntity)
            self.currentRoom.removeLivingEntity(livingEntity)
            _logger.debug(
                "living entity died",
                entityName=livingEntity.getName(),
                roomName=self.currentRoom.getName(),
            )

    def save(self):
        """Submit save operations to the background thread.
        Prepares room JSON snapshot on the main thread to avoid dict-iteration
        races, then writes files in the background.
        Skips if a save is already in progress to avoid stacking."""
        with self._saveLock:
            if self._saveInProgress:
                return
            self._saveInProgress = True
        # snapshot room JSON on the main thread (safe dict iteration)
        try:
            roomJson = self.roomJsonReaderWriter.generateJsonForRoom(self.currentRoom)
        except Exception as e:
            _logger.error("error preparing room snapshot for save", error=str(e))
            roomJson = None
        roomPath = (
            self.config.pathToSaveDirectory
            + "/rooms/room_"
            + str(self.currentRoom.getX())
            + "_"
            + str(self.currentRoom.getY())
            + ".json"
        )
        self._saveExecutor.submit(self._doSave, roomJson, roomPath)

    def saveSynchronous(self):
        """Run save operations synchronously (used on exit to ensure data is persisted)."""
        self.saveCurrentRoomToFile()
        self.savePlayerLocationToFile()
        self.savePlayerAttributesToFile()
        self.savePlayerInventoryToFile()
        self.stats.save()
        self.tickCounter.save()

        if self.config.showMiniMap:
            if not self.isCurrentRoomSavedAsPNG():
                self.saveCurrentRoomAsPNG()
            # flush pending PNG writes so the map image update reads complete files
            future = self._saveExecutor.submit(lambda: None)
            future.result()  # block until all prior tasks are done
            self.mapImageUpdater.updateMapImage()

    def _doSave(self, roomJson, roomPath):
        """Perform save operations. Runs on a background thread.
        roomJson is a pre-built dict snapshot prepared on the main thread."""
        try:
            if roomJson is not None:
                dirPath = os.path.dirname(roomPath)
                if not os.path.exists(dirPath):
                    os.makedirs(dirPath, exist_ok=True)
                with open(roomPath, "w") as outfile:
                    json.dump(roomJson, outfile, indent=4)
            self.savePlayerLocationToFile()
            self.savePlayerAttributesToFile()
            self.savePlayerInventoryToFile()
            self.stats.save()
            self.tickCounter.save()
        except Exception as e:
            _logger.error("error during save", error=str(e))
        finally:
            with self._saveLock:
                self._saveInProgress = False

        if self.config.showMiniMap:
            self.mapImageUpdater.updateMapImage()

    def shutdown(self):
        """Cleanly shut down background thread pools and recreate them so the
        same WorldScreen instance can be reused when the player returns."""
        self._saveExecutor.shutdown(wait=True)
        self._saveExecutor = ThreadPoolExecutor(max_workers=1)
        self.roomPreloader.shutdown(wait=True)
        self.mapImageUpdater.shutdown(wait=True)

    def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.printStatsToConsole()
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)
                elif event.type == pygame.KEYUP:
                    self.handleKeyUpEvent(event.key)
                elif event.type == pygame.WINDOWRESIZED:
                    self.initializeLocationWidthAndHeight()
                    self.updateConfigWindowSize()
                elif event.type == pygame.VIDEORESIZE:
                    self.initializeLocationWidthAndHeight()
                    self.updateConfigWindowSize()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseDownEvent(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handleMouseUpEvent(event)
                elif event.type == pygame.MOUSEMOTION:
                    self.handleMouseMotionEvent()
                elif event.type == pygame.MOUSEWHEEL:
                    self.handleMouseWheelEvent(event)

            # move living entities
            entitiesToMoveToNewRooms = self.currentRoom.moveLivingEntities(
                self.tickCounter.getTick()
            )
            if len(entitiesToMoveToNewRooms) > 0:
                for entityToMove in entitiesToMoveToNewRooms:
                    # get new room
                    try:
                        (
                            newRoomX,
                            newRoomY,
                        ) = self.getCoordinatesForNewRoomBasedOnLivingEntityLocation(
                            entityToMove
                        )
                    except Exception as e:
                        if self.config.debug:
                            _logger.debug("error moving entity to new room", error=str(e))
                        continue
                    newRoom = self.map.getRoom(newRoomX, newRoomY)
                    if newRoom == -1:
                        # attempt to load room if file exists, otherwise generate new room
                        nextRoomPath = (
                            self.config.pathToSaveDirectory
                            + "/rooms/room_"
                            + str(newRoomX)
                            + "_"
                            + str(newRoomY)
                            + ".json"
                        )
                        if os.path.exists(nextRoomPath):
                            roomJsonReaderWriter = RoomJsonReaderWriter(
                                self.config.gridSize,
                                self.graphik,
                                self.tickCounter,
                                self.config,
                            )
                            newRoom = roomJsonReaderWriter.loadRoom(nextRoomPath)
                            self.map.addRoom(newRoom)
                            self.status.set("Area loaded")
                        else:
                            (
                                x,
                                y,
                            ) = (
                                self.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection()
                            )
                            newRoom = self.map.generateNewRoom(x, y)
                            self.status.set("New area discovered")
                            self.stats.incrementScore()
                            self.stats.incrementRoomsExplored()

                    # get new location
                    currentLocationId = entityToMove.getLocationID()
                    currentLocation = self.currentRoom.getGrid().getLocation(
                        currentLocationId
                    )
                    try:
                        (
                            newLocationX,
                            newLocationY,
                        ) = self.getNewLocationCoordinatesForLivingEntityBasedOnLocation(
                            currentLocation
                        )
                    except Exception as e:
                        if self.config.debug:
                            _logger.debug("error getting new location for entity", error=str(e))
                        continue
                    newLocation = newRoom.getGrid().getLocationByCoordinates(
                        newLocationX, newLocationY
                    )

                    if newLocation == -1:
                        _logger.debug(
                            "could not find new location for entity",
                            entityName=entityToMove.getName(),
                        )
                        continue

                    # remove entity from current room
                    self.currentRoom.removeEntity(entityToMove)
                    self.currentRoom.removeLivingEntity(entityToMove)

                    # add entity to new room
                    newRoom.addEntityToLocation(entityToMove, newLocation)
                    newRoom.addLivingEntity(entityToMove)

                    # save new room
                    self.saveRoomToFileAsync(newRoom)

            self.currentRoom.reproduceLivingEntities(self.tickCounter.getTick())

            self.currentRoom.tickExcrement(self.tickCounter.getTick(), self.config)
            self.currentRoom.tickCrops(self.tickCounter.getTick(), self.config)

            self.handleMouseOver()

            self.handlePlayerActions()
            self.removeEnergyAndCheckForPlayerDeath()
            if self.config.removeDeadEntities:
                self.checkForLivingEntityDeaths()
            self.status.checkForExpiration(self.tickCounter.getTick())
            self.draw()

            pygame.display.update()
            self.tickCounter.incrementTick()

            if self.config.limitTps:
                self.clock.tick(self.config.ticksPerSecond)

            if self.player.isDead():
                time.sleep(3)
                self.respawnPlayer()

            if self.config.showMiniMap:
                self.mapImageUpdater.updateIfCooldownOver()

        # create save directory if it doesn't exist
        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)

        self.returnCursorSlotToInventory()
        self.saveSynchronous()
        self.shutdown()

        self.changeScreen = False
        return self.nextScreen
