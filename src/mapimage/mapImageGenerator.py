# Combines all room images into a single map image

import os
from PIL import Image

from gameLogging.logger import getLogger

_logger = getLogger(__name__)


# @author Daniel McCoy Stephenson
# @since February 2nd, 2023
class MapImageGenerator:
    def __init__(self, config):
        self.config = config

        self.numRoomsInEachDirection = 5
        self.roomSizeInPixels = 100
        self.mapImageSizeInPixels = (
            self.numRoomsInEachDirection * 2 + 1
        ) * self.roomSizeInPixels

        os.makedirs(self.config.pathToSaveDirectory, exist_ok=True)
        self.mapImage = self._loadOrCreateMapImage()

    # The save directory is chosen at runtime (saveSelectionScreen.selectSave
    # reassigns config.pathToSaveDirectory), but this generator is constructed
    # at startup. Resolve both paths lazily from the config every time so the
    # map image always lands in the active save rather than the startup default.
    def getRoomImagesDirectoryPath(self):
        return self.config.pathToSaveDirectory + "/roompngs"

    def getMapImagePath(self):
        return self.config.pathToSaveDirectory + "/mapImage.png"

    def _loadOrCreateMapImage(self):
        if self.mapImageExists():
            return self.getExistingMapImage()
        return self.createNewMapImage()

    def generate(self):
        # Reload the canvas from the current save directory each call so a
        # save-directory change after construction is honored.
        os.makedirs(self.config.pathToSaveDirectory, exist_ok=True)
        self.mapImage = self._loadOrCreateMapImage()
        roomImages = self.getRoomImages()
        self.pasteRoomImagesAtCorrectCoordinates(roomImages)
        return self.mapImage

    def clearRoomImages(self):
        roomImagesDirectoryPath = self.getRoomImagesDirectoryPath()
        if not os.path.isdir(roomImagesDirectoryPath):
            return
        for file in os.listdir(roomImagesDirectoryPath):
            os.remove(roomImagesDirectoryPath + "/" + file)

    def mapImageExists(self):
        return os.path.exists(self.getMapImagePath())

    def getExistingMapImage(self):
        mapImagePath = self.getMapImagePath()
        _logger.debug("loading existing map image", path=mapImagePath)
        return Image.open(mapImagePath)

    def createNewMapImage(self):
        _logger.debug("creating new map image")
        return Image.new(
            "RGB", (self.mapImageSizeInPixels, self.mapImageSizeInPixels), "white"
        )

    def getRoomImages(self):
        roomImagesDirectoryPath = self.getRoomImagesDirectoryPath()
        if not os.path.isdir(roomImagesDirectoryPath):
            return []
        return os.listdir(roomImagesDirectoryPath)

    def pasteRoomImagesAtCorrectCoordinates(self, roomImages):
        numPasted = 0
        numOutOfBounds = 0
        roomImagesDirectoryPath = self.getRoomImagesDirectoryPath()

        for roomImageFilename in roomImages:
            with Image.open(roomImagesDirectoryPath + "/" + roomImageFilename) as image:
                roomSize = 100
                resizedImage = image.resize((roomSize, roomSize))

            roomCoordinates = roomImageFilename.split(".")[0].split("_")
            roomX = int(roomCoordinates[0])
            roomY = int(roomCoordinates[1])

            picX = (
                int(self.mapImageSizeInPixels / 2)
                + roomX * roomSize
                - int(roomSize / 2)
            )
            picY = (
                int(self.mapImageSizeInPixels / 2)
                + roomY * roomSize
                - int(roomSize / 2)
            )
            if (
                picX >= 0
                and picY >= 0
                and picX < self.mapImageSizeInPixels
                and picY < self.mapImageSizeInPixels
            ):
                self.mapImage.paste(resizedImage, (picX, picY))
                numPasted += 1
            else:
                numOutOfBounds += 1

        _logger.debug(
            "map image paste complete",
            imagesPasted=numPasted,
            imagesOutOfBounds=numOutOfBounds,
            percentUpdated=int(
                numPasted / (self.numRoomsInEachDirection * 2 + 1) ** 2 * 100
            ),
        )
