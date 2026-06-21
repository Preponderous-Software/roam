import math
import os
import threading
from concurrent.futures import ThreadPoolExecutor
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
from jsonPersistence import writeJsonAtomically
from mapimage.mapImageUpdater import MapImageUpdater
from screen.pickupableEntities import canBePickedUp as _canBePickedUp
from screen.screenType import ScreenType
from screen.worldScreenPersistence import WorldScreenPersistence
from stats.stats import Stats
from ui.energyBar import EnergyBar
from goals.goals import Goals
from goals.goalsJsonReaderWriter import GoalsJsonReaderWriter
from rendering.renderer import Renderer
from rendering.inputSource import InputSource
from rendering.clock import Clock
from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode
from entity.grass import Grass
from lib.pyenvlib.grid import Grid
from entity.stone import Stone
from entity.woodFloor import WoodFloor
from entity.stoneFloor import StoneFloor
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
from entity.chest import Chest
from entity.gravestone import Gravestone
from entity.wheat import Wheat
from entity.wheatSeed import WheatSeed
from entity.youngCrop import YoungCrop
from entity.matureCrop import MatureCrop
from gameLogging.logger import getLogger
from ui import palette
from ui.geometry import Rect

_logger = getLogger(__name__)

MIDDLE_MOUSE_BUTTON = 2


