# @author Copilot
# @since April 20th, 2026
from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from player.player import Player
from stats.stats import Stats
from ui.status import Status
from world.roomPreloader import RoomPreloader
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


@component
class MovementService:
    """Handles player movement logic including collision detection and room transitions."""

    def __init__(
        self,
        config: Config,
        player: Player,
        stats: Stats,
        status: Status,
        tickCounter: TickCounter,
        roomPreloader: RoomPreloader,
    ):
        self.config = config
        self.player = player
        self.stats = stats
        self.status = status
        self.tickCounter = tickCounter
        self.roomPreloader = roomPreloader

    def _checkCooldown(self, tickToCheck, speed):
        ticksPerSecond = self.config.ticksPerSecond
        return tickToCheck + ticksPerSecond / speed < self.tickCounter.getTick()

    def checkPlayerMovementCooldown(self, tickToCheck):
        return self._checkCooldown(tickToCheck, self.player.getMovementSpeed())

    def checkPlayerGatherCooldown(self, tickToCheck):
        return self._checkCooldown(tickToCheck, self.player.getGatherSpeed())

    def checkPlayerPlaceCooldown(self, tickToCheck):
        return self._checkCooldown(tickToCheck, self.player.getPlaceSpeed())

    def getLocationDirection(self, direction, grid, location):
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

    def locationContainsSolidEntity(self, location):
        for entityId in list(location.getEntities().keys()):
            entity = location.getEntity(entityId)
            if entity.isSolid():
                return True
        return False

    def ifCorner(self, location):
        gridSize = self.config.gridSize
        return (
            (location.getX() == 0 and location.getY() == 0)
            or (location.getX() == gridSize - 1 and location.getY() == 0)
            or (location.getX() == 0 and location.getY() == gridSize - 1)
            or (location.getX() == gridSize - 1 and location.getY() == gridSize - 1)
        )

    def getCoordinatesForNewRoom(self, currentRoom, playerLocation):
        x = currentRoom.getX()
        y = currentRoom.getY()
        gridSize = self.config.gridSize

        if self.ifCorner(playerLocation):
            direction = self.player.getDirection()
            if playerLocation.getX() == 0 and playerLocation.getY() == 0:
                if direction == 0:
                    y -= 1
                elif direction == 1:
                    x -= 1
            elif playerLocation.getX() == gridSize - 1 and playerLocation.getY() == 0:
                if direction == 0:
                    y -= 1
                elif direction == 3:
                    x += 1
            elif playerLocation.getX() == 0 and playerLocation.getY() == gridSize - 1:
                if direction == 2:
                    y += 1
                elif direction == 1:
                    x -= 1
            elif (
                playerLocation.getX() == gridSize - 1
                and playerLocation.getY() == gridSize - 1
            ):
                if direction == 2:
                    y += 1
                elif direction == 3:
                    x += 1
        else:
            if playerLocation.getX() == gridSize - 1:
                x += 1
            elif playerLocation.getX() == 0:
                x -= 1
            elif playerLocation.getY() == gridSize - 1:
                y += 1
            elif playerLocation.getY() == 0:
                y -= 1
        return x, y

    def calculateTargetLocationForRoomTransition(self, currentRoom, playerLocation):
        gridSize = self.config.gridSize
        targetX = playerLocation.getX()
        targetY = playerLocation.getY()
        minCoord = 0
        maxCoord = gridSize - 1

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

        return currentRoom.getGrid().getLocationByCoordinates(targetX, targetY)

    def changeRooms(self, currentRoom, map, worldService, save_callback=None):
        """Handle a room transition for the player.

        Returns the new current room, or the unchanged currentRoom on failure.
        """
        playerLocation = map.getLocationOfEntity(self.player, currentRoom)
        x, y = self.getCoordinatesForNewRoom(currentRoom, playerLocation)

        if self.config.worldBorder != 0 and (
            abs(x) > self.config.worldBorder or abs(y) > self.config.worldBorder
        ):
            self.status.set("Reached world border")
            return currentRoom

        currentRoom.removeEntity(self.player)

        newRoom = worldService.loadOrGenerateRoom(x, y, map)

        targetLocation = self.calculateTargetLocationForRoomTransition(
            currentRoom, playerLocation
        )
        newRoom.addEntityToLocation(self.player, targetLocation)

        if save_callback is not None:
            save_callback()

        _logger.info(
            "room transition",
            roomX=newRoom.getX(),
            roomY=newRoom.getY(),
        )

        self.roomPreloader.preloadNearbyRooms(newRoom.getX(), newRoom.getY(), map)

        return newRoom

    def movePlayer(self, direction, currentRoom, map, worldService, save_callback=None):
        """Move the player in the given direction.

        Returns the (possibly new) current room.
        """
        from entity.living.bear import Bear
        from entity.food import Food

        if self.player.isCrouching():
            return currentRoom

        playerLocation = map.getLocationOfEntity(self.player, currentRoom)
        newLocation = self.getLocationDirection(
            direction, currentRoom.getGrid(), playerLocation
        )

        if newLocation == -1:
            newRoom = self.changeRooms(
                currentRoom, map, worldService, save_callback=save_callback
            )
            return newRoom

        if self.locationContainsSolidEntity(newLocation):
            if self.config.pushableStone:
                from entity.stone import Stone

                stoneEntity = None
                for entityId in list(newLocation.getEntities().keys()):
                    entity = newLocation.getEntity(entityId)
                    if isinstance(entity, Stone):
                        stoneEntity = entity
                        break
                if stoneEntity is not None:
                    pushDestination = self.getLocationDirection(
                        direction, currentRoom.getGrid(), newLocation
                    )
                    if pushDestination != -1 and not self.locationContainsSolidEntity(
                        pushDestination
                    ):
                        newLocation.removeEntity(stoneEntity)
                        pushDestination.addEntity(stoneEntity)
                        if self.locationContainsSolidEntity(newLocation):
                            return currentRoom
                    else:
                        return currentRoom
                else:
                    return currentRoom
            else:
                return currentRoom

        for entityId in list(newLocation.getEntities().keys()):
            entity = newLocation.getEntity(entityId)
            if isinstance(entity, Bear):
                self.player.kill()
                return currentRoom

        if self.player.needsEnergy():
            for entityId in list(newLocation.getEntities().keys()):
                entity = newLocation.getEntity(entityId)
                if self.player.canEat(entity):
                    newLocation.removeEntity(entity)
                    self.player.addEnergy(entity.getEnergy())
                    self.stats.incrementFoodEaten()
                    self.status.set("Ate " + entity.getName())
                    self.stats.incrementScore()

        playerLocation.removeEntity(self.player)
        newLocation.addEntity(self.player)

        self.player.removeEnergy(self.config.playerMovementEnergyCost)
        self.player.setTickLastMoved(self.tickCounter.getTick())

        return currentRoom
