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
        self, locationWidth, locationHeight, offsetX, offsetY, clipWidth=None, clipHeight=None
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

    # Draws a location at a specified position.
    def drawLocation(self, location, xPos, yPos, width, height):
        # always draw background color first (needed for entities with transparent images)
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
            print(
                "Entity was not found in living entities list when trying to remove it. Entity ID: "
                + str(entity.getID())
            )
            return
        del self.livingEntities[entity.getID()]

    def removeLivingEntityById(self, entityId):
        if entityId not in self.livingEntities:
            print(
                "Entity was not found in living entities list when trying to remove it. Entity ID: "
                + str(entityId)
            )
            return
        del self.livingEntities[entityId]

    def getRandomAdjacentLocation(self, location):
        num = random.randrange(0, 4)
        if num == 0:
            return self.getGrid().getUp(location)
        elif num == 1:
            return self.getGrid().getRight(location)
        elif num == 2:
            return self.getGrid().getDown(location)
        elif num == 3:
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
            try:
                location = self.getGrid().getLocation(locationId)
            except:
                print(
                    "ERROR: Location not found when trying to move entity. Entity ID: "
                    + str(entity.getID())
                    + ", Location ID: "
                    + str(locationId)
                )
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

            # if entity needs energy
            if entity.needsEnergy():
                # search for food
                for targetEntityId in list(newLocation.getEntities().keys()):
                    if targetEntityId == entity.getID():
                        continue
                    targetEntity = newLocation.getEntity(targetEntityId)
                    if entity.canEat(targetEntity):
                        if (
                            isinstance(targetEntity, LivingEntity)
                            and targetEntity.getEnergy() > 0
                        ):
                            targetEntity.kill()
                            entity.addEnergy(targetEntity.getEnergy())
                        else:
                            self.removeEntity(targetEntity)
                            entity.addEnergy(10)
                        break
        return entitiesToMoveToNewRoom

    def reproduceLivingEntities(self, tick):
        entityLocationMappings = []
        minAgeToReproduce = 30 * 60 * 5  # 5 minutes (at 30/ticks per second)
        reproductionCooldown = minAgeToReproduce / 2  # 2.5 minutes
        for entityId in self.livingEntities:
            entity = self.livingEntities[entityId]
            if entity.getAge(tick) < minAgeToReproduce:
                continue
            locationId = entity.getLocationID()
            if locationId == -1:
                continue
            try:
                location = self.getGrid().getLocation(locationId)
            except:
                print(
                    "ERROR: Location not found when trying to reproduce entity. Entity ID: "
                    + str(entity.getID())
                    + ", Location ID: "
                    + str(locationId)
                )
                continue
            for targetEntityId in list(location.getEntities().keys()):
                targetEntity = location.getEntity(targetEntityId)
                # check if target entity is a living entity
                if isinstance(targetEntity, LivingEntity) == False:
                    continue
                # check if target entity is the entity itself
                if targetEntity.getID() == entity.getID():
                    continue
                # check if target entity is the same type as the entity
                if isinstance(targetEntity, type(entity)) == False:
                    continue
                # check if target entity has enough energy
                if targetEntity.needsEnergy():
                    continue
                # check if target entity is old enough to reproduce
                if targetEntity.getAge(tick) < minAgeToReproduce:
                    continue
                # check reproduction cooldown
                if (
                    entity.getTickLastReproduced() != None
                    and entity.getTickLastReproduced() + reproductionCooldown > tick
                ):
                    continue

                # reset image
                if isinstance(entity, Chicken):
                    entity.setImagePath("assets/images/chicken.png")
                elif isinstance(entity, Bear):
                    entity.setImagePath("assets/images/bear.png")

                # throw dice
                if random.randrange(1, 101) > 1:  # 1% chance
                    continue

                # decrease energy by half
                entity.removeEnergy(entity.getEnergy() / 2)
                targetEntity.removeEnergy(targetEntity.getEnergy() / 2)

                newEntity = None
                if isinstance(entity, Bear):
                    newEntity = Bear(tick)
                elif isinstance(entity, Chicken):
                    newEntity = Chicken(tick)

                if newEntity != None:
                    entityLocationMappings.append((newEntity, location))
                    entity.setTickLastReproduced(tick)
                    targetEntity.setTickLastReproduced(tick)
                    if isinstance(entity, Chicken):
                        entity.setImagePath(
                            "assets/images/chickenOnReproductionCooldown.png"
                        )
                        targetEntity.setImagePath(
                            "assets/images/chickenOnReproductionCooldown.png"
                        )
                    if isinstance(entity, Bear):
                        entity.setImagePath(
                            "assets/images/bearOnReproductionCooldown.png"
                        )
                        targetEntity.setImagePath(
                            "assets/images/bearOnReproductionCooldown.png"
                        )

                # set new entity's energy to 10% of average of parent's energy
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
            if locationId == -1:
                continue
            # 0.1% chance per tick
            if random.randrange(1, 1001) > 1:
                continue
            try:
                location = self.getGrid().getLocation(locationId)
            except Exception:
                continue
            excrement = Excrement(tick)
            self.addEntityToLocation(excrement, location)

        # Decay existing excrement into grass
        entitiesToReplace = []
        for locationId in self.getGrid().getLocations():
            location = self.getGrid().getLocation(locationId)
            for entityId in list(location.getEntities().keys()):
                entity = location.getEntity(entityId)
                if not isinstance(entity, Excrement):
                    continue
                if tick - entity.getTickCreated() < config.excrementDecayTicks:
                    continue
                # Don't place grass on solid entities, existing grass, or floors
                if self.locationContainsSolidEntity(location):
                    entitiesToReplace.append((location, entity, False))
                    continue
                if self.locationContainsEntityOfType(location, Grass):
                    entitiesToReplace.append((location, entity, False))
                    continue
                if self.locationContainsEntityOfType(
                    location, StoneFloor
                ) or self.locationContainsEntityOfType(location, WoodFloor):
                    entitiesToReplace.append((location, entity, False))
                    continue
                entitiesToReplace.append((location, entity, True))

        for location, excrement, shouldPlaceGrass in entitiesToReplace:
            location.removeEntity(excrement)
            self.removeEntity(excrement)
            if shouldPlaceGrass:
                grass = Grass()
                self.addEntityToLocation(grass, location)
