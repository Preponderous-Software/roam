# @author Copilot
# @since April 20th, 2026
import pygame

from appContainer import component
from gameLogging.logger import getLogger
from screen.screenType import ScreenType

_logger = getLogger(__name__)


@component
class MenuController:
    """Routes menu navigation and screen transitions."""

    def __init__(self):
        self.nextScreen = ScreenType.SAVE_SELECTION_SCREEN
        self.changeScreen = False

    def handleKeyDownEvent(self, key):
        if key == pygame.K_ESCAPE:
            pygame.quit()
            quit()
        else:
            self.navigateTo(ScreenType.SAVE_SELECTION_SCREEN)

    def navigateTo(self, screenType):
        self.nextScreen = screenType
        self.changeScreen = True

    def getNextScreen(self):
        return self.nextScreen

    def shouldChangeScreen(self):
        return self.changeScreen

    def resetChangeScreen(self):
        self.changeScreen = False