# @author Daniel McCoy Stephenson
# @since August 16th, 2022
@component
class WorldScreen:
    def __init__(
        self,
        renderer: Renderer,
        inputSource: InputSource,
        clock: Clock,
        config: Config,
        status: Status,
        tickCounter: TickCounter,
        stats: Stats,
        player: Player,
        container: Container,
        keyBindings: KeyBindings,
    ):
        self.renderer = renderer
        self.inputSource = inputSource
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
        self.persistence = self.container.resolve(WorldScreenPersistence)
        self.roomPreloader = self.container.resolve(RoomPreloader)
        self.mapImageUpdater = self.container.resolve(MapImageUpdater)
        self.hudDragManager = self.container.resolve(HudDragManager)
        self.codex = self.container.resolve(Codex)
        self.dayNightCycle = self.container.resolve(DayNightCycle)
        self.goals = self.container.resolve(Goals)
        self.goalsJsonReaderWriter = self.container.resolve(GoalsJsonReaderWriter)
        self.deathRespawnTicksRemaining = 0
        self.pausedByFocusLoss = False
        self._frameLightSources = []
        self.minimapScaleFactor = 0.10
        self.minimapX = 5
        self.minimapY = 5
        self._cachedMiniMapImage = None
        self._miniMapLastLoadTick = 0
        # Tracks whether the last minimap-image load failed, so the failure is
        # logged once on the good->failed transition rather than every reload.
        self._miniMapLoadFailed = False
        self._saveExecutor = ThreadPoolExecutor(
            max_workers=1
        )  # serialize save operations off main thread
        self._saveInProgress = False
        self._saveLock = threading.Lock()
        self._pngSavePending = set()
        self.cursorSlot = InventorySlot()
        self.clock = clock
        self.showHelp = False
        # The chest most recently opened via right-click, and the room it lives
        # in, so the ChestScreen can persist its contents on close.
        self.activeChest = None
        self.activeChestRoom = None
        self._isRunning = False
        self._isCrouching = False

    def initialize(self):
        self.map = self.container.resolve(Map)
        self.currentRoom = None

        if os.path.exists(self.config.pathToSaveDirectory + "/playerLocation.json"):
            self.loadPlayerLocationFromFile()

        if self.currentRoom is None:
            self.currentRoom = self.map.getRoom(0, 0)
            if self.currentRoom == -1:
                self.currentRoom = self.map.generateNewRoom(0, 0)
            self.currentRoom.addEntity(self.player)
            if self.map.consumeIsNewRoom(0, 0):
                self.stats.incrementRoomsExplored()

        if os.path.exists(self.config.pathToSaveDirectory + "/playerAttributes.json"):
            self.loadPlayerAttributesFromFile()

        if os.path.exists(self.config.pathToSaveDirectory + "/stats.json"):
            self.stats.load()

        if os.path.exists(self.config.pathToSaveDirectory + "/tick.json"):
            self.tickCounter.load()

        if os.path.exists(self.config.pathToSaveDirectory + "/goals.json"):
            self.goals.setCompletedIdentifiers(self.goalsJsonReaderWriter.load())

        if os.path.exists(self.config.pathToSaveDirectory + "/playerInventory.json"):
            self.loadPlayerInventoryFromFile()

        if os.path.exists(self.config.pathToSaveDirectory + "/codex.json"):
            self.loadCodexFromFile()

        self.initializeLocationWidthAndHeight()

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
        gameArea = self.renderer.getGameAreaRect()
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
        w, h = self.renderer.getDisplaySize()
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

        if self.isCorner(location):
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
        if self.isCorner(location):
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

    def isCorner(self, location: Location):
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
        roomPath = self.config.getRoomFilePath(room.getX(), room.getY())
        try:
            roomJson = self.roomJsonReaderWriter.generateJsonForRoom(room)
        except Exception as e:
            _logger.error("error preparing room snapshot", error=str(e))
            return
        self._saveExecutor.submit(self._writeJsonToFile, roomJson, roomPath)

    def _writeJsonToFile(self, data, path):
        """Write a pre-built JSON dict to disk. Runs on background thread."""
        try:
            writeJsonAtomically(path, data)
        except Exception as e:
            _logger.error("error writing JSON file", error=str(e), path=path)

    def _loadOrGenerateRoom(self, x, y, updateStats=True):
        wasCached = self.map.hasRoom(x, y)
        room = self.map.getRoom(x, y)
        if room == -1:
            room = self.map.generateNewRoom(x, y)
        if updateStats and self.map.consumeIsNewRoom(x, y):
            self.status.set("New area discovered")
            self.stats.incrementScore()
            self.stats.incrementRoomsExplored()
        elif updateStats and not wasCached:
            self.status.set("Area loaded")
        return room

    def _calculateTargetLocationForRoomTransition(self, playerLocation):
        targetX = playerLocation.getX()
        targetY = playerLocation.getY()
        minCoord = 0
        maxCoord = self.config.gridSize - 1

        if self.isCorner(playerLocation):
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
            self.changeRooms()
            self.save()
            return

        if self.locationContainsSolidEntity(newLocation):
            if self.config.pushableStone and self.tryPushStone(newLocation, direction):
                if self.locationContainsSolidEntity(newLocation):
                    return
            else:
                return

        for entityId in list(newLocation.getEntities().keys()):
            entity = newLocation.getEntity(entityId)
            if isinstance(entity, Bear):
                self.status.set("Killed by " + entity.getName())
                self.player.kill()
                return

        if self.player.needsEnergy():
            for entityId in list(newLocation.getEntities().keys()):
                entity = newLocation.getEntity(entityId)
                if self.player.canEat(entity):
                    newLocation.removeEntity(entity)
                    self.player.addEnergy(entity.getEnergy())

                    self.stats.incrementFoodEaten()

                    self.status.set("Ate " + entity.getName())

                    self.stats.incrementScore()

        location.removeEntity(self.player)
        newLocation.addEntity(self.player)

        self.player.removeEnergy(self.config.playerMovementEnergyCost)
        self.player.setTickLastMoved(self.tickCounter.getTick())

    def canBePickedUp(self, entity):
        return _canBePickedUp(entity)

    def getLocationAndRoomAtMousePosition(self):
        x, y = self.inputSource.getMousePosition()
        gameArea = self.renderer.getGameAreaRect()
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

    def _tryHarvestCrop(self, targetLocation, targetRoom):
        """Check for crop interactions. Returns True if a crop was found (harvested or not ready)."""
        for entityId in list(reversed(targetLocation.getEntities())):
            entity = targetLocation.getEntity(entityId)
            if isinstance(entity, YoungCrop):
                self.status.set("Crop is not ready")
                return True
            if isinstance(entity, MatureCrop):
                wheat = Wheat()
                if not self.player.getInventory().placeIntoFirstAvailableInventorySlot(
                    wheat
                ):
                    self.status.set("Inventory full")
                    return True
                targetRoom.removeEntity(entity)
                self.status.set("Harvested Wheat")
                self.player.removeEnergy(self.config.playerInteractionEnergyCost)
                self.player.setTickLastGathered(self.tickCounter.getTick())
                return True
        return False

    def executeGatherAction(self):
        targetLocation, targetRoom = self.getLocationAndRoomAtMousePosition()
        if targetLocation == -1:
            self.status.set("Nothing to pick up here")
            return
        if self.isLocationTooFar(targetLocation, targetRoom):
            self.status.set("Too far away")
            return
        self._executeGatherAt(targetLocation, targetRoom)

    def _lookAtFacingTile(self):
        location = self.getLocationInFrontOfPlayer()
        if location == -1:
            self.status.set("Nothing ahead")
            return
        entities = [
            location.getEntity(eid).getName()
            for eid in location.getEntities()
        ]
        if entities:
            self.status.set("Ahead: " + ", ".join(entities))
        else:
            self.status.set("Nothing notable ahead")

    def executeGatherAtFront(self):
        targetLocation = self.getLocationInFrontOfPlayer()
        if targetLocation == -1:
            self.status.set("Nothing to pick up here")
            return
        self._executeGatherAt(targetLocation, self.currentRoom)

    def _executeGatherAt(self, targetLocation, targetRoom):
        if self._tryHarvestCrop(targetLocation, targetRoom):
            return

        toRemove = None
        for entityId in list(reversed(targetLocation.getEntities())):
            entity = targetLocation.getEntity(entityId)
            if self.canBePickedUp(entity):
                toRemove = entity
                break

        if toRemove is None:
            nonEmptyChestPresent = any(
                isinstance(targetLocation.getEntity(entityId), Chest)
                and targetLocation.getEntity(entityId)
                .getStoredInventory()
                .getNumItems()
                > 0
                for entityId in targetLocation.getEntities()
            )
            if nonEmptyChestPresent:
                self.status.set("Empty the chest before picking it up")
            else:
                self.status.set("Nothing to pick up here")
            return

        if not self.player.getInventory().placeIntoFirstAvailableInventorySlot(
            toRemove
        ):
            self.status.set("Inventory full")
            return
        targetRoom.removeEntity(toRemove)
        if isinstance(toRemove, LivingEntity):
            targetRoom.removeLivingEntity(toRemove)
        self.status.set("Picked up " + toRemove.getName())
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

    def locationContainsFloor(self, location):
        for entityId in list(location.getEntities().keys()):
            entity = location.getEntity(entityId)
            if isinstance(entity, (WoodFloor, StoneFloor)):
                return True
        return False

    def tryPushStone(self, location, direction):
        stoneEntity = None
        for entityId in list(location.getEntities().keys()):
            entity = location.getEntity(entityId)
            if isinstance(entity, Stone):
                stoneEntity = entity
                break

        if stoneEntity is None:
            return False

        pushDestination = self.getLocationDirection(
            direction, self.currentRoom.getGrid(), location
        )

        if pushDestination == -1:
            # stone is at a room border, try to push into adjacent room
            return self.tryPushStoneToAdjacentRoom(stoneEntity, location, direction)

        if self.locationContainsSolidEntity(pushDestination):
            return False

        location.removeEntity(stoneEntity)
        pushDestination.addEntity(stoneEntity)
        return True

    def tryPushStoneToAdjacentRoom(self, stoneEntity, location, direction):
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

        if self.config.worldBorder != 0 and (
            abs(roomX) > self.config.worldBorder or abs(roomY) > self.config.worldBorder
        ):
            return False

        adjacentRoom = self.getOrLoadRoom(roomX, roomY)

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

        location.removeEntity(stoneEntity)
        targetLocation.addEntity(stoneEntity)
        self.saveRoomToFileAsync(adjacentRoom)
        return True

    def executePlaceAction(self):
        targetLocation, targetRoom = self.getLocationAndRoomAtMousePosition()
        if targetLocation == -1:
            self.status.set("Cannot place here")
            return
        if targetLocation == -2:
            self.status.set("Stop moving to place items")
            return
        if self.isLocationTooFar(targetLocation, targetRoom):
            self.status.set("Too far away")
            return
        self._executePlaceAt(targetLocation, targetRoom)

    def executePlaceAtFront(self):
        targetLocation = self.getLocationInFrontOfPlayer()
        if targetLocation == -1:
            self.status.set("Cannot place here")
            return
        self._executePlaceAt(targetLocation, self.currentRoom)

    def _executePlaceAt(self, targetLocation, targetRoom):
        # Check for chest/gravestone interaction before checking solid/blocked
        for entityId in list(targetLocation.getEntities().keys()):
            entity = targetLocation.getEntity(entityId)
            if isinstance(entity, Chest):
                self._openChest(entity, targetRoom)
                return
            if isinstance(entity, Gravestone):
                self._interactWithGravestone(entity, targetRoom, targetLocation)
                return

        if self.player.getInventory().getNumTakenInventorySlots() == 0:
            self.status.set("No items to place")
            return

        if self.locationContainsSolidEntity(targetLocation):
            self.status.set("Location is blocked")
            return

        for entityId in list(targetLocation.getEntities().keys()):
            entity = targetLocation.getEntity(entityId)
            if isinstance(entity, LivingEntity):
                self.status.set("Blocked by " + entity.getName())
                return

        inventorySlot = self.player.getInventory().getSelectedInventorySlot()
        if inventorySlot.isEmpty():
            firstKey = self.keyBindings.getKeyName("hotbar_1").upper()
            zeroKey = self.keyBindings.getKeyName("hotbar_0").upper()
            self.status.set(f"Select an item first ({firstKey}-{zeroKey})")
            return

        selectedItem = inventorySlot.getContents()[0]
        if isinstance(selectedItem, WheatSeed):
            self._plantWheatSeed(targetLocation, targetRoom)
            return

        isFloor = isinstance(selectedItem, (WoodFloor, StoneFloor))
        if isFloor and self.locationContainsFloor(targetLocation):
            self.status.set("A floor is already here")
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

    def _openChest(self, chest, targetRoom):
        self.returnCursorSlotToInventory()
        self.activeChest = chest
        self.activeChestRoom = targetRoom
        self.nextScreen = ScreenType.CHEST_SCREEN
        self.changeScreen = True

    def getActiveChest(self):
        return self.activeChest

    def saveActiveChestRoom(self):
        if self.activeChestRoom is not None:
            self.saveRoomToFileAsync(self.activeChestRoom)

    def _interactWithGravestone(self, gravestone, targetRoom, targetLocation):
        storedInventory = gravestone.getStoredInventory()
        # Collect all items to transfer
        itemsToTransfer = []
        for slot in storedInventory.getInventorySlots():
            if slot.isEmpty():
                continue
            for item in list(slot.getContents()):
                itemsToTransfer.append(item)

        # Pre-check capacity: simulate placement to ensure all items fit
        if not self._inventoryCanFitAll(self.player.getInventory(), itemsToTransfer):
            self.status.set("Inventory full")
            return

        # All items fit — transfer atomically
        for item in itemsToTransfer:
            self.player.getInventory().placeIntoFirstAvailableInventorySlot(item)
        targetRoom.removeEntity(gravestone)
        self.status.set("Retrieved items from Gravestone")

    def _inventoryCanFitAll(self, inventory, items):
        """Return True if all items can be placed into inventory without overflow."""
        # Available space in existing non-empty slots keyed by item name
        slotSpace = {}
        freeSlots = 0
        maxStack = 20
        for slot in inventory.getInventorySlots():
            maxStack = slot.getMaxStackSize()
            if slot.isEmpty():
                freeSlots += 1
            else:
                name = slot.getContents()[0].getName()
                available = maxStack - slot.getNumItems()
                if available > 0:
                    slotSpace[name] = slotSpace.get(name, 0) + available
        for item in items:
            name = item.getName()
            if slotSpace.get(name, 0) > 0:
                slotSpace[name] -= 1
            elif freeSlots > 0:
                freeSlots -= 1
                # Opening a new slot gives (maxStack - 1) additional spaces
                slotSpace[name] = slotSpace.get(name, 0) + (maxStack - 1)
            else:
                return False
        return True

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
        if key == KeyCode.ESCAPE:
            if self.showHelp:
                self.showHelp = False
                return
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
            result = self.renderer.captureScreenshot()
            self.status.set("Screenshot saved" if result else "Screenshots not supported in this mode")
        elif key == kb.getKey("run"):
            self.player.setMovementSpeed(
                self.player.getMovementSpeed() * self.config.runSpeedFactor
            )
        elif key == kb.getKey("crouch"):
            self.player.setCrouching(True)
        elif key == kb.getKey("run_toggle"):
            if self._isRunning:
                self.player.setMovementSpeed(
                    self.player.getMovementSpeed() / self.config.runSpeedFactor
                )
                self._isRunning = False
                self.status.set("Run: OFF")
            else:
                self.player.setMovementSpeed(
                    self.player.getMovementSpeed() * self.config.runSpeedFactor
                )
                self._isRunning = True
                self.status.set("Run: ON")
        elif key == kb.getKey("crouch_toggle"):
            self._isCrouching = not self._isCrouching
            self.player.setCrouching(self._isCrouching)
            self.status.set("Crouch: " + ("ON" if self._isCrouching else "OFF"))
        elif key == kb.getKey("inventory"):
            self.switchToInventoryScreen()
            if self.player.isGathering():
                self.player.setGathering(False)
            if self.player.isPlacing():
                self.player.setPlacing(False)
        elif not self._handleHotbarKey(key):
            self._handleUtilityKey(key, kb)

    def _handleUtilityKey(self, key, kb):
        if key == kb.getKey("toggle_debug"):
            self.config.debug = not self.config.debug
            self.status.set("Debug info " + ("ON" if self.config.debug else "OFF"))
        elif key == kb.getKey("toggle_minimap"):
            self.config.showMiniMap = not self.config.showMiniMap
            self.status.set("Minimap " + ("ON" if self.config.showMiniMap else "OFF"))
        elif key == kb.getKey("minimap_zoom_in"):
            if self.minimapScaleFactor < 1.0:
                self.minimapScaleFactor = min(1.0, self.minimapScaleFactor + 0.1)
            else:
                self.status.set("Minimap at maximum size")
        elif key == kb.getKey("minimap_zoom_out"):
            # Floor at the default 0.1 so the minimap can't be shrunk away to
            # nothing, and tell the player when they've hit the limit.
            if self.minimapScaleFactor > 0.1:
                self.minimapScaleFactor = max(0.1, self.minimapScaleFactor - 0.1)
            else:
                self.status.set("Minimap at minimum size")
        elif key == kb.getKey("toggle_camera_follow"):
            self.config.cameraFollowPlayer = not self.config.cameraFollowPlayer
            self.status.set(
                "Camera follow " + ("ON" if self.config.cameraFollowPlayer else "OFF")
            )
        elif key == kb.getKey("toggle_help"):
            self.showHelp = not self.showHelp
        elif key == kb.getKey("look"):
            self._lookAtFacingTile()
        elif key == kb.getKey("gather"):
            if self.checkPlayerGatherCooldown(self.player.getTickLastGathered()):
                self.executeGatherAtFront()
        elif key == kb.getKey("place"):
            if self.checkPlayerPlaceCooldown(self.player.getTickLastPlaced()):
                self.executePlaceAtFront()
        elif key == kb.getKey("codex"):
            self.nextScreen = ScreenType.CODEX_SCREEN
            self.changeScreen = True
        elif key == KeyCode.LEFTBRACKET:
            current = self.player.getInventory().getSelectedInventorySlotIndex()
            self.changeSelectedInventorySlot((current - 1) % 10)
        elif key == KeyCode.RIGHTBRACKET:
            current = self.player.getInventory().getSelectedInventorySlotIndex()
            self.changeSelectedInventorySlot((current + 1) % 10)

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
        playerLocationId = self.player.getLocationID()
        playerLocation = self.currentRoom.getGrid().getLocation(playerLocationId)

        # Collect all items into a gravestone at the player's location
        gravestone = Gravestone()
        hasItems = False
        for inventorySlot in self.player.getInventory().getInventorySlots():
            if inventorySlot.isEmpty():
                continue
            for item in inventorySlot.getContents():
                gravestone.getStoredInventory().placeIntoFirstAvailableInventorySlot(
                    item
                )
                hasItems = True
        self.player.getInventory().clear()

        if hasItems:
            self.currentRoom.addEntityToLocation(gravestone, playerLocation)

        self.currentRoom.removeEntity(self.player)
        self.map.getRoom(0, 0).addEntity(self.player)

        self.save()

        self.currentRoom = self.map.getRoom(0, 0)
        self.player.energy = self.player.targetEnergy
        if self._isRunning:
            self.player.setMovementSpeed(
                self.player.getMovementSpeed() / self.config.runSpeedFactor
            )
            self._isRunning = False
        if self._isCrouching:
            self.player.setCrouching(False)
            self._isCrouching = False
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
        if self.player.isDead() and self.deathRespawnTicksRemaining == 0:
            self.status.set("You died! Respawning...")
            self.stats.setScore(math.floor(self.stats.getScore() * 0.9))
            self.stats.incrementNumberOfDeaths()
            self.deathRespawnTicksRemaining = max(
                1, int(self.config.ticksPerSecond * 3)
            )

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

        locationOfPlayer = self.currentRoom.getGrid().getLocation(
            self.player.getLocationID()
        )
        self.currentRoom.removeEntity(self.player)

        # render the room onto a clean off-screen surface so the day/night
        # overlay (and any other display artefacts) are not captured
        gameArea = self.renderer.getGameAreaRect()
        size = (int(gameArea.width), int(gameArea.height))
        offscreen = self.renderer.createSurface(size)
        originalTarget = self.renderer.getRenderTarget()
        try:
            self.renderer.setRenderTarget(offscreen)
            self.renderer.clearScreen(self.currentRoom.getBackgroundColor())
            self.currentRoom.draw(self.locationWidth, self.locationHeight)
        finally:
            self.renderer.setRenderTarget(originalTarget)

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

        self.currentRoom.addEntityToLocation(self.player, locationOfPlayer)

    def _saveSurfaceToDisk(self, surface, path, roomKey):
        """Save a rendered surface to disk. Runs on a background thread.
        Acquires roompngsLock to avoid racing with clearRoomImages()."""
        try:
            with self.mapImageUpdater.roompngsLock:
                self.renderer.saveImage(surface, path)
        except Exception as e:
            _logger.error("error saving room PNG", error=str(e), path=path)
        finally:
            self._pngSavePending.discard(roomKey)

    def _drawTextMinimap(self):
        minimapOx, minimapOy = self.hudDragManager.getOffset("minimap")
        drawX = self.minimapX + minimapOx
        drawY = self.minimapY + minimapOy
        roomX = self.currentRoom.getX()
        roomY = self.currentRoom.getY() * -1
        dirArrows = {0: "^", 1: "<", 2: "v", 3: ">"}
        facing = dirArrows.get(self.player.getDirection(), ".")
        label = f"[{roomX},{roomY}] {facing}"
        self.renderer.drawRectangle(drawX, drawY, 80, 20, palette.NEAR_BLACK)
        self.renderer.drawText(label, drawX + 40, drawY + 10, 12, palette.MEDIUM_GRAY)

    def drawMiniMap(self):
        if not self.renderer.supportsImageLoading():
            self._drawTextMinimap()
            return
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
                loaded = self.renderer.tryLoadImage(mapImagePath)
                if loaded is not None:
                    mapImage = loaded
                    self._cachedMiniMapImage = mapImage
                    self._miniMapLastLoadTick = currentTick
                    self._miniMapLoadFailed = False
                else:
                    # Log once on the good->failed transition so a persistently
                    # missing/corrupt mapImage.png is diagnosable, without
                    # spamming a log line on every 60-tick reload attempt.
                    if not self._miniMapLoadFailed:
                        _logger.warning(
                            "could not load minimap image; "
                            "keeping last good frame if available",
                            path=mapImagePath,
                        )
                        self._miniMapLoadFailed = True
                    if self._cachedMiniMapImage is not None:
                        mapImage = self._cachedMiniMapImage
                    else:
                        return
            else:
                mapImage = self._cachedMiniMapImage

        gameArea = self.renderer.getGameAreaRect()
        minimapSize = gameArea.width * self.minimapScaleFactor
        mapImage = self.renderer.scaleImage(
            mapImage,
            (
                minimapSize,
                minimapSize,
            ),
        )

        minimapOx, minimapOy = self.hudDragManager.getOffset("minimap")
        drawX = self.minimapX + minimapOx
        drawY = self.minimapY + minimapOy

        backgroundColor = palette.GRAY
        # mapImage was scaled to (minimapSize, minimapSize) above, so its drawn
        # footprint is minimapSize on each side (avoids reading surface metrics).
        self.renderer.drawRectangle(
            drawX,
            drawY,
            minimapSize + 20,
            minimapSize + 20,
            backgroundColor,
        )

        # blit in top left corner with 10px padding
        self.renderer.drawImage(mapImage, (drawX + 10, drawY + 10))

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
        gameArea = self.renderer.getGameAreaRect()
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

    def _drawPausedOverlay(self):
        width, height = self.renderer.getDisplaySize()
        self.renderer.drawTranslucentOverlay((0, 0, 0, 140))
        self.renderer.drawText(
            "PAUSED", width / 2, height / 2 - 20, 56, palette.LIGHT_GRAY
        )
        resumeHint = (
            "Press any key to resume"
            if not self.renderer.supportsImageLoading()
            else "Click the window or press any key to resume"
        )
        self.renderer.drawText(resumeHint, width / 2, height / 2 + 28, 22, palette.MEDIUM_GRAY)

    def _drawDayNightPhaseIndicator(self):
        phase = self.dayNightCycle.getPhase(self.tickCounter.getTick())
        label = phase.capitalize()
        phaseColors = {
            "day": (255, 220, 90),
            "dusk": (240, 140, 90),
            "night": (140, 160, 255),
            "dawn": (255, 180, 140),
        }
        color = phaseColors.get(phase, palette.LIGHT_GRAY)
        self.renderer.drawText(label, 30, 20, 18, color)

    def _drawDeathOverlay(self):
        width, height = self.renderer.getDisplaySize()
        self.renderer.drawTranslucentOverlay((0, 0, 0, 160))
        self.renderer.drawText(
            "YOU DIED", width / 2, height / 2 - 30, 64, (220, 60, 60)
        )
        secondsLeft = max(
            1,
            int(
                (self.deathRespawnTicksRemaining + self.config.ticksPerSecond - 1)
                / self.config.ticksPerSecond
            ),
        )
        self.renderer.drawText(
            f"Respawning in {secondsLeft}...",
            width / 2,
            height / 2 + 30,
            28,
            palette.LIGHT_GRAY,
        )

    def drawHelpOverlay(self):
        x, y = self.renderer.getDisplaySize()
        overlayWidth = x * 0.6
        overlayHeight = y * 0.75
        overlayX = x / 2 - overlayWidth / 2
        overlayY = y / 2 - overlayHeight / 2

        self.renderer.drawRectangle(
            overlayX, overlayY, overlayWidth, overlayHeight, palette.NEAR_BLACK
        )

        kb = self.keyBindings

        titleY = overlayY + 25
        closeKeyName = kb.getKeyName("toggle_help").upper()
        self.renderer.drawText(
            f"Controls  ({closeKeyName} to close)",
            x / 2,
            titleY,
            28,
            palette.WHITE,
        )

        def keyName(action):
            return kb.getKeyName(action).upper()

        isTextMode = not self.renderer.supportsImageLoading()
        if isTextMode:
            helpLines = [
                "W/A/S/D or Arrows  -  Move",
                f"{keyName('gather')}  -  Gather / Pick up (facing tile)",
                f"{keyName('place')}  -  Place / open chest (facing tile)",
                "1-0  -  Select hotbar slot",
                "[ ]  -  Cycle hotbar",
                f"{keyName('inventory')}  -  Open / Close inventory",
                f"{keyName('run_toggle')}  -  Run toggle",
                f"{keyName('crouch_toggle')}  -  Crouch toggle",
                f"{keyName('look')}  -  Examine facing tile",
                f"{keyName('toggle_minimap')}  -  Toggle minimap",
                f"{keyName('toggle_camera_follow')}  -  Toggle camera follow",
                f"{keyName('toggle_debug')}  -  Toggle debug info",
                f"{keyName('screenshot')}  -  Take screenshot (saved as .txt)",
                f"{keyName('codex')}  -  Open Codex",
                "Esc  -  Open menu",
                f"{keyName('toggle_help')}  -  Toggle this help",
            ]
        else:
            helpLines = [
                "W/A/S/D or Arrows  -  Move",
                f"Left Click / {keyName('gather')}  -  Gather / Pick up (facing tile)",
                f"Right Click / {keyName('place')}  -  Place item / open chest (facing tile)",
                "Middle Click  -  Drag HUD elements to reposition",
                "1-0  -  Select hotbar slot",
                "Scroll Wheel / [ ]  -  Cycle hotbar",
                f"{keyName('inventory')}  -  Open / Close inventory",
                f"{keyName('run')}  -  Run (hold)  /  {keyName('run_toggle')}  -  Run toggle",
                f"{keyName('crouch')}  -  Crouch (hold)  /  {keyName('crouch_toggle')}  -  Crouch toggle",
                f"{keyName('look')}  -  Examine facing tile",
                f"{keyName('toggle_minimap')}  -  Toggle minimap",
                f"{keyName('minimap_zoom_in')}/{keyName('minimap_zoom_out')}  -  Resize minimap",
                f"{keyName('toggle_camera_follow')}  -  Toggle camera follow",
                f"{keyName('toggle_debug')}  -  Toggle debug info",
                f"{keyName('screenshot')}  -  Take screenshot",
                f"{keyName('codex')}  -  Open Codex",
                "Esc  -  Open menu",
                f"{keyName('toggle_help')}  -  Toggle this help",
            ]

        lineY = titleY + 40
        lineSpacing = 24
        for line in helpLines:
            self.renderer.drawText(line, x / 2, lineY, 20, palette.LIGHT_GRAY)
            lineY += lineSpacing

    def _getHotbarDefaultRect(self):
        """Return the default bounding rect for the hotbar (no drag offset)."""
        displayWidth = self.renderer.getDisplayWidth()
        displayHeight = self.renderer.getDisplayHeight()
        itemPreviewXPos = displayWidth / 2 - HOTBAR_SLOT_SIZE * 5 - HOTBAR_SLOT_SIZE / 2
        itemPreviewYPos = displayHeight - HOTBAR_BOTTOM_OFFSET
        barXPos = itemPreviewXPos - HOTBAR_PADDING
        barYPos = itemPreviewYPos - HOTBAR_PADDING
        barWidth = HOTBAR_SLOT_SIZE * 11 + HOTBAR_PADDING
        barHeight = HOTBAR_SLOT_SIZE + HOTBAR_PADDING * 2
        return Rect(barXPos, barYPos, barWidth, barHeight)

    def _getMinimapDefaultRect(self):
        """Return the default bounding rect for the minimap (no drag offset)."""
        gameArea = self.renderer.getGameAreaRect()
        minimapSize = gameArea.width * self.minimapScaleFactor
        return Rect(
            self.minimapX,
            self.minimapY,
            minimapSize + 20,
            minimapSize + 20,
        )

    def _drawDayNightOverlay(self, gameArea):
        opacity = self.dayNightCycle.getOverlayOpacity(self.tickCounter.getTick())
        if opacity <= 0:
            return
        # Game logic decides how dark it is and where the lights are; the
        # Renderer owns the per-pixel dimming + light-mask compositing (so a
        # text/null backend simply skips it — epic #433 / #463).
        lightSources = [
            (screenX, screenY, int(radiusTiles * self.locationWidth))
            for screenX, screenY, radiusTiles in self._frameLightSources
        ]
        self.renderer.drawDayNightOverlay(
            (gameArea.x, gameArea.y, gameArea.width, gameArea.height),
            opacity,
            lightSources,
        )

    def _drawHotbarSelectionIndicator(self, xPos, yPos, slotWidth, slotHeight):
        self.renderer.drawSelectionHighlight(xPos, yPos, slotWidth, slotHeight, (255, 255, 0))

    def _drawHotbar(self):
        hotbarOx, hotbarOy = self.hudDragManager.getOffset("hotbar")
        slotStartX = (
            self.renderer.getDisplayWidth() / 2
            - HOTBAR_SLOT_SIZE * 5
            - HOTBAR_SLOT_SIZE / 2
        ) + hotbarOx
        slotY = self.renderer.getDisplayHeight() - HOTBAR_BOTTOM_OFFSET + hotbarOy

        barXPos = slotStartX - HOTBAR_PADDING
        barYPos = slotY - HOTBAR_PADDING
        barWidth = HOTBAR_SLOT_SIZE * 11 + HOTBAR_PADDING
        barHeight = HOTBAR_SLOT_SIZE + HOTBAR_PADDING * 2
        self.renderer.drawRectangle(
            barXPos, barYPos, barWidth, barHeight, palette.BLACK
        )

        isTextMode = not self.renderer.supportsImageLoading()
        selectedIndex = self.player.getInventory().getSelectedInventorySlotIndex()
        firstTenInventorySlots = self.player.getInventory().getFirstTenInventorySlots()
        slotX = slotStartX
        for i, inventorySlot in enumerate(firstTenInventorySlots):
            if inventorySlot.isEmpty():
                self.renderer.drawRectangle(
                    slotX, slotY, HOTBAR_SLOT_SIZE, HOTBAR_SLOT_SIZE, palette.WHITE
                )
                if isTextMode:
                    self.renderer.drawImage("-", (slotX, slotY))
            else:
                item = inventorySlot.getContents()[0]
                scaledImage = self.renderer.scaleImage(
                    self.renderer.loadImage(item.getImagePath()),
                    (HOTBAR_SLOT_SIZE, HOTBAR_SLOT_SIZE),
                )
                self.renderer.drawImage(scaledImage, (slotX, slotY))
                self.renderer.drawText(
                    str(inventorySlot.getNumItems()),
                    slotX + HOTBAR_SLOT_SIZE - 20,
                    slotY + HOTBAR_SLOT_SIZE - 20,
                    20,
                    palette.WHITE,
                )

            if i == selectedIndex:
                self._drawHotbarSelectionIndicator(
                    slotX, slotY, HOTBAR_SLOT_SIZE, HOTBAR_SLOT_SIZE
                )

            if isTextMode:
                label = str(i + 1) if i < 9 else "0"
                self.renderer.drawTextLeftAligned(
                    label, slotX, slotY - HOTBAR_SLOT_SIZE // 2, 12, palette.MEDIUM_GRAY
                )

            slotX += HOTBAR_SLOT_SIZE + HOTBAR_SLOT_GAP

        if isTextMode:
            selectedSlot = self.player.getInventory().getSelectedInventorySlot()
            if not selectedSlot.isEmpty():
                item = selectedSlot.getContents()[0]
                count = selectedSlot.getNumItems()
                itemLabel = f"{item.getName()} x{count}" if count > 1 else item.getName()
            else:
                itemLabel = "-"
            self.renderer.drawText(
                itemLabel,
                self.renderer.getDisplayWidth() / 2,
                slotY + HOTBAR_SLOT_SIZE + 16,
                14,
                palette.LIGHT_GRAY,
            )

    def _drawDebugInfo(self):
        displayWidth = self.renderer.getDisplayWidth()
        displayHeight = self.renderer.getDisplayHeight()
        tickValue = self.tickCounter.getTick()
        measuredTps = int(self.tickCounter.getMeasuredTicksPerSecond())
        peakTps = int(self.tickCounter.getHighestMeasuredTicksPerSecond())
        rightX = displayWidth - 100
        white = palette.WHITE

        self.renderer.drawText(
            "Tick: " + str(tickValue) + " (" + str(measuredTps) + " TPS)",
            rightX,
            20,
            20,
            white,
        )
        self.renderer.drawText("Peak TPS: " + str(peakTps), rightX, 40, 20, white)

        roomX = self.currentRoom.getX()
        roomY = self.currentRoom.getY() * -1
        coordinatesText = "(" + str(roomX) + ", " + str(roomY) + ")"
        coordY = displayHeight - 40 if self.config.showMiniMap else 20
        self.renderer.drawText(coordinatesText, 30, coordY, 20, white)

        if self.config.dayNightCycleEnabled:
            cyclePhase = self.dayNightCycle.getPhase(tickValue)
            cycleOpacity = self.dayNightCycle.getOverlayOpacity(tickValue)
            self.renderer.drawText(
                "Cycle: " + cyclePhase + " (" + str(cycleOpacity) + ")",
                rightX,
                60,
                20,
                white,
            )

    def draw(self):
        gameArea = self.renderer.getGameAreaRect()

        if self.config.showMiniMap and not self.isCurrentRoomSavedAsPNG():
            self.saveCurrentRoomAsPNG()

        self.renderer.clearScreen(palette.BLACK)

        self.renderer.setClipRegion(gameArea)
        self.renderer.clearScreen(self.currentRoom.getBackgroundColor())

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

        self.renderer.setClipRegion(None)

        statusOx, statusOy = self.hudDragManager.getOffset("status")
        self.status.draw(statusOx, statusOy)
        energyOx, energyOy = self.hudDragManager.getOffset("energyBar")
        self.energyBar.draw(energyOx, energyOy)

        self._drawHotbar()

        if self.config.dayNightCycleEnabled:
            self._drawDayNightPhaseIndicator()

        if self.config.debug:
            self._drawDebugInfo()

        if self.config.showMiniMap and self.minimapScaleFactor > 0:
            self.drawMiniMap()
        elif not self.renderer.supportsImageLoading():
            self._drawTextMinimap()

        if not self.showHelp:
            helpKeyName = self.keyBindings.getKeyName("toggle_help").upper()
            hintLabel = f"{helpKeyName}: Help"
            hintX = self.renderer.getDisplayWidth() - 50
            hintY = self.renderer.getDisplayHeight() - 20
            self.renderer.drawText(hintLabel, hintX, hintY, 16, palette.MEDIUM_GRAY)

        self.drawCursorSlot()

        if self.deathRespawnTicksRemaining > 0:
            self._drawDeathOverlay()

        if self.pausedByFocusLoss:
            self._drawPausedOverlay()

        if self.showHelp:
            self.drawHelpOverlay()

        self.renderer.present()

    def getHotbarSlotAtMousePosition(self):
        x, y = self.inputSource.getMousePosition()
        displayWidth = self.renderer.getDisplayWidth()
        displayHeight = self.renderer.getDisplayHeight()
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
        image = self.renderer.loadImage(item.getImagePath())
        scaledImage = self.renderer.scaleImage(image, (50, 50))
        self.renderer.drawImage(scaledImage, self.inputSource.getMousePosition())
        numItems = self.cursorSlot.getNumItems()
        if numItems > 1:
            mouseX, mouseY = self.inputSource.getMousePosition()
            self.renderer.drawText(
                str(numItems),
                mouseX + 30,
                mouseY + 30,
                20,
                palette.WHITE,
            )

    def _handleHotbarClick(self, hotbarIndex):
        inventory = self.player.getInventory()
        hotbarSlot = inventory.getInventorySlots()[hotbarIndex]
        if self.inputSource.getMouseButtons()[2]:  # right click
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
        elif self.inputSource.getMouseButtons()[0]:  # left click
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
        if self.inputSource.getMouseButtons()[0]:  # left click
            self.player.setGathering(True)
        elif self.inputSource.getMouseButtons()[2]:  # right click
            self.player.setPlacing(True)

    def handleMouseDownEvent(self, event):
        # Middle-click initiates HUD drag
        if event.button == MIDDLE_MOUSE_BUTTON:
            mx, my = self.inputSource.getMousePosition()
            self.hudDragManager.handleMouseDown(mx, my)
            return

        if self.showInventory:
            invKey = self.keyBindings.getKeyName("inventory").upper()
            self.status.set(f"Close inventory first ({invKey})")
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
            mx, my = self.inputSource.getMousePosition()
            sw = self.renderer.getDisplayWidth()
            sh = self.renderer.getDisplayHeight()
            self.hudDragManager.handleMouseUp(mx, my, sw, sh)
            return
        if not self.inputSource.getMouseButtons()[0]:
            self.player.setGathering(False)
        if not self.inputSource.getMouseButtons()[2]:
            self.player.setPlacing(False)

    def handleMouseMotionEvent(self):
        if self.hudDragManager.isDragging():
            mx, my = self.inputSource.getMousePosition()
            sw = self.renderer.getDisplayWidth()
            sh = self.renderer.getDisplayHeight()
            self.hudDragManager.handleMouseMotion(mx, my, sw, sh)

    def handleMouseWheelEvent(self, event):
        if event.scrollY != 0:
            current = self.player.getInventory().getSelectedInventorySlotIndex()
            delta = -1 if event.scrollY > 0 else 1
            # Route through changeSelectedInventorySlot so a wheel-cycle announces
            # the newly selected slot the same way the number keys do.
            self.changeSelectedInventorySlot((current + delta) % 10)

    def handleMouseOver(self):
        location = self.getLocationAtMousePosition()
        if location == -1:
            # mouse is not over a location
            return
        livingDescribed = False
        fallbackName = None
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
                livingDescribed = True
                break
            if fallbackName is None and hasattr(entity, "getName"):
                if isinstance(entity, Chest):
                    if entity.getStoredInventory().getNumItems() > 0:
                        fallbackName = "Chest (contains items)"
                    else:
                        fallbackName = "Chest (empty)"
                else:
                    fallbackName = entity.getName()
        if not livingDescribed and fallbackName is not None:
            self.status.set(fallbackName)

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
        if not self.persistence.savePlayerInventoryToFile(inventoryJsonReaderWriter):
            self.status.set("Could not save inventory (invalid data)")

    def loadPlayerInventoryFromFile(self):
        inventoryJsonReaderWriter = InventoryJsonReaderWriter(self.config)
        self.persistence.loadPlayerInventoryFromFile(inventoryJsonReaderWriter)

    def saveCodexToFile(self):
        codexReaderWriter = CodexJsonReaderWriter(self.config)
        if not codexReaderWriter.save(self.codex.getDiscoveredEntities()):
            self.status.set("Could not save codex (invalid data)")

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
        currentLocationX = currentLocation.getX()
        currentLocationY = currentLocation.getY()
        gridEdge = self.currentRoom.getGrid().getRows() - 1

        if self.isCorner(currentLocation):
            raise Exception("corner movement not supported yet")

        if currentLocationX == 0:
            return gridEdge, currentLocationY
        elif currentLocationX == gridEdge:
            return 0, currentLocationY
        elif currentLocationY == 0:
            return currentLocationX, gridEdge
        elif currentLocationY == gridEdge:
            return currentLocationX, 0
        else:
            raise Exception("Living entity is not on the edge of the room")

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
        roomPath = self.config.getRoomFilePath(
            self.currentRoom.getX(), self.currentRoom.getY()
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
                writeJsonAtomically(roomPath, roomJson)
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
        for event in self.inputSource.pollEvents():
            if event.type == EventType.QUIT:
                self.printStatsToConsole()
                self.nextScreen = ScreenType.NONE
                self.changeScreen = True
            elif event.type == EventType.KEY_DOWN:
                self.handleKeyDownEvent(event.key)
            elif event.type == EventType.KEY_UP:
                self.handleKeyUpEvent(event.key)
            elif event.type == EventType.WINDOW_RESIZE:
                self.initializeLocationWidthAndHeight()
                self.updateConfigWindowSize()
            elif event.type == EventType.FOCUS_LOST:
                self.pausedByFocusLoss = True
            elif event.type == EventType.FOCUS_GAINED:
                self.pausedByFocusLoss = False
            elif event.type == EventType.MOUSE_DOWN:
                self.handleMouseDownEvent(event)
            elif event.type == EventType.MOUSE_UP:
                self.handleMouseUpEvent(event)
            elif event.type == EventType.MOUSE_MOTION:
                self.handleMouseMotionEvent()
            elif event.type == EventType.MOUSE_WHEEL:
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
                        _logger.debug("error moving entity to new room", error=str(e))
                    continue
                newRoom = self._loadOrGenerateRoom(
                    newRoomX, newRoomY, updateStats=False
                )

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

    def _updateGoals(self):
        # Re-evaluate goals; announce and persist any fresh completions.
        newlyCompleted = self.goals.evaluate()
        if not newlyCompleted:
            return
        if len(newlyCompleted) == 1:
            self.status.set("Goal complete: " + newlyCompleted[0].getDescription())
        else:
            self.status.set(str(len(newlyCompleted)) + " goals complete!")
        self.goalsJsonReaderWriter.save(self.goals.getCompletedIdentifiers())

    def _updateGameState(self):
        self._updateGoals()
        if self.pausedByFocusLoss:
            self.draw()
            self.renderer.present()
            if self.config.limitTps:
                self.clock.tick(self.config.ticksPerSecond)
            return

        self.currentRoom.tickExcrement(self.tickCounter.getTick(), self.config)
        self.currentRoom.tickCrops(self.tickCounter.getTick(), self.config)

        self.handleMouseOver()

        if self.deathRespawnTicksRemaining == 0:
            self.handlePlayerActions()
        self.removeEnergyAndCheckForPlayerDeath()
        if self.config.removeDeadEntities:
            self.checkForLivingEntityDeaths()
        self.status.checkForExpiration(self.tickCounter.getTick())
        self.draw()

        self.renderer.present()
        self.tickCounter.incrementTick()

        if self.config.limitTps:
            self.clock.tick(self.config.ticksPerSecond)

        if self.deathRespawnTicksRemaining > 0:
            self.deathRespawnTicksRemaining -= 1
            if self.deathRespawnTicksRemaining == 0:
                self.respawnPlayer()

        if self.config.showMiniMap:
            self.mapImageUpdater.updateIfCooldownOver()

    def run(self):
        while not self.changeScreen:
            self._processEvents()
            self._updateLivingEntities()
            self._updateGameState()

        if not os.path.exists(self.config.pathToSaveDirectory):
            os.makedirs(self.config.pathToSaveDirectory)

        self.returnCursorSlotToInventory()
        self.saveSynchronous()
        self.shutdown()

        self.changeScreen = False
        return self.nextScreen
