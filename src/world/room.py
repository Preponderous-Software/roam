import random

import pygame
from entity.excrement import Excrement
from entity.grass import Grass
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from entity.stoneFloor import StoneFloor
from entity.woodFloor import WoodFloor
from lib.pyenvlib.environment import Environment
from lib.graphik.src.graphik import Graphik
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Room(Environment):
    _scaledImageCache = {}

    def __init__(self, name, gridSize, backgroundColor, x, y, graphik: Graphik):
        Environment.__init__(self, name, gridSize)
        self.backgroundColor = backgroundColor
        self.x = x
        self.y = y
        self.graphik = graphik
        self.livingEntities = dict()

    def getBackgroundColor(self):
        return self.backgroundColor

    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def draw(self, locationWidth, locationHeight):
        for locationId in self.grid.getLocations():
            location = self.grid.getLocation(locationId)
            self.drawLocation(
                location,
                location.getX() * locationWidth - 1,
                location.getY() * locationHeight - 1,
                locationWidth + 2,
                locationHeight + 2,
            )

    def drawWithOffset(
        self,
        locationWidth,
        locationHeight,
        offsetX,
        offsetY,
        clipWidth=None,
        clipHeight=None,
    ):
        locWidth = locationWidth + 2
        locHeight = locationHeight + 2
        for locationId in self.grid.getLocations():
            location = self.grid.getLocation(locationId)
            xPos = offsetX + location.getX() * locationWidth - 1
            yPos = offsetY + location.getY() * locationHeight - 1
            if clipWidth is not None:
                if xPos + locWidth < 0 or xPos > clipWidth:
                    continue
            if clipHeight is not None:
                if yPos + locHeight < 0 or yPos > clipHeight:
                    continue
            self.drawLocation(location, xPos, yPos, locWidth, locHeight)

    def drawLocation(self, location, xPos, yPos, width, height):
        # transparent images require the background color to be drawn first
        self.graphik.drawRectangle(xPos, yPos, width, height, self.backgroundColor)
        if location.getNumEntities() > 0:
            # draw texture
            topEntityId = list(location.getEntities().keys())[-1]
            topEntity = location.getEntities()[topEntityId]
            imagePath = topEntity.getImagePath()
            scaledWidth = int(width)
            scaledHeight = int(height)
            cacheKey = (imagePath, scaledWidth, scaledHeight)
            if cacheKey not in Room._scaledImageCache:
                image = topEntity.getImage()
                Room._scaledImageCache[cacheKey] = pygame.transform.scale(
                    image, (scaledWidth, scaledHeight)
                )
            self.graphik.gameDisplay.blit(
                Room._scaledImageCache[cacheKey], (xPos, yPos)
            )

    def addLivingEntity(self, entity):
        self.livingEntities[entity.getID()] = entity

    def removeLivingEntity(self, entity):
        if entity.getID() not in self.livingEntities:
            _logger.warning(
                "entity not found in living entities list when removing",
                entityId=str(entity.getID()),
            )
            return
        del self.livingEntities[entity.getID()]

    def removeLivingEntityById(self, entityId):
        if entityId not in self.livingEntities:
            _logger.warning(
                "entity not found in living entities list when removing by id",
                entityId=str(entityId),
            )
            return
        del self.livingEntities[entityId]

    def getRandomAdjacentLocation(self, location):
        directionIndex = random.randrange(0, 4)
        if directionIndex == 0:
            return self.getGrid().getUp(location)
        elif directionIndex == 1:
            return self.getGrid().getRight(location)
        elif directionIndex == 2:
            return self.getGrid().getDown(location)
        elif directionIndex == 3:
            return self.getGrid().getLeft(location)

    def checkEntityMovementCooldown(self, tickToCheck, entity):
        ticksPerSecond = self.config.ticksPerSecond
        return tickToCheck + ticksPerSecond / entity.getSpeed() < self.tick

    def moveLivingEntities(self, tick) -> list:
        entitiesToMoveToNewRoom = []
        for entityId in self.livingEntities:
            # 1% chance to skip
            if random.randrange(1, 101) > 1:
                continue

            entity = self.livingEntities[entityId]
            locationId = entity.getLocationID()
            if locationId == -1:
                continue
            location = self._getLocationOrNone(
                locationId, "move entity", entity.getID()
            )
            if location is None:
                continue
            newLocation = self.getRandomAdjacentLocation(location)

            if newLocation == -1:
                entitiesToMoveToNewRoom.append(entity)
                continue

            if self.locationContainsSolidEntity(newLocation):
                continue

            # move entity
            location.removeEntity(entity)
            newLocation.addEntity(entity)
            entity.setLocationID(newLocation.getID())

            # decrease energy
            entity.removeEnergy(1)

            self._feedLivingEntityIfNeeded(entity, newLocation)
        return entitiesToMoveToNewRoom

    def reproduceLivingEntities(self, tick):
        entityLocationMappings = []
        minAgeToReproduce = 30 * 60 * 5  # 5 minutes (at 30/ticks per second)
        reproductionCooldown = minAgeToReproduce / 2  # 2.5 minutes
        for entityId in self.livingEntities:
            entity = self.livingEntities[entityId]
            locationId = entity.getLocationID()
            if not self._isEntityReadyToReproduce(
                entity, tick, minAgeToReproduce, locationId
            ):
                continue
            location = self._getLocationOrNone(
                locationId, "reproduce entity", entity.getID()
            )
            if location is None:
                continue
            for targetEntityId in list(location.getEntities().keys()):
                targetEntity = location.getEntity(targetEntityId)
                if not self._isValidReproductionTarget(
                    entity, targetEntity, tick, minAgeToReproduce
                ):
                    continue
                if (
                    entity.getTickLastReproduced() is not None
                    and entity.getTickLastReproduced() + reproductionCooldown > tick
                ):
                    continue

                self._setDefaultEntityImage(entity)

                if random.randrange(1, 101) > 1:  # 1% chance
                    continue

                entity.removeEnergy(entity.getEnergy() / 2)
                targetEntity.removeEnergy(targetEntity.getEnergy() / 2)

                newEntity = self._createOffspring(entity, tick)

                if newEntity is None:
                    continue

                entityLocationMappings.append((newEntity, location))
                entity.setTickLastReproduced(tick)
                targetEntity.setTickLastReproduced(tick)
                self._setReproductionCooldownImage(entity)
                self._setReproductionCooldownImage(targetEntity)
                newEntity.setEnergy(
                    (entity.getEnergy() + targetEntity.getEnergy()) / 2 * 0.1
                )

        for entityLocationMapping in entityLocationMappings:
            entity = entityLocationMapping[0]
            location = entityLocationMapping[1]
            self.addEntityToLocation(entity, location)
            self.addLivingEntity(entity)

    def locationContainsSolidEntity(self, location):
        for entityId in list(location.getEntities().keys()):
            entity = location.getEntity(entityId)
            if entity.isSolid():
                return True
        return False

    def getLivingEntities(self):
        return self.livingEntities

    def setLivingEntities(self, livingEntities):
        self.livingEntities = livingEntities

    def locationContainsEntityOfType(self, location, entityType):
        for entityId in list(location.getEntities().keys()):
            entity = location.getEntity(entityId)
            if isinstance(entity, entityType):
                return True
        return False

    def tickExcrement(self, tick, config):
        # Living entities have a small chance to produce excrement
        for entityId in self.livingEntities:
            entity = self.livingEntities[entityId]
            locationId = entity.getLocationID()
            if str(locationId) == "-1":
                continue
            # 0.1% chance per tick
            if random.randrange(1, 1001) > 1:
                continue
            try:
                location = self.getGrid().getLocation(locationId)
            except KeyError:
                continue
            excrement = Excrement(tick)
            self.addEntityToLocation(excrement, location)

        # Decay existing excrement into grass
        entitiesToReplace = []
        for locationId in self.getGrid().getLocations():
            location = self.getGrid().getLocation(locationId)
            expiredExcrement = []
            for entityId in list(location.getEntities().keys()):
                entity = location.getEntity(entityId)
                if not isinstance(entity, Excrement):
                    continue
                if tick - entity.getTickCreated() < config.excrementDecayTicks:
                    continue
                expiredExcrement.append(entity)

            if len(expiredExcrement) == 0:
                continue

            # Don't place grass on solid entities, existing grass, or floors
            shouldPlaceGrass = True
            if self.locationContainsSolidEntity(location):
                shouldPlaceGrass = False
            elif self.locationContainsEntityOfType(location, Grass):
                shouldPlaceGrass = False
            elif self.locationContainsEntityOfType(
                location, StoneFloor
            ) or self.locationContainsEntityOfType(location, WoodFloor):
                shouldPlaceGrass = False

            entitiesToReplace.append((location, expiredExcrement, shouldPlaceGrass))

        for location, excrementList, shouldPlaceGrass in entitiesToReplace:
            for excrement in excrementList:
                location.removeEntity(excrement)
            if shouldPlaceGrass:
                grass = Grass()
                self.addEntityToLocation(grass, location)

    def _getLocationOrNone(self, locationId, actionName, entityId):
        try:
            return self.getGrid().getLocation(locationId)
        except KeyError:
            _logger.error(
                "location not found",
                action=actionName,
                entityId=str(entityId),
                locationId=str(locationId),
            )
            return None

    def _feedLivingEntityIfNeeded(self, entity, location):
        if not entity.needsEnergy():
            return

        for targetEntityId in list(location.getEntities().keys()):
            if targetEntityId == entity.getID():
                continue
            targetEntity = location.getEntity(targetEntityId)
            if not entity.canEat(targetEntity):
                continue

            if isinstance(targetEntity, LivingEntity) and targetEntity.getEnergy() > 0:
                targetEntity.kill()
                entity.addEnergy(targetEntity.getEnergy())
            else:
                self.removeEntity(targetEntity)
                entity.addEnergy(10)
            return

    def _isEntityReadyToReproduce(self, entity, tick, minAgeToReproduce, locationId):
        return entity.getAge(tick) >= minAgeToReproduce and locationId != -1

    def _isValidReproductionTarget(self, entity, targetEntity, tick, minAgeToReproduce):
        if not isinstance(targetEntity, LivingEntity):
            return False
        if targetEntity.getID() == entity.getID():
            return False
        if not isinstance(targetEntity, type(entity)):
            return False
        if targetEntity.needsEnergy():
            return False
        if targetEntity.getAge(tick) < minAgeToReproduce:
            return False
        return True

    def _setDefaultEntityImage(self, entity):
        if isinstance(entity, Chicken):
            entity.setImagePath("assets/images/chicken.png")
        elif isinstance(entity, Bear):
            entity.setImagePath("assets/images/bear.png")

    def _setReproductionCooldownImage(self, entity):
        if isinstance(entity, Chicken):
            entity.setImagePath("assets/images/chickenOnReproductionCooldown.png")
        elif isinstance(entity, Bear):
            entity.setImagePath("assets/images/bearOnReproductionCooldown.png")

    def _createOffspring(self, entity, tick):
        if isinstance(entity, Bear):
            return Bear(tick)
        if isinstance(entity, Chicken):
            return Chicken(tick)
        return None
