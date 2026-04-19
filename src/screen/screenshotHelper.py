import datetime
import os

import pygame

SCREENSHOTS_FOLDER = "screenshots"


def captureScreen(gameDisplay, name, pos, size):
    image = pygame.Surface(size)
    image.blit(gameDisplay, (0, 0), (pos, size))
    pygame.image.save(image, name)


def takeScreenshot(gameDisplay):
    if not os.path.exists(SCREENSHOTS_FOLDER):
        os.makedirs(SCREENSHOTS_FOLDER)
    displayWidth, displayHeight = gameDisplay.get_size()
    timestamp = str(datetime.datetime.now()).replace(" ", "-").replace(":", ".")
    filename = SCREENSHOTS_FOLDER + "/screenshot-" + timestamp + ".png"
    captureScreen(gameDisplay, filename, (0, 0), (displayWidth, displayHeight))
