import pygame
from lib.pyenvlib.entity import Entity


# @author Daniel McCoy Stephenson
# @since August 5th, 2022
class DrawableEntity(Entity):
    def __init__(self, name, imagePath):
        Entity.__init__(self, name)
        self.imagePath = imagePath

    def getImage(self):
        return pygame.image.load(self.imagePath)

    def getImagePath(self):
        return self.imagePath

    def setImagePath(self, imagePath):
        self.imagePath = imagePath

    def isPushable(self):
        return False
