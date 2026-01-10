import random

import pygame
from entity.excrement import Excrement
from entity.grass import Grass
from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.livingEntity import LivingEntity
from lib.pyenvlib.environment import Environment
from lib.graphik.src.graphik import Graphik


# @author Daniel McCoy Stephenson
# @since August 8th, 2022
class Room(Environment):
    # Excrement aging threshold: 10 minutes at 30 ticks per second
    EXCREMENT_AGE_THRESHOLD_TICKS = 30 * 60 * 10  # 18000 ticks
    
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

    # Draws a location at a specified position.
    def drawLocation(self, location, xPos, yPos, width, height):
        if location.getNumEntities() > 0:
            # draw texture
            topEntityId = list(location.getEntities().keys())[-1]
            topEntity = location.getEntities()[topEntityId]
            image = topEntity.getImage()
            scaledImage = pygame.transform.scale(image, (width, height))
            self.graphik.gameDisplay.blit(scaledImage, (xPos, yPos))
        else:
            # draw background color
            self.graphik.drawRectangle(xPos, yPos, width, height, self.backgroundColor)

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

            # check if entity should spawn excrement
            if entity.shouldSpawnExcrement(tick):
                # spawn excrement at the old location
                excrement = Excrement(tick)
                self.addEntityToLocation(excrement, location)
                entity.setTickLastExcrement(tick)

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

    def ageExcrement(self, tick):
        """Convert excrement to grass after it ages for 10 minutes (at 30 ticks per second)"""
        excrementToConvert = []
        for locationId in self.grid.getLocations():
            location = self.grid.getLocation(locationId)
            for entityId in list(location.getEntities().keys()):
                entity = location.getEntity(entityId)
                if isinstance(entity, Excrement):
                    if entity.getAge(tick) >= self.EXCREMENT_AGE_THRESHOLD_TICKS:
                        excrementToConvert.append((entity, location))
        
        # Convert excrement to grass
        for excrement, location in excrementToConvert:
            self.removeEntity(excrement)
            grass = Grass()
            self.addEntityToLocation(grass, location)
