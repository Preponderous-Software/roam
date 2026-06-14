import datetime
import os

import pygame

from config.config import Config


def getScreenshotsFolder():
    # Write screenshots to the writable user-data directory so captures work
    # even when the game is installed to a read-only location (e.g. Program
    # Files). From source this is the repository root, as before.
    return os.path.join(Config.getUserDataDirectory(), "screenshots")


def captureScreen(gameDisplay, name, pos, size):
    image = pygame.Surface(size)
    image.blit(gameDisplay, (0, 0), (pos, size))
    pygame.image.save(image, name)


def takeScreenshot(gameDisplay):
    screenshotsFolder = getScreenshotsFolder()
    if not os.path.exists(screenshotsFolder):
        os.makedirs(screenshotsFolder)
    displayWidth, displayHeight = gameDisplay.get_size()
    timestamp = str(datetime.datetime.now()).replace(" ", "-").replace(":", ".")
    filename = os.path.join(screenshotsFolder, "screenshot-" + timestamp + ".png")
    captureScreen(gameDisplay, filename, (0, 0), (displayWidth, displayHeight))
