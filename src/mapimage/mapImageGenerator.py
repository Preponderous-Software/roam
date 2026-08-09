# Combines all room images into a single map image

import os
from PIL import Image

from gameLogging.logger import getLogger
from mapimage.mapImagePaths import (
    getMapImageFilename,
    getRoomImageFilename,
    parseRoomImageFilename,
)

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

    def getMapImagePath(self, z=0):
        return self.config.pathToSaveDirectory + "/" + getMapImageFilename(z)

    def getRoomImagePath(self, x, y, z=0):
        return self.getRoomImagesDirectoryPath() + "/" + getRoomImageFilename(x, y, z)

    def _loadOrCreateMapImage(self, z=0):
        if self.mapImageExists(z):
            return self.getExistingMapImage(z)
        return self.createNewMapImage()

    def generate(self, z=0):
        # Reload the canvas from the current save directory each call so a
        # save-directory change after construction is honored.
        os.makedirs(self.config.pathToSaveDirectory, exist_ok=True)
        self.mapImage = self._loadOrCreateMapImage(z)
        roomImages = self.getRoomImages(z)
        self.pasteRoomImagesAtCorrectCoordinates(roomImages)
        return self.mapImage

    def clearRoomImages(self, z=None):
        """Delete captured room images. With ``z`` given, only that level's
        captures are removed, so stitching one level never discards the
        captures another level is still waiting on."""
        roomImagesDirectoryPath = self.getRoomImagesDirectoryPath()
        if not os.path.isdir(roomImagesDirectoryPath):
            return
        for file in os.listdir(roomImagesDirectoryPath):
            if z is not None:
                coordinates = parseRoomImageFilename(file)
                if coordinates is None or coordinates[2] != z:
                    continue
            os.remove(roomImagesDirectoryPath + "/" + file)

    def mapImageExists(self, z=0):
        return os.path.exists(self.getMapImagePath(z))

    def getExistingMapImage(self, z=0):
        mapImagePath = self.getMapImagePath(z)
        _logger.debug("loading existing map image", path=mapImagePath)
        try:
            with Image.open(mapImagePath) as mapImage:
                mapImage.load()
                return mapImage.copy()
        except Exception as error:
            _logger.warning(
                "map image unreadable, recreating",
                path=mapImagePath,
                error=str(error),
            )
            return self.createNewMapImage()

    def createNewMapImage(self):
        _logger.debug("creating new map image")
        return Image.new(
            "RGB", (self.mapImageSizeInPixels, self.mapImageSizeInPixels), "white"
        )

    def getRoomImages(self, z=0):
        """Return the captured room image filenames belonging to level ``z``."""
        roomImages = []
        for file in self._listRoomImageFiles():
            coordinates = parseRoomImageFilename(file)
            if coordinates is not None and coordinates[2] == z:
                roomImages.append(file)
        return roomImages

    def getLevelsWithRoomImages(self):
        """Return the sorted ``z`` levels that currently have captured room
        images waiting to be stitched."""
        levels = set()
        for file in self._listRoomImageFiles():
            coordinates = parseRoomImageFilename(file)
            if coordinates is not None:
                levels.add(coordinates[2])
        return sorted(levels)

    def _listRoomImageFiles(self):
        roomImagesDirectoryPath = self.getRoomImagesDirectoryPath()
        if not os.path.isdir(roomImagesDirectoryPath):
            return []
        return os.listdir(roomImagesDirectoryPath)

    def pasteRoomImagesAtCorrectCoordinates(self, roomImages):
        numPasted = 0
        numOutOfBounds = 0
        roomImagesDirectoryPath = self.getRoomImagesDirectoryPath()

        for roomImageFilename in roomImages:
            roomCoordinates = parseRoomImageFilename(roomImageFilename)
            if roomCoordinates is None:
                continue

            with Image.open(roomImagesDirectoryPath + "/" + roomImageFilename) as image:
                roomSize = 100
                resizedImage = image.resize((roomSize, roomSize))

            roomX, roomY = roomCoordinates[0], roomCoordinates[1]

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
