from appContainer import component
from config.config import Config
from mapimage.mapImageGenerator import MapImageGenerator
from world.tickCounter import TickCounter


# @author Daniel McCoy Stephenson
# @since February 2nd, 2023
@component
class MapImageUpdater:
    def __init__(self, tickCounter: TickCounter, config: Config):
        self.tickCounter = tickCounter
        self.config = config
        self.mapImageGenerator = MapImageGenerator(self.config)
        self.tickLastUpdated = self.tickCounter.getTick()
        self.updateCooldownInTicks = 300

    def updateIfCooldownOver(self):
        if (
            self.tickCounter.getTick() - self.tickLastUpdated
            > self.updateCooldownInTicks
        ):
            self.updateMapImage()

    def updateMapImage(self):
        image = self.mapImageGenerator.generate()
        image.save(self.mapImageGenerator.mapImagePath)
        self.mapImageGenerator.clearRoomImages()
        self.tickLastUpdated = self.tickCounter.getTick()
