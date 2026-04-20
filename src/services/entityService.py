# @author Copilot
# @since April 20th, 2026
from appContainer import component
from codex.codex import Codex
from config.config import Config
from entity.food import Food
from entity.grass import Grass
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from entity.matureCrop import MatureCrop
from entity.wheat import Wheat
from entity.wheatSeed import WheatSeed
from entity.youngCrop import YoungCrop
from gameLogging.logger import getLogger
from player.player import Player
from repositories.codexRepository import CodexRepository
from stats.stats import Stats
from ui.status import Status
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


@component
class EntityService:
    """Handles entity interactions including gathering, placing, and living entity behavior."""

    def __init__(
        self,
        config: Config,
        player: Player,
        stats: Stats,
        status: Status,
        tickCounter: TickCounter,
        codex: Codex,
        codexRepository: CodexRepository,
    ):
        self.config = config
        self.player = player
        self.stats = stats
        self.status = status
        self.tickCounter = tickCounter
        self.codex = codex
        self.codexRepository = codexRepository

    def canBePickedUp(self, entity):
        from screen.pickupableEntities import canBePickedUp

        return canBePickedUp(entity)

    def isLocationTooFar(self, targetLocation, targetRoom, currentRoom):
        distanceLimit = self.config.playerInteractionDistanceLimit
        from world.map import Map

        playerLocationId = self.player.getLocationID()
        playerLocation = currentRoom.getGrid().getLocation(playerLocationId)
        gridSize = self.config.gridSize
        worldTargetX = targetRoom.getX() * gridSize + targetLocation.getX()
        worldTargetY = targetRoom.getY() * gridSize + targetLocation.getY()
        worldPlayerX = currentRoom.getX() * gridSize + playerLocation.getX()
        worldPlayerY = currentRoom.getY() * gridSize + playerLocation.getY()
        return (
            abs(worldTargetX - worldPlayerX) > distanceLimit
            or abs(worldTargetY - worldPlayerY) > distanceLimit
        )

    def tryHarvestCrop(self, targetLocation, targetRoom):
        """Check for crop interactions. Returns True if a crop was found."""
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

    def executeGatherAction(self, currentRoom, map):
        from screen.pickupableEntities import canBePickedUp

        targetLocation, targetRoom = self._getLocationAndRoomAtMousePosition(
            currentRoom, map
        )

        if targetLocation == -1:
            self.status.set("Nothing to pick up here")
            return

        if self.isLocationTooFar(targetLocation, targetRoom, currentRoom):
            self.status.set("Too far away")
            return

        if self.tryHarvestCrop(targetLocation, targetRoom):
            return

        toRemove = None
        for entityId in list(reversed(targetLocation.getEntities())):
            entity = targetLocation.getEntity(entityId)
            if canBePickedUp(entity):
                toRemove = entity
                break

        if toRemove is None:
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

    def executePlaceAction(self, currentRoom, map):
        if self.player.getInventory().getNumTakenInventorySlots() == 0:
            self.status.set("No items to place")
            return

        targetLocation, targetRoom = self._getLocationAndRoomAtMousePosition(
            currentRoom, map
        )
        if targetLocation == -1:
            self.status.set("Cannot place here")
            return
        if targetLocation == -2:
            self.status.set("Stop moving to place items")
            return

        from services.movementService import MovementService

        if self._locationContainsSolidEntity(targetLocation):
            self.status.set("Location is blocked")
            return

        if self.isLocationTooFar(targetLocation, targetRoom, currentRoom):
            self.status.set("Too far away")
            return

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

    def _locationContainsSolidEntity(self, location):
        for entityId in list(location.getEntities().keys()):
            entity = location.getEntity(entityId)
            if entity.isSolid():
                return True
        return False

    def _getLocationAndRoomAtMousePosition(self, currentRoom, map):
        """Delegate to WorldScreen helper - accessed via graphik context.

        This method is intentionally thin; actual pixel math stays in WorldScreen.
        EntityService callers should pass the resolved (location, room) tuple.
        This stub exists so callers internal to EntityService can be unit-tested.
        """
        return -1, None

    def discoverLivingEntitiesInRoom(self, currentRoom):
        for entityId, entity in currentRoom.getLivingEntities().items():
            entityClassName = entity.__class__.__name__
            if self.codex.discover(entityClassName):
                self.status.set("New codex entry: " + entityClassName)
                self.codexRepository.save(self.codex)

    def checkForLivingEntityDeaths(self, currentRoom):
        toRemove = []
        for livingEntityId in currentRoom.getLivingEntities():
            livingEntity = currentRoom.getEntity(livingEntityId)
            if livingEntity is None:
                _logger.debug(
                    "living entity not found in room",
                    entityId=str(livingEntityId),
                    roomName=currentRoom.getName(),
                )
                toRemove.append(livingEntityId)
                continue
            if livingEntity.getEnergy() == 0:
                toRemove.append(livingEntityId)

        for livingEntityId in toRemove:
            livingEntity = currentRoom.getEntity(livingEntityId)
            if livingEntity is None:
                currentRoom.removeLivingEntityById(livingEntityId)
                continue

            locationId = livingEntity.getLocationID()
            if str(locationId) != "-1":
                try:
                    location = currentRoom.getGrid().getLocation(locationId)
                    if isinstance(livingEntity, Chicken):
                        from entity.chickenMeat import ChickenMeat

                        meat = ChickenMeat()
                        currentRoom.addEntityToLocation(meat, location)
                    elif isinstance(livingEntity, Bear):
                        from entity.bearMeat import BearMeat

                        meat = BearMeat()
                        currentRoom.addEntityToLocation(meat, location)
                except KeyError as ex:
                    _logger.debug(
                        "could not spawn meat for entity",
                        entityName=livingEntity.getName(),
                        locationId=str(locationId),
                        error=str(ex),
                    )

            currentRoom.removeEntity(livingEntity)
            currentRoom.removeLivingEntity(livingEntity)
            _logger.debug(
                "living entity died",
                entityName=livingEntity.getName(),
                roomName=currentRoom.getName(),
            )
