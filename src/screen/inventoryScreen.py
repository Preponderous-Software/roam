import datetime
import os
import time
from config.config import Config
from crafting.recipeRegistry import RecipeRegistry
from inventory.inventory import Inventory
from inventory.inventorySlot import InventorySlot
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from ui.status import Status
import pygame


# @author Daniel McCoy Stephenson
class InventoryScreen:
    def __init__(
        self, graphik: Graphik, config: Config, status: Status, inventory: Inventory
    ):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.inventory = inventory
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.cursorSlot = InventorySlot()
        self.craftPanelOpen = False
        self.recipeRegistry = RecipeRegistry()
        self.lastCraftToggleTime = 0

    # @source https://stackoverflow.com/questions/63342477/how-to-take-screenshot-of-entire-display-pygame
    def captureScreen(self, name, pos, size):  # (pygame Surface, String, tuple, tuple)
        image = pygame.Surface(size)  # Create image surface
        image.blit(
            self.graphik.getGameDisplay(), (0, 0), (pos, size)
        )  # Blit portion of the display to the image
        pygame.image.save(image, name)  # Save the image to the disk**

    def swapCursorSlotWithInventorySlotByIndex(self, index):
        destSlot = self.inventory.getInventorySlots()[index]
        if self.cursorSlot.isEmpty():
            self.cursorSlot.setContents(destSlot.getContents())
            destSlot.setContents([])
        elif (
            not destSlot.isEmpty()
            and self.cursorSlot.getContents()[0].getName()
            == destSlot.getContents()[0].getName()
        ):
            self.inventory.mergeIntoSlot(self.cursorSlot, destSlot)
        else:
            temp = destSlot.getContents()
            destSlot.setContents(self.cursorSlot.getContents())
            self.cursorSlot.setContents(temp)

    def handleKeyDownEvent(self, key):
        if key == pygame.K_i or key == pygame.K_ESCAPE:
            self.switchToWorldScreen()
        elif key == pygame.K_PRINTSCREEN:
            screenshotsFolder = "screenshots"
            if not os.path.exists(screenshotsFolder):
                os.makedirs(screenshotsFolder)
            x, y = self.graphik.getGameDisplay().get_size()
            self.captureScreen(
                screenshotsFolder
                + "/screenshot-"
                + str(datetime.datetime.now()).replace(" ", "-").replace(":", ".")
                + ".png",
                (0, 0),
                (x, y),
            )
        elif key == pygame.K_1:
            self.swapCursorSlotWithInventorySlotByIndex(0)
        elif key == pygame.K_2:
            self.swapCursorSlotWithInventorySlotByIndex(1)
        elif key == pygame.K_3:
            self.swapCursorSlotWithInventorySlotByIndex(2)
        elif key == pygame.K_4:
            self.swapCursorSlotWithInventorySlotByIndex(3)
        elif key == pygame.K_5:
            self.swapCursorSlotWithInventorySlotByIndex(4)
        elif key == pygame.K_6:
            self.swapCursorSlotWithInventorySlotByIndex(5)
        elif key == pygame.K_7:
            self.swapCursorSlotWithInventorySlotByIndex(6)
        elif key == pygame.K_8:
            self.swapCursorSlotWithInventorySlotByIndex(7)
        elif key == pygame.K_9:
            self.swapCursorSlotWithInventorySlotByIndex(8)
        elif key == pygame.K_0:
            self.swapCursorSlotWithInventorySlotByIndex(9)

    def switchToWorldScreen(self):
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawPlayerInventory(self):
        # draw inventory background that is 50% size of screen and centered
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        self.graphik.drawRectangle(
            backgroundX, backgroundY, backgroundWidth, backgroundHeight, (0, 0, 0)
        )

        # draw contents inside inventory background
        itemsPerRow = 5
        row = 0
        column = 0
        margin = 5
        for inventorySlot in self.inventory.getInventorySlots():
            itemX = backgroundX + column * backgroundWidth / itemsPerRow + margin
            itemY = backgroundY + row * backgroundHeight / itemsPerRow + margin
            itemWidth = backgroundWidth / itemsPerRow - 2 * margin
            itemHeight = backgroundHeight / itemsPerRow - 2 * margin

            if inventorySlot.isEmpty():
                self.graphik.drawRectangle(
                    itemX, itemY, itemWidth, itemHeight, (255, 255, 255)
                )
                if (
                    row * itemsPerRow + column
                    == self.inventory.getSelectedInventorySlotIndex()
                ):
                    # draw yellow square in the middle of the selected inventory slot (may be on any row)
                    self.graphik.drawRectangle(
                        itemX + itemWidth / 2 - 5,
                        itemY + itemHeight / 2 - 5,
                        10,
                        10,
                        (255, 255, 0),
                    )
                column += 1
                if column == itemsPerRow:
                    column = 0
                    row += 1
                continue

            item = inventorySlot.getContents()[0]
            image = item.getImage()
            scaledImage = pygame.transform.scale(image, (itemWidth, itemHeight))
            self.graphik.gameDisplay.blit(scaledImage, (itemX, itemY))

            if (
                row * itemsPerRow + column
                == self.inventory.getSelectedInventorySlotIndex()
            ):
                # draw yellow square in the middle of the selected inventory slot
                self.graphik.drawRectangle(
                    itemX + itemWidth / 2 - 5,
                    itemY + itemHeight / 2 - 5,
                    10,
                    10,
                    (255, 255, 0),
                )

            # draw item amount in bottom right corner of inventory slot
            self.graphik.drawText(
                str(inventorySlot.getNumItems()),
                itemX + itemWidth - 20,
                itemY + itemHeight - 20,
                20,
                (255, 255, 255),
            )

            column += 1
            if column == itemsPerRow:
                column = 0
                row += 1

        # draw '(press I to close)' text below inventory
        self.graphik.drawText(
            "(press I to close)",
            backgroundX,
            backgroundY + backgroundHeight + 20,
            20,
            (255, 255, 255),
        )

    def toggleCraftPanel(self):
        now = time.time()
        if now - self.lastCraftToggleTime < 1:
            return
        self.lastCraftToggleTime = now
        self.craftPanelOpen = not self.craftPanelOpen

    def drawCraftButton(self):
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        buttonWidth = 100
        buttonHeight = 30
        buttonX = backgroundX + backgroundWidth - buttonWidth
        buttonY = backgroundY + backgroundHeight + 20
        self.graphik.drawButton(
            buttonX,
            buttonY,
            buttonWidth,
            buttonHeight,
            (255, 255, 255),
            (0, 0, 0),
            20,
            "Craft",
            self.toggleCraftPanel,
        )

    def getCraftPanelRect(self):
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        panelX = backgroundX + backgroundWidth + 10
        panelY = backgroundY
        panelWidth = backgroundWidth * 0.6
        panelHeight = backgroundHeight
        return panelX, panelY, panelWidth, panelHeight

    def drawCraftPanel(self):
        if not self.craftPanelOpen:
            return

        panelX, panelY, panelWidth, panelHeight = self.getCraftPanelRect()
        self.graphik.drawRectangle(panelX, panelY, panelWidth, panelHeight, (0, 0, 0))

        self.graphik.drawText(
            "Recipes",
            panelX + panelWidth / 2,
            panelY + 20,
            24,
            (255, 255, 255),
        )

        recipes = self.recipeRegistry.getRecipes()
        recipeButtonHeight = 40
        recipeMargin = 10
        startY = panelY + 50

        for i, recipe in enumerate(recipes):
            recipeY = startY + i * (recipeButtonHeight + recipeMargin)
            ingredientText = ", ".join(
                [
                    str(count) + "x " + cls.__name__
                    for cls, count in recipe.getIngredients().items()
                ]
            )
            label = recipe.getName() + " (" + ingredientText + ")"

            if recipe.canCraft(self.inventory):
                self.graphik.drawButton(
                    panelX + recipeMargin,
                    recipeY,
                    panelWidth - 2 * recipeMargin,
                    recipeButtonHeight,
                    (255, 255, 255),
                    (0, 0, 0),
                    16,
                    label,
                    lambda r=recipe: self.craftRecipe(r),
                )
            else:
                self.graphik.drawRectangle(
                    panelX + recipeMargin,
                    recipeY,
                    panelWidth - 2 * recipeMargin,
                    recipeButtonHeight,
                    (80, 80, 80),
                )
                self.graphik.drawText(
                    label,
                    panelX + panelWidth / 2,
                    recipeY + recipeButtonHeight / 2,
                    16,
                    (150, 150, 150),
                )

    def craftRecipe(self, recipe):
        if not recipe.canCraft(self.inventory):
            self.status.set("Not enough materials")
            return
        if not self.inventory.hasAvailableSlotFor(recipe.getResultClass()):
            self.status.set("Inventory full")
            return
        result = recipe.craft(self.inventory)
        if result is not None:
            self.inventory.placeIntoFirstAvailableInventorySlot(result)
            self.status.set("Crafted " + recipe.getName())

    def drawBackButton(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = 100
        height = 50
        xpos = x - width - 10
        ypos = y - height - 10
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            (255, 255, 255),
            (0, 0, 0),
            30,
            "Back",
            self.switchToWorldScreen,
        )

    def isInsideInventoryPanel(self, pos):
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        return (
            pos[0] >= backgroundX
            and pos[0] <= backgroundX + backgroundWidth
            and pos[1] >= backgroundY
            and pos[1] <= backgroundY + backgroundHeight
        )

    def isInsideBackButton(self, pos):
        x, y = self.graphik.getGameDisplay().get_size()
        width = 100
        height = 50
        xpos = x - width - 10
        ypos = y - height - 10
        return (
            pos[0] >= xpos
            and pos[0] <= xpos + width
            and pos[1] >= ypos
            and pos[1] <= ypos + height
        )

    def isInsideCraftButton(self, pos):
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        buttonWidth = 100
        buttonHeight = 30
        buttonX = backgroundX + backgroundWidth - buttonWidth
        buttonY = backgroundY + backgroundHeight + 20
        return (
            pos[0] >= buttonX
            and pos[0] <= buttonX + buttonWidth
            and pos[1] >= buttonY
            and pos[1] <= buttonY + buttonHeight
        )

    def isInsideCraftPanel(self, pos):
        if not self.craftPanelOpen:
            return False
        panelX, panelY, panelWidth, panelHeight = self.getCraftPanelRect()
        return (
            pos[0] >= panelX
            and pos[0] <= panelX + panelWidth
            and pos[1] >= panelY
            and pos[1] <= panelY + panelHeight
        )

    def dropCursorSlot(self):
        self.cursorSlot.clear()

    def dropOneFromCursorSlot(self):
        if not self.cursorSlot.isEmpty():
            self.cursorSlot.pop()

    def handleMouseClickEvent(self, pos, button=1):
        # get inventory slot that was clicked
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        itemsPerRow = 5
        row = 0
        column = 0
        margin = 5
        clickedSlot = False
        for inventorySlot in self.inventory.getInventorySlots():
            itemX = backgroundX + column * backgroundWidth / itemsPerRow + margin
            itemY = backgroundY + row * backgroundHeight / itemsPerRow + margin
            itemWidth = backgroundWidth / itemsPerRow - 2 * margin
            itemHeight = backgroundHeight / itemsPerRow - 2 * margin

            # if mouse click was inside inventory slot
            if (
                pos[0] > itemX
                and pos[0] < itemX + itemWidth
                and pos[1] > itemY
                and pos[1] < itemY + itemHeight
            ):
                clickedSlot = True
                index = row * itemsPerRow + column

                # select that inventory slot if right mouse button was clicked
                if button == 3:
                    self.inventory.setSelectedInventorySlotIndex(index)
                    return

                # merge matching cursor and inventory slot items, otherwise swap them
                if (
                    not self.cursorSlot.isEmpty()
                    and not inventorySlot.isEmpty()
                    and self.cursorSlot.getContents()[0].getName()
                    == inventorySlot.getContents()[0].getName()
                ):
                    self.inventory.mergeIntoSlot(self.cursorSlot, inventorySlot)
                else:
                    inventorySlotContents = inventorySlot.getContents()
                    cursorSlotContents = self.cursorSlot.getContents()
                    inventorySlot.setContents(cursorSlotContents)
                    self.cursorSlot.setContents(inventorySlotContents)

            column += 1
            if column == itemsPerRow:
                column = 0
                row += 1

        # drop items from cursor slot when clicking outside the inventory panel
        if not clickedSlot and not self.isInsideInventoryPanel(pos):
            if self.isInsideBackButton(pos) or self.isInsideCraftButton(pos):
                return
            if self.isInsideCraftPanel(pos):
                return
            if not self.cursorSlot.isEmpty():
                if button == 2:  # middle mouse button
                    self.dropOneFromCursorSlot()
                elif button == 1:  # left mouse button
                    self.dropCursorSlot()

    def drawCursorSlot(self):
        if self.cursorSlot.isEmpty():
            return

        item = self.cursorSlot.getContents()[0]
        image = item.getImage()
        scaledImage = pygame.transform.scale(image, (50, 50))
        self.graphik.gameDisplay.blit(scaledImage, pygame.mouse.get_pos())

    def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handleMouseClickEvent(event.pos, event.button)

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawPlayerInventory()
            self.drawCraftButton()
            self.drawCraftPanel()
            self.drawBackButton()
            self.drawCursorSlot()
            self.status.draw()
            pygame.display.update()

        # empty cursor slot when exiting inventory screen
        if not self.cursorSlot.isEmpty():
            for item in self.cursorSlot.getContents():
                self.inventory.placeIntoFirstAvailableInventorySlot(item)
            self.cursorSlot.setContents([])

        self.changeScreen = False
        return self.nextScreen

    def setInventory(self, inventory):
        self.inventory = inventory
