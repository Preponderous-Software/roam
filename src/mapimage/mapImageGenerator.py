# Combines all room images into a single map image

import os
from PIL import Image


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

        self.roomImagesDirectoryPath = self.config.pathToSaveDirectory + "/roompngs"
        self.mapImagePath = self.config.pathToSaveDirectory + "/mapImage.png"

        if self.mapImageExists():
            self.mapImage = self.getExistingMapImage()
        else:
            self.mapImage = self.createNewMapImage()

    def generate(self):
        roomImages = self.getRoomImages()
        self.pasteRoomImagesAtCorrectCoordinates(roomImages)
        return self.mapImage

    def clearRoomImages(self):
        for file in os.listdir(self.roomImagesDirectoryPath):
            os.remove(self.roomImagesDirectoryPath + "/" + file)

    def mapImageExists(self):
        return os.path.exists(self.mapImagePath)

    def getExistingMapImage(self):
        if self.config.debug:
            print("Loading existing map image")
        return Image.open(self.mapImagePath)

    def createNewMapImage(self):
        if self.config.debug:
            print("Creating new map image")
        return Image.new(
            "RGB", (self.mapImageSizeInPixels, self.mapImageSizeInPixels), "white"
        )

    def getRoomImages(self):
        return os.listdir(self.roomImagesDirectoryPath)

    def pasteRoomImagesAtCorrectCoordinates(self, roomImages):
        numPasted = 0
        numOutOfBounds = 0

        for roomImageFilename in roomImages:
            image = Image.open(self.roomImagesDirectoryPath + "/" + roomImageFilename)

            roomSize = 100
            image = image.resize((roomSize, roomSize))

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
                self.mapImage.paste(image, (picX, picY))
                numPasted += 1
            else:
                numOutOfBounds += 1

        if self.config.debug:
            print("Images pasted: " + str(numPasted))
            print("Images out of bounds: " + str(numOutOfBounds))
            print(
                "Percent of map updated: "
                + str(
                    int(numPasted / (self.numRoomsInEachDirection * 2 + 1) ** 2 * 100)
                )
                + "%"
            )
