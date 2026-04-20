import json
import math
from math import ceil
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import pygame
from appContainer import component
from di import Container
from config.config import Config
from config.keyBindings import KeyBindings
from entity.bearMeat import BearMeat
from entity.chickenMeat import ChickenMeat
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from codex.codex import Codex
from codex.codexJsonReaderWriter import CodexJsonReaderWriter
from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
from inventory.inventorySlot import InventorySlot
from mapimage.mapImageUpdater import MapImageUpdater
from screen.pickupableEntities import canBePickedUp as _canBePickedUp
from screen.screenType import ScreenType
from screen.screenshotHelper import takeScreenshot
from screen.worldScreenPersistence import WorldScreenPersistence
from stats.stats import Stats
from ui.energyBar import EnergyBar
from lib.graphik.src.graphik import Graphik
from entity.grass import Grass
from lib.pyenvlib.grid import Grid
from entity.stone import Stone
from lib.pyenvlib.location import Location
from world.room import Room
from world.roomJsonReaderWriter import RoomJsonReaderWriter
from world.roomPreloader import RoomPreloader
from world.tickCounter import TickCounter
from world.dayNightCycle import DayNightCycle
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
from entity.wheat import Wheat
from entity.wheatSeed import WheatSeed
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
        self.persistence = WorldScreenPersistence(
            config, player, stats, tickCounter, self.roomJsonReaderWriter
        )
        self.roomPreloader = self.container.resolve(RoomPreloader)
        self.mapImageUpdater = self.container.resolve(MapImageUpdater)
        self.hudDragManager = self.container.resolve(HudDragManager)
        self.codex = self.container.resolve(Codex)
        self.dayNightCycle = self.container.resolve(DayNightCycle)
        self._dayNightOverlay = None
        self._dayNightOverlaySize = (0, 0)
        self._scaledMaskCache = {}
        self._lastScaledOpacity = -1
        self._frameLightSources = []
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

        # load codex if possible
        if os.path.exists(self.config.pathToSaveDirectory + "/codex.json"):
            self.loadCodexFromFile()

        self.initializeLocationWidthAndHeight()

        # pre-load nearby rooms in the background
        self.roomPreloader.preloadNearbyRooms(
            self.currentRoom.getX(), self.currentRoom.getY(), self.map
        )

        self.status.set("Entered the world")
        self.energyBar = self.container.resolve(EnergyBar)

        self.discoverLivingEntitiesInRoom()

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
        self.persistence.saveRoomToFile(room)

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

    def _loadOrGenerateRoom(self, x, y):
        room = self.map.getRoom(x, y)
        if room != -1:
            return room
        nextRoomPath = self.persistence.buildRoomPath(x, y)
        if os.path.exists(nextRoomPath):
            roomJsonReaderWriter = RoomJsonReaderWriter(
                self.config.gridSize, self.graphik, self.tickCounter, self.config
            )
            room = roomJsonReaderWriter.loadRoom(nextRoomPath)
            self.map.addRoom(room)
            self.status.set("Area loaded")
            return room
        x, y = self.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection()
        room = self.map.generateNewRoom(x, y)
        self.status.set("New area discovered")
        self.stats.incrementScore()
        self.stats.incrementRoomsExplored()
        return room

    def _calculateTargetLocationForRoomTransition(self, playerLocation):
        targetX = playerLocation.getX()
        targetY = playerLocation.getY()
        minCoord = 0
        maxCoord = self.config.gridSize - 1

        if self.ifCorner(playerLocation):
            playerDirection = self.player.getDirection()
            if playerLocation.getX() == 0 and playerLocation.getY() == 0:
                if playerDirection == 0:
                    targetY = maxCoord
                elif playerDirection == 1:
                    targetX = maxCoord
            elif playerLocation.getX() == maxCoord and playerLocation.getY() == 0:
                if playerDirection == 0:
                    targetY = maxCoord
                elif playerDirection == 3:
                    targetX = minCoord
            elif playerLocation.getX() == 0 and playerLocation.getY() == maxCoord:
                if playerDirection == 2:
                    targetY = minCoord
                elif playerDirection == 1:
                    targetX = maxCoord
            elif (
                playerLocation.getX() == maxCoord
                and playerLocation.getY() == maxCoord
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

        return self.currentRoom.getGrid().getLocationByCoordinates(targetX, targetY)

    def changeRooms(self):
        x, y = self.getCoordinatesForNewRoomBasedOnPlayerLocationAndDirection()

        if self.config.worldBorder != 0 and (
            abs(x) > self.config.worldBorder or abs(y) > self.config.worldBorder
        ):
            self.status.set("Reached world border")
            return

        playerLocation = self.getLocationOfPlayer()
        self.currentRoom.removeEntity(self.player)

        self.currentRoom = self._loadOrGenerateRoom(x, y)

        targetLocation = self._calculateTargetLocationForRoomTransition(playerLocation)
        self.currentRoom.addEntityToLocation(self.player, targetLocation)
        self.initializeLocationWidthAndHeight()

        _logger.info(
            "room transition",
            roomX=self.currentRoom.getX(),
            roomY=self.currentRoom.getY(),
        )

        self.roomPreloader.preloadNearbyRooms(
            self.currentRoom.getX(), self.currentRoom.getY(), self.map
        )

        self.discoverLivingEntitiesInRoom()

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
        return _canBePickedUp(entity)

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
                result = (
                    self.player.getInventory().placeIntoFirstAvailableInventorySlot(
                        wheat
                    )
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

        inventorySlot = self.player.getInventory().getSelectedInventorySlot()
        if inventorySlot.isEmpty():
            self.status.set("Select an item first (1-0)")
            return

        selectedItem = inventorySlot.getContents()[0]
        if isinstance(selectedItem, WheatSeed):
            self._plantWheatSeed(targetLocation, targetRoom)
            return

        self.player.removeEnergy(self.config.playerInteractionEnergyCost)
        toPlace = self.player.getInventory().removeSelectedItem()

        if toPlace == -1:
            return

        targetRoom.addEntityToLocation(toPlace, targetLocation)
        if isinstance(toPlace, LivingEntity):
            targetRoom.addLivingEntity(toPlace)
        self.status.set("Placed " + toPlace.getName())
        self.player.setTickLastPlaced(self.tickCounter.getTick())

    def _plantWheatSeed(self, targetLocation, targetRoom):
        for entityId in list(targetLocation.getEntities().keys()):
            entity = targetLocation.getEntity(entityId)
            if isinstance(entity, (YoungCrop, MatureCrop)):
                self.status.set("A crop is already growing here")
                return
        hasGrass = False
        for entityId in list(targetLocation.getEntities().keys()):
            entity = targetLocation.getEntity(entityId)
            if isinstance(entity, Grass):
                hasGrass = True
                break
        if not hasGrass:
            self.status.set("Must plant on grass")
            return
        self.player.removeEnergy(self.config.playerInteractionEnergyCost)
        for entityId in list(targetLocation.getEntities().keys()):
            entity = targetLocation.getEntity(entityId)
            if isinstance(entity, Grass):
                targetLocation.removeEntity(entity)
                break
        self.player.getInventory().removeSelectedItem()
        youngCrop = YoungCrop(self.tickCounter.getTick())
        targetRoom.addEntityToLocation(youngCrop, targetLocation)
        self.status.set("Planted Wheat Seed")
        self.player.setTickLastPlaced(self.tickCounter.getTick())

    def changeSelectedInventorySlot(self, index):
        self.player.getInventory().setSelectedInventorySlotIndex(index)
        inventorySlot = self.player.getInventory().getSelectedInventorySlot()
        if inventorySlot.isEmpty():
            self.status.set("Empty slot")
            return
        item = inventorySlot.getContents()[0]
        self.status.set("Selected " + item.getName())

    def _handleMovementKey(self, direction):
        self.player.setDirection(direction)
        if self.checkPlayerMovementCooldown(self.player.getTickLastMoved()):
            self.movePlayer(self.player.direction)

    def _handleHotbarKey(self, key):
        kb = self.keyBindings
        hotbarKeys = [
            (kb.getKey("hotbar_1"), 0),
            (kb.getKey("hotbar_2"), 1),
            (kb.getKey("hotbar_3"), 2),
            (kb.getKey("hotbar_4"), 3),
            (kb.getKey("hotbar_5"), 4),
            (kb.getKey("hotbar_6"), 5),
            (kb.getKey("hotbar_7"), 6),
            (kb.getKey("hotbar_8"), 7),
            (kb.getKey("hotbar_9"), 8),
            (kb.getKey("hotbar_0"), 9),
        ]
        for hotbarKey, index in hotbarKeys:
            if key == hotbarKey:
                self.changeSelectedInventorySlot(index)
                return True
        return False

    def handleKeyDownEvent(self, key):
        kb = self.keyBindings
        if key == pygame.K_ESCAPE:
            self.nextScreen = ScreenType.OPTIONS_SCREEN
            self.changeScreen = True
        elif key == kb.getKey("move_up") or key == kb.getKey("alt_move_up"):
            self._handleMovementKey(0)
        elif key == kb.getKey("move_left") or key == kb.getKey("alt_move_left"):
            self._handleMovementKey(1)
        elif key == kb.getKey("move_down") or key == kb.getKey("alt_move_down"):
            self._handleMovementKey(2)
        elif key == kb.getKey("move_right") or key == kb.getKey("alt_move_right"):
            self._handleMovementKey(3)
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
        elif self._handleHotbarKey(key):
            pass
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
        elif key == kb.getKey("codex"):
            self.nextScreen = ScreenType.CODEX_SCREEN
            self.changeScreen = True

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

    def _checkCooldown(self, tickToCheck, speed):
        ticksPerSecond = self.config.ticksPerSecond
        return tickToCheck + ticksPerSecond / speed < self.tickCounter.getTick()

    def checkPlayerMovementCooldown(self, tickToCheck):
        return self._checkCooldown(tickToCheck, self.player.getMovementSpeed())

    def checkPlayerGatherCooldown(self, tickToCheck):
        return self._checkCooldown(tickToCheck, self.player.getGatherSpeed())

    def checkPlayerPlaceCooldown(self, tickToCheck):
        return self._checkCooldown(tickToCheck, self.player.getPlaceSpeed())

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

        # render the room onto a clean off-screen surface so the day/night
        # overlay (and any other display artefacts) are not captured
        gameArea = self.graphik.getGameAreaRect()
        size = (int(gameArea.width), int(gameArea.height))
        offscreen = pygame.Surface(size)
        originalDisplay = self.graphik.gameDisplay
        try:
            self.graphik.gameDisplay = offscreen
            offscreen.fill(self.currentRoom.getBackgroundColor())
            self.currentRoom.draw(self.locationWidth, self.locationHeight)
        finally:
            self.graphik.gameDisplay = originalDisplay

        path = (
            self.config.pathToSaveDirectory
            + "/roompngs/"
            + str(self.currentRoom.getX())
            + "_"
            + str(self.currentRoom.getY())
            + ".png"
        )
        self._pngSavePending.add(roomKey)
        self._saveExecutor.submit(self._saveSurfaceToDisk, offscreen, path, roomKey)

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

    def _iterateVisibleRoomOffsets(self, gameArea):
        """Yield (roomX, roomY, roomOffsetX, roomOffsetY) for visible rooms."""
        playerLocation = self.getLocationOfPlayer()
        playerGridX = playerLocation.getX()
        playerGridY = playerLocation.getY()
        gridSize = self.config.gridSize
        roomPixelWidth = gridSize * self.locationWidth
        roomPixelHeight = gridSize * self.locationHeight
        centerX = gameArea.x + gameArea.width / 2
        centerY = gameArea.y + gameArea.height / 2
        playerPixelX = playerGridX * self.locationWidth + self.locationWidth / 2
        playerPixelY = playerGridY * self.locationHeight + self.locationHeight / 2
        baseOffsetX = centerX - playerPixelX
        baseOffsetY = centerY - playerPixelY
        currentRoomX = self.currentRoom.getX()
        currentRoomY = self.currentRoom.getY()
        halfWidth = gameArea.width / 2
        halfHeight = gameArea.height / 2
        roomsH = int(halfWidth / roomPixelWidth) + 1
        roomsV = int(halfHeight / roomPixelHeight) + 1
        for dx in range(-roomsH, roomsH + 1):
            for dy in range(-roomsV, roomsV + 1):
                roomX = currentRoomX + dx
                roomY = currentRoomY + dy
                if self.config.worldBorder != 0 and (
                    abs(roomX) > self.config.worldBorder
                    or abs(roomY) > self.config.worldBorder
                ):
                    continue
                roomOffsetX = baseOffsetX + dx * roomPixelWidth
                roomOffsetY = baseOffsetY + dy * roomPixelHeight
                if (
                    roomOffsetX + roomPixelWidth < gameArea.x
                    or roomOffsetX > gameArea.right
                    or roomOffsetY + roomPixelHeight < gameArea.y
                    or roomOffsetY > gameArea.bottom
                ):
                    continue
                yield roomX, roomY, roomOffsetX, roomOffsetY

    def _collectLightSourcesFromRoom(self, room, offsetX, offsetY, sources):
        grid = room.getGrid()
        locWidth = self.locationWidth
        locHeight = self.locationHeight
        halfW = locWidth / 2
        halfH = locHeight / 2
        for locationId in grid.getLocations():
            location = grid.getLocation(locationId)
            if location.getNumEntities() == 0:
                continue
            for entity in location.getEntities().values():
                if hasattr(entity, "getLightRadius"):
                    sources.append(
                        (
                            offsetX + location.getX() * locWidth + halfW,
                            offsetY + location.getY() * locHeight + halfH,
                            entity.getLightRadius(),
                        )
                    )

    def drawFollowMode(self):
        gameArea = self.graphik.getGameAreaRect()
        collectLights = self.config.dayNightCycleEnabled
        if collectLights:
            self._frameLightSources = []

        for roomX, roomY, roomOffsetX, roomOffsetY in self._iterateVisibleRoomOffsets(
            gameArea
        ):
            room = self.getOrLoadRoom(roomX, roomY)
            room.drawWithOffset(
                self.locationWidth,
                self.locationHeight,
                roomOffsetX,
                roomOffsetY,
                gameArea.right,
                gameArea.bottom,
            )
            if collectLights:
                self._collectLightSourcesFromRoom(
                    room, roomOffsetX, roomOffsetY, self._frameLightSources
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

    def _drawDayNightOverlay(self, gameArea):
        opacity = self.dayNightCycle.getOverlayOpacity(self.tickCounter.getTick())
        if opacity <= 0:
            return
        overlaySize = (gameArea.width, gameArea.height)
        if (
            self._dayNightOverlay is None
            or self._dayNightOverlaySize != overlaySize
        ):
            self._dayNightOverlay = pygame.Surface(overlaySize, pygame.SRCALPHA)
            self._dayNightOverlaySize = overlaySize
            self.dayNightCycle.clearLightMaskCache()
            self._scaledMaskCache.clear()
        self._dayNightOverlay.fill((0, 0, 0, opacity))
        if opacity != self._lastScaledOpacity:
            self._scaledMaskCache.clear()
            self._lastScaledOpacity = opacity
        for screenX, screenY, radiusTiles in self._frameLightSources:
            overlayX = screenX - gameArea.x
            overlayY = screenY - gameArea.y
            radiusPx = int(radiusTiles * self.locationWidth)
            if radiusPx <= 0:
                continue
            cacheKey = (radiusPx, opacity)
            if cacheKey not in self._scaledMaskCache:
                mask = self.dayNightCycle.getLightMask(radiusPx)
                scaledMask = mask.copy()
                scaledMask.fill(
                    (255, 255, 255, opacity),
                    special_flags=pygame.BLEND_RGBA_MULT,
                )
                self._scaledMaskCache[cacheKey] = scaledMask
            self._dayNightOverlay.blit(
                self._scaledMaskCache[cacheKey],
                (overlayX - radiusPx, overlayY - radiusPx),
                special_flags=pygame.BLEND_RGBA_MIN,
            )
        self.graphik.getGameDisplay().blit(
            self._dayNightOverlay, (gameArea.x, gameArea.y)
        )

    def _drawHotbar(self):
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

    def _drawDebugInfo(self):
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

        # display day/night cycle phase and opacity
        if self.config.dayNightCycleEnabled:
            cyclePhase = self.dayNightCycle.getPhase(tickValue)
            cycleOpacity = self.dayNightCycle.getOverlayOpacity(tickValue)
            xpos = self.graphik.getGameDisplay().get_width() - 100
            ypos = 60
            self.graphik.drawText(
                "Cycle: " + cyclePhase + " (" + str(cycleOpacity) + ")",
                xpos,
                ypos,
                20,
                (255, 255, 255),
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
            if self.config.dayNightCycleEnabled:
                self._frameLightSources = []
                self._collectLightSourcesFromRoom(
                    self.currentRoom, gameArea.x, gameArea.y, self._frameLightSources
                )

        if self.config.dayNightCycleEnabled:
            self._drawDayNightOverlay(gameArea)

        # remove clip so UI draws over the full display
        self.graphik.getGameDisplay().set_clip(None)

        statusOx, statusOy = self.hudDragManager.getOffset("status")
        self.status.draw(statusOx, statusOy)
        energyOx, energyOy = self.hudDragManager.getOffset("energyBar")
        self.energyBar.draw(energyOx, energyOy)

        self._drawHotbar()

        if self.config.debug:
            self._drawDebugInfo()

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

    def _handleHotbarClick(self, hotbarIndex):
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

    def _handleWorldClick(self):
        if pygame.mouse.get_pressed()[0]:  # left click
            self.player.setGathering(True)
        elif pygame.mouse.get_pressed()[2]:  # right click
            self.player.setPlacing(True)

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
            self._handleHotbarClick(hotbarIndex)
            return

        if not self.cursorSlot.isEmpty():
            # clicking outside hotbar with cursor item returns it to inventory
            self.returnCursorSlotToInventory()
            return

        self._handleWorldClick()

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
        if event.y != 0:
            current = self.player.getInventory().getSelectedInventorySlotIndex()
            delta = -1 if event.y > 0 else 1
            self.player.getInventory().setSelectedInventorySlotIndex(
                (current + delta) % 10
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
        self.persistence.savePlayerLocationToFile(self.currentRoom)

    def loadPlayerLocationFromFile(self):
        result = self.persistence.loadPlayerLocationFromFile(self.map)
        if result is not None:
            self.currentRoom = result

    def savePlayerAttributesToFile(self):
        self.persistence.savePlayerAttributesToFile()

    def loadPlayerAttributesFromFile(self):
        self.persistence.loadPlayerAttributesFromFile()

    def savePlayerInventoryToFile(self):
        inventoryJsonReaderWriter = InventoryJsonReaderWriter(self.config)
        self.persistence.savePlayerInventoryToFile(inventoryJsonReaderWriter)

    def loadPlayerInventoryFromFile(self):
        inventoryJsonReaderWriter = InventoryJsonReaderWriter(self.config)
        self.persistence.loadPlayerInventoryFromFile(inventoryJsonReaderWriter)

    def saveCodexToFile(self):
        codexReaderWriter = CodexJsonReaderWriter(self.config)
        codexReaderWriter.save(self.codex.getDiscoveredEntities())

    def loadCodexFromFile(self):
        codexReaderWriter = CodexJsonReaderWriter(self.config)
        entities = codexReaderWriter.load()
        if entities is not None:
            self.codex.setDiscovered(entities)

    def discoverLivingEntitiesInRoom(self):
        for entityId, entity in self.currentRoom.getLivingEntities().items():
            entityClassName = entity.__class__.__name__
            if self.codex.discover(entityClassName):
                self.status.set("New codex entry: " + entityClassName)
                self.saveCodexToFile()

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
        self.saveCodexToFile()

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

    def _processEvents(self):
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

    def _updateLivingEntities(self):
        entitiesToMoveToNewRooms = self.currentRoom.moveLivingEntities(
            self.tickCounter.getTick()
        )
        if len(entitiesToMoveToNewRooms) > 0:
            for entityToMove in entitiesToMoveToNewRooms:
                try:
                    (
                        newRoomX,
                        newRoomY,
                    ) = self.getCoordinatesForNewRoomBasedOnLivingEntityLocation(
                        entityToMove
                    )
                except Exception as e:
                    if self.config.debug:
                        _logger.debug(
                            "error moving entity to new room", error=str(e)
                        )
                    continue
                newRoom = self._loadOrGenerateRoom(newRoomX, newRoomY)

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
                        _logger.debug(
                            "error getting new location for entity", error=str(e)
                        )
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

                self.currentRoom.removeEntity(entityToMove)
                self.currentRoom.removeLivingEntity(entityToMove)

                newRoom.addEntityToLocation(entityToMove, newLocation)
                newRoom.addLivingEntity(entityToMove)

                self.saveRoomToFileAsync(newRoom)

        self.currentRoom.reproduceLivingEntities(self.tickCounter.getTick())

    def _updateGameState(self):
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

    def run(self):
        while not self.changeScreen:
            self._processEvents()
            self._updateLivingEntities()
            self._updateGameState()

        # create save directory if it doesn't exist
        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)

        self.returnCursorSlotToInventory()
        self.saveSynchronous()
        self.shutdown()

        self.changeScreen = False
        return self.nextScreen
