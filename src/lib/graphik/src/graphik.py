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
        self.drawRectangle(xpos, ypos, width, height, colorBox)
        self.drawText(
            text, xpos + (width // 2), ypos + (height // 2), sizeText, colorText
        )

        # if clicked then do function
        mouse = pygame.mouse.get_pos()
        if xpos + width > mouse[0] > xpos and ypos + height > mouse[1] > ypos:
            click = pygame.mouse.get_pressed()
            if click[0] == 1:
                function()
