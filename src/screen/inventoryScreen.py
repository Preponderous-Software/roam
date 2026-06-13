import time
from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from crafting.recipeRegistry import RecipeRegistry
from inventory.inventory import Inventory
from inventory.inventorySlot import InventorySlot
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from screen.screenshotHelper import takeScreenshot
from ui.status import Status
import pygame


# @author Daniel McCoy Stephenson
@component
class InventoryScreen:
    def __init__(
        self,
        graphik: Graphik,
        config: Config,
        status: Status,
        inventory: Inventory,
        keyBindings: KeyBindings,
    ):
        self.graphik = graphik
        self.config = config
        self.status = status
        self.inventory = inventory
        self.keyBindings = keyBindings
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.cursorSlot = InventorySlot()
        self.craftPanelOpen = False
        self.recipeRegistry = RecipeRegistry()
        self.lastCraftToggleTime = 0

    def _drawSelectionBorder(self, x, y, width, height):
        borderWidth = 3
        color = (255, 255, 0)
        self.graphik.drawRectangle(x, y, width, borderWidth, color)
        self.graphik.drawRectangle(
            x, y + height - borderWidth, width, borderWidth, color
        )
        self.graphik.drawRectangle(x, y, borderWidth, height, color)
        self.graphik.drawRectangle(
            x + width - borderWidth, y, borderWidth, height, color
        )

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
        kb = self.keyBindings
        if key == pygame.K_ESCAPE and self.craftPanelOpen:
            self.craftPanelOpen = False
            return
        if key == kb.getKey("inventory") or key == pygame.K_ESCAPE:
            self.switchToWorldScreen()
        elif key == kb.getKey("screenshot"):
            takeScreenshot(self.graphik.getGameDisplay())
        else:
            self._handleHotbarKey(key)

    def _handleHotbarKey(self, key):
        # hotbar_1..hotbar_9 select inventory slots 0..8 and hotbar_0 selects
        # slot 9 (the "10th" hotbar key wraps to index 9).
        kb = self.keyBindings
        for index in range(10):
            if key == kb.getKey("hotbar_" + str((index + 1) % 10)):
                self.swapCursorSlotWithInventorySlotByIndex(index)
                return

    def switchToWorldScreen(self):
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawPlayerInventory(self):
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        self.graphik.drawRectangle(
            backgroundX, backgroundY, backgroundWidth, backgroundHeight, (0, 0, 0)
        )

        itemsPerRow = 5
        row = 0
        column = 0
        margin = 5
        mouseX, mouseY = pygame.mouse.get_pos()
        hoveredItemName = None
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
                    self._drawSelectionBorder(itemX, itemY, itemWidth, itemHeight)
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
                itemX <= mouseX < itemX + itemWidth
                and itemY <= mouseY < itemY + itemHeight
            ):
                hoveredItemName = item.getName()

            if (
                row * itemsPerRow + column
                == self.inventory.getSelectedInventorySlotIndex()
            ):
                self._drawSelectionBorder(itemX, itemY, itemWidth, itemHeight)

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

        closeKeyName = self.keyBindings.getKeyName("inventory").upper()
        self.graphik.drawText(
            "press [" + closeKeyName + "] or [Esc] to close",
            backgroundX,
            backgroundY + backgroundHeight + 20,
            20,
            (255, 255, 255),
        )
        self.graphik.drawText(
            "Left-click: swap  -  Right-click: select hotbar  -  Drop button: discard",
            backgroundX,
            backgroundY + backgroundHeight + 45,
            16,
            (180, 180, 180),
        )

        if hoveredItemName is not None:
            screenW, screenH = self.graphik.getGameDisplay().get_size()
            textWidth = len(hoveredItemName) * 8 + 12
            tooltipX = mouseX + 18
            tooltipY = mouseY + 18
            if tooltipX + textWidth > screenW:
                tooltipX = max(0, mouseX - textWidth - 8)
            if tooltipY + 22 > screenH:
                tooltipY = max(0, mouseY - 30)
            self.graphik.drawRectangle(
                tooltipX, tooltipY, textWidth, 22, (30, 30, 30)
            )
            self.graphik.drawText(
                hoveredItemName,
                tooltipX + textWidth / 2,
                tooltipY + 11,
                14,
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

    def _craftRowLayout(self, numRecipes):
        # Fit every recipe row inside the craft panel so none spill off the
        # bottom (the list grew past the fixed 40px-row layout's capacity).
        # Rows shrink to fit when there are many recipes, but are capped at the
        # original 50px stride so a short list doesn't balloon into huge buttons.
        _, panelY, _, panelHeight = self.getCraftPanelRect()
        recipeMargin = 10
        bottomPadding = 10
        startY = panelY + 60
        availableHeight = (panelY + panelHeight - bottomPadding) - startY
        defaultStride = 50
        rowStride = defaultStride
        if numRecipes > 0:
            rowStride = min(defaultStride, availableHeight / numRecipes)
        recipeButtonHeight = max(20, rowStride - recipeMargin)
        return startY, rowStride, recipeButtonHeight, recipeMargin

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
        craftableCount = sum(
            1 for r in recipes if r.canCraft(self.inventory)
        )
        self.graphik.drawText(
            f"{craftableCount} / {len(recipes)} craftable",
            panelX + panelWidth / 2,
            panelY + 40,
            14,
            (180, 180, 180),
        )
        startY, rowStride, recipeButtonHeight, recipeMargin = self._craftRowLayout(
            len(recipes)
        )

        for i, recipe in enumerate(recipes):
            recipeY = startY + i * rowStride
            ingredientText = ", ".join(
                [
                    str(count) + "x " + cls.__name__
                    for cls, count in recipe.getIngredients().items()
                ]
            )
            namePrefix = recipe.getName()
            if recipe.getResultCount() > 1:
                namePrefix = f"{recipe.getResultCount()}x " + namePrefix
            label = namePrefix + " (" + ingredientText + ")"

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
                missingParts = [
                    f"{required - self.inventory.getNumItemsByType(cls)} {cls.__name__}"
                    for cls, required in recipe.getIngredients().items()
                    if self.inventory.getNumItemsByType(cls) < required
                ]
                disabledLabel = (
                    f"{namePrefix} — need {', '.join(missingParts)}"
                    if missingParts
                    else label
                )
                self.graphik.drawRectangle(
                    panelX + recipeMargin,
                    recipeY,
                    panelWidth - 2 * recipeMargin,
                    recipeButtonHeight,
                    (60, 60, 60),
                )
                self.graphik.drawText(
                    disabledLabel,
                    panelX + panelWidth / 2,
                    recipeY + recipeButtonHeight / 2,
                    16,
                    (210, 210, 210),
                )

    def craftRecipe(self, recipe):
        if not recipe.canCraft(self.inventory):
            self.status.set("Not enough materials")
            return
        # Pre-validate capacity for all result items
        availableSpace = 0
        probe = recipe.getResultClass()()
        probeName = probe.getName()
        for slot in self.inventory.getInventorySlots():
            if slot.isEmpty():
                availableSpace += slot.getMaxStackSize()
            elif slot.getContents()[0].getName() == probeName:
                availableSpace += slot.getMaxStackSize() - slot.getNumItems()
        if availableSpace < recipe.getResultCount():
            self.status.set("Inventory full")
            return
        results = recipe.craft(self.inventory)
        if results is not None:
            for result in results:
                if not self.inventory.placeIntoFirstAvailableInventorySlot(result):
                    self.status.set("Inventory full while placing crafted items")
                    return
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

    def _dropButtonRect(self):
        _, height = self.graphik.getGameDisplay().get_size()
        return 10, height - 60, 100, 50

    def drawDropButton(self):
        buttonX, buttonY, buttonWidth, buttonHeight = self._dropButtonRect()
        mouseX, mouseY = pygame.mouse.get_pos()
        hovering = (
            buttonX <= mouseX <= buttonX + buttonWidth
            and buttonY <= mouseY <= buttonY + buttonHeight
        )
        # Muted red marks it as the destructive option, distinct from the white
        # Back / Craft buttons; it brightens on hover.
        color = (200, 110, 110) if hovering else (150, 80, 80)
        self.graphik.drawRectangle(buttonX, buttonY, buttonWidth, buttonHeight, color)
        self.graphik.drawText(
            "Drop",
            buttonX + buttonWidth / 2,
            buttonY + buttonHeight / 2,
            24,
            (255, 255, 255),
        )

    def isInsideDropButton(self, pos):
        buttonX, buttonY, buttonWidth, buttonHeight = self._dropButtonRect()
        return (
            buttonX <= pos[0] <= buttonX + buttonWidth
            and buttonY <= pos[1] <= buttonY + buttonHeight
        )

    def dropCursorSlot(self):
        self.cursorSlot.clear()

    def dropOneFromCursorSlot(self):
        if not self.cursorSlot.isEmpty():
            self.cursorSlot.pop()

    def handleMouseClickEvent(self, pos, button=1):
        # Dropping (discarding) cursor items now happens only via the explicit
        # Drop button, so a stray click in empty space can no longer silently
        # destroy a held stack (Nielsen #5, error prevention).
        if self.isInsideDropButton(pos):
            if not self.cursorSlot.isEmpty():
                if button == 2:  # middle mouse button drops a single item
                    self.dropOneFromCursorSlot()
                elif button == 1:  # left mouse button drops the whole stack
                    self.dropCursorSlot()
            return

        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        itemsPerRow = 5
        row = 0
        column = 0
        margin = 5
        for inventorySlot in self.inventory.getInventorySlots():
            itemX = backgroundX + column * backgroundWidth / itemsPerRow + margin
            itemY = backgroundY + row * backgroundHeight / itemsPerRow + margin
            itemWidth = backgroundWidth / itemsPerRow - 2 * margin
            itemHeight = backgroundHeight / itemsPerRow - 2 * margin

            if (
                pos[0] > itemX
                and pos[0] < itemX + itemWidth
                and pos[1] > itemY
                and pos[1] < itemY + itemHeight
            ):
                index = row * itemsPerRow + column

                # select that inventory slot if right mouse button was clicked
                if button == 3:
                    self.inventory.setSelectedInventorySlotIndex(index)
                    # Confirm the selection in the status line — the help text
                    # advertises this action, so a silent success leaves the
                    # player unsure it registered (Nielsen #1).
                    if inventorySlot.isEmpty():
                        self.status.set("Empty slot")
                    else:
                        self.status.set(
                            "Selected " + inventorySlot.getContents()[0].getName()
                        )
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

        # A click in empty space (outside any slot) intentionally does nothing
        # now — held cursor items are kept, not dropped.

    def drawCursorSlot(self):
        if self.cursorSlot.isEmpty():
            return

        item = self.cursorSlot.getContents()[0]
        image = item.getImage()
        cursorX, cursorY = pygame.mouse.get_pos()
        scaledImage = pygame.transform.scale(image, (50, 50))
        self.graphik.gameDisplay.blit(scaledImage, (cursorX, cursorY))

        count = self.cursorSlot.getNumItems()
        if count > 1:
            self.graphik.drawText(
                str(count),
                cursorX + 40,
                cursorY + 40,
                18,
                (255, 255, 255),
            )

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
            self.drawDropButton()
            self.drawCursorSlot()
            self.status.draw()
            pygame.display.update()

        if not self.cursorSlot.isEmpty():
            for item in self.cursorSlot.getContents():
                self.inventory.placeIntoFirstAvailableInventorySlot(item)
            self.cursorSlot.setContents([])

        self.changeScreen = False
        return self.nextScreen

    def setInventory(self, inventory):
        self.inventory = inventory
