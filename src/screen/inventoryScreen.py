import time
from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from crafting.recipeRegistry import RecipeRegistry
from inventory.inventory import Inventory
from inventory.inventorySlot import InventorySlot
from rendering.renderer import Renderer
from rendering.inputSource import InputSource
from rendering.inputEvent import EventType
from rendering.keyCode import KeyCode
from screen.screenType import ScreenType
from screen.screen import Screen
from ui.status import Status
from ui import palette


# @author Daniel McCoy Stephenson
@component
class InventoryScreen(Screen):
    def __init__(
        self,
        renderer: Renderer,
        inputSource: InputSource,
        config: Config,
        status: Status,
        inventory: Inventory,
        keyBindings: KeyBindings,
    ):
        self.renderer = renderer
        self.inputSource = inputSource
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
        self._craftCursor = 0

    def _drawSelectionBorder(self, x, y, width, height):
        self.renderer.drawSelectionHighlight(x, y, width, height, (255, 255, 0))

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

    _ITEMS_PER_ROW = 5
    _NAV_KEYS = frozenset({
        KeyCode.UP, KeyCode.DOWN, KeyCode.LEFT, KeyCode.RIGHT,
        KeyCode.W, KeyCode.A, KeyCode.S,
        KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE, KeyCode.D,
    })

    def _announceSelectedSlot(self):
        slot = self.inventory.getInventorySlots()[
            self.inventory.getSelectedInventorySlotIndex()
        ]
        if slot.isEmpty():
            self.status.set("Empty slot")
        else:
            item = slot.getContents()[0]
            count = slot.getNumItems()
            self.status.set(item.getName() + (f" x{count}" if count > 1 else ""))

    def handleKeyDownEvent(self, key):
        kb = self.keyBindings
        if key == KeyCode.ESCAPE and self.craftPanelOpen:
            self.craftPanelOpen = False
            return
        if key == kb.getKey("inventory") or key == KeyCode.ESCAPE:
            self.switchToWorldScreen()
            return
        if key == kb.getKey("screenshot"):
            self.renderer.captureScreenshot()
            return
        # When the craft panel is open, arrow keys / W S and Enter navigate recipes.
        if self.craftPanelOpen:
            recipes = self.recipeRegistry.getRecipes()
            if key in (KeyCode.UP, KeyCode.W):
                self._craftCursor = max(0, self._craftCursor - 1)
                return
            if key in (KeyCode.DOWN, KeyCode.S):
                if recipes:
                    self._craftCursor = min(len(recipes) - 1, self._craftCursor + 1)
                return
            if key in (KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE):
                if 0 <= self._craftCursor < len(recipes):
                    self.craftRecipe(recipes[self._craftCursor])
                return
        if key == KeyCode.C:
            self.toggleCraftPanel()
            return
        if key in self._NAV_KEYS:
            idx = self.inventory.getSelectedInventorySlotIndex()
            n = len(self.inventory.getInventorySlots())
            cols = self._ITEMS_PER_ROW
            moved = False
            if key == KeyCode.RIGHT:
                self.inventory.setSelectedInventorySlotIndex((idx + 1) % n)
                moved = True
            elif key in (KeyCode.LEFT, KeyCode.A):
                self.inventory.setSelectedInventorySlotIndex((idx - 1) % n)
                moved = True
            elif key in (KeyCode.DOWN, KeyCode.S):
                self.inventory.setSelectedInventorySlotIndex(min(idx + cols, n - 1))
                moved = True
            elif key in (KeyCode.UP, KeyCode.W):
                self.inventory.setSelectedInventorySlotIndex(max(idx - cols, 0))
                moved = True
            elif key in (KeyCode.RETURN, KeyCode.KP_ENTER, KeyCode.SPACE):
                self.swapCursorSlotWithInventorySlotByIndex(idx)
            elif key == KeyCode.D:
                self.dropCursorSlot()
            if moved:
                self._announceSelectedSlot()
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

    def drawPlayerInventory(self):
        backgroundX = self.renderer.getDisplayWidth() / 4
        backgroundY = self.renderer.getDisplayHeight() / 4
        backgroundWidth = self.renderer.getDisplayWidth() / 2
        backgroundHeight = self.renderer.getDisplayHeight() / 2
        self.renderer.drawRectangle(
            backgroundX, backgroundY, backgroundWidth, backgroundHeight, palette.BLACK
        )

        itemsPerRow = 5
        row = 0
        column = 0
        margin = 5
        mouseX, mouseY = self.inputSource.getMousePosition()
        hoveredItemName = None
        for inventorySlot in self.inventory.getInventorySlots():
            itemX = backgroundX + column * backgroundWidth / itemsPerRow + margin
            itemY = backgroundY + row * backgroundHeight / itemsPerRow + margin
            itemWidth = backgroundWidth / itemsPerRow - 2 * margin
            itemHeight = backgroundHeight / itemsPerRow - 2 * margin

            if inventorySlot.isEmpty():
                self.renderer.drawRectangle(
                    itemX, itemY, itemWidth, itemHeight, palette.WHITE
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
            image = self.renderer.loadImage(item.getImagePath())
            scaledImage = self.renderer.scaleImage(image, (itemWidth, itemHeight))
            self.renderer.drawImage(scaledImage, (itemX, itemY))

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

            self.renderer.drawText(
                str(inventorySlot.getNumItems()),
                itemX + itemWidth - 20,
                itemY + itemHeight - 20,
                20,
                palette.WHITE,
            )

            column += 1
            if column == itemsPerRow:
                column = 0
                row += 1

        closeKeyName = self.keyBindings.getKeyName("inventory").upper()
        self.renderer.drawText(
            "press [" + closeKeyName + "] or [Esc] to close",
            backgroundX,
            backgroundY + backgroundHeight + 20,
            20,
            palette.WHITE,
        )
        self.renderer.drawText(
            "Arrows / W A S: navigate  -  Enter/Space: pick up / put down  -  D: discard held  -  C: craft",
            backgroundX,
            backgroundY + backgroundHeight + 42,
            14,
            palette.MEDIUM_GRAY,
        )
        if self.renderer.supportsImageLoading():
            self.renderer.drawText(
                "Left-click: swap  -  Right-click: select hotbar  -  Drop button: discard",
                backgroundX,
                backgroundY + backgroundHeight + 58,
                14,
                palette.DIM_GRAY,
            )
        if not self.cursorSlot.isEmpty():
            heldItem = self.cursorSlot.getContents()[0]
            heldCount = self.cursorSlot.getNumItems()
            heldText = "Holding: " + heldItem.getName()
            if heldCount > 1:
                heldText += " x" + str(heldCount)
            self.renderer.drawText(
                heldText,
                backgroundX + backgroundWidth / 2,
                backgroundY - 20,
                18,
                (255, 255, 160),
            )

        if hoveredItemName is not None:
            screenW, screenH = self.renderer.getDisplaySize()
            textWidth = len(hoveredItemName) * 8 + 12
            tooltipX = mouseX + 18
            tooltipY = mouseY + 18
            if tooltipX + textWidth > screenW:
                tooltipX = max(0, mouseX - textWidth - 8)
            if tooltipY + 22 > screenH:
                tooltipY = max(0, mouseY - 30)
            self.renderer.drawRectangle(
                tooltipX, tooltipY, textWidth, 22, palette.NEAR_BLACK
            )
            self.renderer.drawText(
                hoveredItemName,
                tooltipX + textWidth / 2,
                tooltipY + 11,
                14,
                palette.WHITE,
            )

    def toggleCraftPanel(self):
        now = time.time()
        if now - self.lastCraftToggleTime < 1:
            return
        self.lastCraftToggleTime = now
        self.craftPanelOpen = not self.craftPanelOpen
        if self.craftPanelOpen:
            self._craftCursor = 0

    def drawCraftButton(self):
        backgroundX = self.renderer.getDisplayWidth() / 4
        backgroundY = self.renderer.getDisplayHeight() / 4
        backgroundWidth = self.renderer.getDisplayWidth() / 2
        backgroundHeight = self.renderer.getDisplayHeight() / 2
        buttonWidth = 100
        buttonHeight = 30
        buttonX = backgroundX + backgroundWidth - buttonWidth
        buttonY = backgroundY + backgroundHeight + 20
        self.renderer.drawButton(
            buttonX,
            buttonY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
            20,
            "Craft",
            self.toggleCraftPanel,
        )

    def getCraftPanelRect(self):
        backgroundX = self.renderer.getDisplayWidth() / 4
        backgroundY = self.renderer.getDisplayHeight() / 4
        backgroundWidth = self.renderer.getDisplayWidth() / 2
        backgroundHeight = self.renderer.getDisplayHeight() / 2
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
        self.renderer.drawRectangle(
            panelX, panelY, panelWidth, panelHeight, palette.BLACK
        )

        self.renderer.drawText(
            "Recipes",
            panelX + panelWidth / 2,
            panelY + 20,
            24,
            palette.WHITE,
        )

        recipes = self.recipeRegistry.getRecipes()
        craftableCount = sum(1 for r in recipes if r.canCraft(self.inventory))
        self.renderer.drawText(
            f"{craftableCount} / {len(recipes)} craftable  —  Up/Down: navigate  Enter: craft  C/Esc: close",
            panelX + panelWidth / 2,
            panelY + 40,
            12,
            palette.MEDIUM_GRAY,
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
                self.renderer.drawButton(
                    panelX + recipeMargin,
                    recipeY,
                    panelWidth - 2 * recipeMargin,
                    recipeButtonHeight,
                    palette.WHITE,
                    palette.BLACK,
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
                self.renderer.drawRectangle(
                    panelX + recipeMargin,
                    recipeY,
                    panelWidth - 2 * recipeMargin,
                    recipeButtonHeight,
                    palette.DARKER_GRAY,
                )
                self.renderer.drawText(
                    disabledLabel,
                    panelX + panelWidth / 2,
                    recipeY + recipeButtonHeight / 2,
                    16,
                    (210, 210, 210),
                )
            if i == self._craftCursor:
                self.renderer.drawSelectionHighlight(
                    panelX + recipeMargin,
                    recipeY,
                    panelWidth - 2 * recipeMargin,
                    recipeButtonHeight,
                    (255, 255, 0),
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
        x, y = self.renderer.getDisplaySize()
        width = 100
        height = 50
        xpos = x - width - 10
        ypos = y - height - 10
        self.renderer.drawButton(
            xpos,
            ypos,
            width,
            height,
            palette.WHITE,
            palette.BLACK,
            30,
            "Back",
            self.switchToWorldScreen,
        )

    def isInsideInventoryPanel(self, pos):
        backgroundX = self.renderer.getDisplayWidth() / 4
        backgroundY = self.renderer.getDisplayHeight() / 4
        backgroundWidth = self.renderer.getDisplayWidth() / 2
        backgroundHeight = self.renderer.getDisplayHeight() / 2
        return (
            pos[0] >= backgroundX
            and pos[0] <= backgroundX + backgroundWidth
            and pos[1] >= backgroundY
            and pos[1] <= backgroundY + backgroundHeight
        )

    def isInsideBackButton(self, pos):
        x, y = self.renderer.getDisplaySize()
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
        backgroundX = self.renderer.getDisplayWidth() / 4
        backgroundY = self.renderer.getDisplayHeight() / 4
        backgroundWidth = self.renderer.getDisplayWidth() / 2
        backgroundHeight = self.renderer.getDisplayHeight() / 2
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
        _, height = self.renderer.getDisplaySize()
        return 10, height - 60, 100, 50

    def drawDropButton(self):
        buttonX, buttonY, buttonWidth, buttonHeight = self._dropButtonRect()
        mouseX, mouseY = self.inputSource.getMousePosition()
        hovering = (
            buttonX <= mouseX <= buttonX + buttonWidth
            and buttonY <= mouseY <= buttonY + buttonHeight
        )
        # Muted red marks it as the destructive option, distinct from the white
        # Back / Craft buttons; it brightens on hover.
        color = (200, 110, 110) if hovering else (150, 80, 80)
        self.renderer.drawRectangle(buttonX, buttonY, buttonWidth, buttonHeight, color)
        self.renderer.drawText(
            "Drop",
            buttonX + buttonWidth / 2,
            buttonY + buttonHeight / 2,
            24,
            palette.WHITE,
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

        backgroundX = self.renderer.getDisplayWidth() / 4
        backgroundY = self.renderer.getDisplayHeight() / 4
        backgroundWidth = self.renderer.getDisplayWidth() / 2
        backgroundHeight = self.renderer.getDisplayHeight() / 2
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
        image = self.renderer.loadImage(item.getImagePath())
        cursorX, cursorY = self.inputSource.getMousePosition()
        scaledImage = self.renderer.scaleImage(image, (50, 50))
        self.renderer.drawImage(scaledImage, (cursorX, cursorY))

        count = self.cursorSlot.getNumItems()
        if count > 1:
            self.renderer.drawText(
                str(count),
                cursorX + 40,
                cursorY + 40,
                18,
                palette.WHITE,
            )

    def handleEvent(self, event):
        if event.type == EventType.KEY_DOWN:
            self.handleKeyDownEvent(event.key)
        elif event.type == EventType.MOUSE_DOWN:
            self.handleMouseClickEvent(event.position, event.button)

    def draw(self):
        self.renderer.clearScreen(palette.BLACK)
        self.drawPlayerInventory()
        self.drawCraftButton()
        self.drawCraftPanel()
        self.drawBackButton()
        self.drawDropButton()
        self.drawCursorSlot()
        self.status.draw()

    def onExit(self):
        if not self.cursorSlot.isEmpty():
            for item in self.cursorSlot.getContents():
                self.inventory.placeIntoFirstAvailableInventorySlot(item)
            self.cursorSlot.setContents([])

    def setInventory(self, inventory):
        self.inventory = inventory
