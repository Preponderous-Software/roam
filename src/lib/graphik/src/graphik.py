import pygame


#  @author Daniel McCoy Stephenson
#  @since February 3rd, 2022
class Graphik:
    def __init__(self):
        displayWidth = 900
        displayHeight = 600
        self.gameDisplay = pygame.display.set_mode((displayWidth, displayHeight))

        self.black = (0, 0, 0)
        self.white = (255, 255, 255)
        self.red = (200, 0, 0)
        self.green = (0, 200, 0)
        self.blue = (0, 0, 200)

    def __init__(self, gameDisplay):
        self.gameDisplay = gameDisplay
        self._mouseDownPrev = False
        self._mouseDownCurrent = False
        self._frameStarted = False

    def beginFrame(self):
        """Snapshot mouse state once per frame so drawButton fires only on the
        down-transition (press), not continuously while the button is held."""
        if not self._frameStarted:
            self._mouseDownPrev = self._mouseDownCurrent
            self._mouseDownCurrent = pygame.mouse.get_pressed()[0] == 1
            self._frameStarted = True

    def endFrame(self):
        self._frameStarted = False

    def getGameDisplay(self):
        return self.gameDisplay

    # Returns a centered square rect that fills as much space as possible.
    def getGameAreaRect(self):
        width, height = self.gameDisplay.get_size()
        size = min(width, height)
        x = (width - size) // 2
        y = (height - size) // 2
        return pygame.Rect(x, y, size, size)

    def getVersion(self):
        return self.version

    def drawRectangle(self, xpos, ypos, width, height, color):
        pygame.draw.rect(self.gameDisplay, color, [xpos, ypos, width, height])

    def drawText(self, text, xpos, ypos, size, color):
        myFont = pygame.font.Font("freesansbold.ttf", size)
        textSurface = myFont.render(text, True, color)
        textRectangle = textSurface.get_rect()
        textRectangle.center = (xpos, ypos)
        self.gameDisplay.blit(textSurface, textRectangle)

    def drawButton(
        self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function
    ):
        mouse = pygame.mouse.get_pos()
        hovering = xpos + width > mouse[0] > xpos and ypos + height > mouse[1] > ypos

        # Lift the background slightly on hover so users can see the button is
        # interactive. Light backgrounds darken, dark backgrounds lighten — the
        # delta is the same direction either way so the cue reads consistently.
        if hovering:
            avg = (colorBox[0] + colorBox[1] + colorBox[2]) / 3
            if avg >= 128:
                shift = -25
            else:
                shift = 35
            drawColor = (
                max(0, min(255, colorBox[0] + shift)),
                max(0, min(255, colorBox[1] + shift)),
                max(0, min(255, colorBox[2] + shift)),
            )
        else:
            drawColor = colorBox

        self.drawRectangle(xpos, ypos, width, height, drawColor)
        self.drawText(
            text, xpos + (width // 2), ypos + (height // 2), sizeText, colorText
        )

        if hovering and self._mouseDownCurrent and not self._mouseDownPrev:
            function()
