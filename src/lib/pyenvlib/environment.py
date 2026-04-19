# Copyright (c) 2022 Preponderous Software
# MIT License
import datetime
import uuid
from lib.pyenvlib.entity import Entity
from lib.pyenvlib.grid import Grid

# @author Daniel McCoy Stephenson
# @since July 1st, 2022


# Represents a virtual environment with an underlying 2D grid of locations that can contain entities.
class Environment(object):
    def __init__(self, name, size):
        self.id = uuid.uuid4()
        self.name = name
        self.grid = Grid(size, size)
        self.creationDate = datetime.datetime.now()

    # Returns the ID of this environment.
    def getID(self):
        return self.id

    # Returns the name of this environment.
    def getName(self):
        return self.name

    # Returns the creation timestamp for this environment.
    def getCreationDate(self):
        return self.creationDate

    # Returns this environment's grid.
    def getGrid(self):
        return self.grid

    # Sets the ID of this environment.
    def setID(self, id):
        self.id = id

    # Sets the name of this environment.
    def setName(self, name):
        self.name = name

    # Sets this environment's grid.
    def setGrid(self, grid):
        self.grid = grid

    # Adds an entity to the underlying grid.
    def addEntity(self, entity: Entity):
        entity.setEnvironmentID(self.getID())
        self.grid.addEntity(entity)

    # Adds an entity to a particular location in the underlying grid of this environment.
    def addEntityToLocation(self, entity: Entity, location):
        entity.setEnvironmentID(self.getID())
        self.grid.addEntityToLocation(entity, location)

    # Removes an entity from the underlying grid.
    def removeEntity(self, entity: Entity):
        self.grid.removeEntity(entity)

    # Checks if an entity is present anywhere in the underlying grid.
    def isEntityPresent(self, entity: Entity):
        return self.grid.isEntityPresent(entity)

    # Returns the number of entities in this environment.
    def getNumEntities(self):
        return self.getGrid().getNumEntities()

    # Prints information about this environment to the console.
    def printInfo(self):
        print("--------------")
        print(self.name)
        print("--------------")
        print("Num entities: ", self.getNumEntities())
        print("Num locations: ", self.getGrid().getSize())
        print("Creation Date: ", self.getCreationDate())
        print("ID: ", self.getID())
        print("Grid ID: ", self.getGrid().getID())
        print("\n")

    # Returns the entity in this environment with the given ID.
    def getEntity(self, id):
        return self.grid.getEntity(id)
