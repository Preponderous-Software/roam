import pygame
from lib.pyenvlib.entity import Entity


# @author Daniel McCoy Stephenson
# @since August 5th, 2022
class DrawableEntity(Entity):
    _imageCache = {}

    def __init__(self, name, imagePath):
        Entity.__init__(self, name)
        self.imagePath = imagePath

    def getImage(self):
        if self.imagePath not in DrawableEntity._imageCache:
            DrawableEntity._imageCache[self.imagePath] = pygame.image.load(
                self.imagePath
            )
        return DrawableEntity._imageCache[self.imagePath]

    def getImagePath(self):
        return self.imagePath

    def setImagePath(self, imagePath):
        self.imagePath = imagePath
