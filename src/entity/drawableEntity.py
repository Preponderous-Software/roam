from lib.pyenvlib.entity import Entity


# @author Daniel McCoy Stephenson
# @since August 5th, 2022
class DrawableEntity(Entity):
    def __init__(self, name, imagePath, solid=False):
        Entity.__init__(self, name)
        self.imagePath = imagePath
        self.solid = solid

    def isSolid(self):
        return self.solid

    def getImagePath(self):
        return self.imagePath

    def setImagePath(self, imagePath):
        self.imagePath = imagePath
