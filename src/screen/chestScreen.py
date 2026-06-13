from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from inventory.inventory import Inventory
from inventory.inventorySlot import InventorySlot
from rendering.renderer import Renderer
from screen.screenType import ScreenType
from ui.status import Status
import pygame
from ui import palette


# @author Claude
# @since June 12th, 2026
@component
class ChestScreen:
    """Inventory-management screen for a placed Chest.

    Displays the chest's stored inventory (top panel) alongside the player's
    inventory (bottom panel) and lets items be moved between them via a cursor
    slot, mirroring InventoryScreen's left-click-to-swap behaviour. Closing the
    screen returns held cursor items to the player and triggers the on-close
    callback so the owning room (and the chest's contents) are persisted.
    """

    ITEMS_PER_ROW = 5

    def __init__(
        self,
        renderer: Renderer,
        config: Config,
        status: Status,
        inventory: Inventory,
        keyBindings: KeyBindings,
    ):
        self.renderer = renderer
        self.config = config
        self.status = status
        self.inventory = inventory
        self.keyBindings = keyBindings
        self.chest = None
        self.onClose = None
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = False
        self.cursorSlot = InventorySlot()

    def setInventory(self, inventory):
        self.inventory = inventory

    def setChest(self, chest):
        self.chest = chest

    def setOnClose(self, onClose):
        self.onClose = onClose

    def getChestInventory(self):
        return self.chest.getStoredInventory()

    def _chestTitle(self):
        # Confirm an empty chest in the title so the player can see at a glance
        # it holds nothing (and is therefore safe to pick up) without scanning
        # the slots one by one (Nielsen #1, visibility of system status).
        if self.getChestInventory().getNumItems() == 0:
            return "Chest (empty)"
        return "Chest"

    def switchToWorldScreen(self):
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def getChestPanelRect(self):
        width = self.renderer.getDisplayWidth()
        height = self.renderer.getDisplayHeight()
        return width / 4, height * 0.10, width / 2, height * 0.32

    def getPlayerPanelRect(self):
        width = self.renderer.getDisplayWidth()
        height = self.renderer.getDisplayHeight()
        return width / 4, height * 0.52, width / 2, height * 0.36

    def _slotGeometry(self, inventory, panelRect):
        panelX, panelY, panelWidth, panelHeight = panelRect
        slots = inventory.getInventorySlots()
        rows = max(1, (len(slots) + self.ITEMS_PER_ROW - 1) // self.ITEMS_PER_ROW)
        margin = 5
        cellWidth = panelWidth / self.ITEMS_PER_ROW
        cellHeight = panelHeight / rows
        for index, slot in enumerate(slots):
            row = index // self.ITEMS_PER_ROW
            column = index % self.ITEMS_PER_ROW
            itemX = panelX + column * cellWidth + margin
            itemY = panelY + row * cellHeight + margin
            itemWidth = cellWidth - 2 * margin
            itemHeight = cellHeight - 2 * margin
            yield index, slot, itemX, itemY, itemWidth, itemHeight

    def _drawPanel(self, inventory, panelRect, title):
        panelX, panelY, panelWidth, panelHeight = panelRect
        self.renderer.drawText(
            title, panelX + panelWidth / 2, panelY - 15, 20, palette.WHITE
        )
        self.renderer.drawRectangle(
            panelX, panelY, panelWidth, panelHeight, palette.BLACK
        )
        mouseX, mouseY = pygame.mouse.get_pos()
        hoveredItemName = None
        for index, slot, itemX, itemY, itemWidth, itemHeight in self._slotGeometry(
            inventory, panelRect
        ):
            if slot.isEmpty():
                self.renderer.drawRectangle(
                    itemX, itemY, itemWidth, itemHeight, palette.WHITE
                )
                continue
            item = slot.getContents()[0]
            scaledImage = pygame.transform.scale(
                item.getImage(), (itemWidth, itemHeight)
            )
            self.renderer.drawImage(scaledImage, (itemX, itemY))
            if (
                itemX <= mouseX < itemX + itemWidth
                and itemY <= mouseY < itemY + itemHeight
            ):
                hoveredItemName = item.getName()
            self.renderer.drawText(
                str(slot.getNumItems()),
                itemX + itemWidth - 20,
                itemY + itemHeight - 20,
                20,
                palette.WHITE,
            )
        return hoveredItemName

    def _drawTooltip(self, itemName):
        screenWidth, screenHeight = self.renderer.getDisplaySize()
        mouseX, mouseY = pygame.mouse.get_pos()
        textWidth = len(itemName) * 8 + 12
        tooltipX = mouseX + 18
        tooltipY = mouseY + 18
        if tooltipX + textWidth > screenWidth:
            tooltipX = max(0, mouseX - textWidth - 8)
        if tooltipY + 22 > screenHeight:
            tooltipY = max(0, mouseY - 30)
        self.renderer.drawRectangle(
            tooltipX, tooltipY, textWidth, 22, palette.NEAR_BLACK
        )
        self.renderer.drawText(
            itemName, tooltipX + textWidth / 2, tooltipY + 11, 14, palette.WHITE
        )

    def isInsidePanel(self, pos, panelRect):
        panelX, panelY, panelWidth, panelHeight = panelRect
        return (
            panelX <= pos[0] <= panelX + panelWidth
            and panelY <= pos[1] <= panelY + panelHeight
        )

    def swapCursorSlotWithSlot(self, slot):
        if (
            not self.cursorSlot.isEmpty()
            and not slot.isEmpty()
            and self.cursorSlot.getContents()[0].getName()
            == slot.getContents()[0].getName()
        ):
            self.inventory.mergeIntoSlot(self.cursorSlot, slot)
        else:
            slotContents = slot.getContents()
            cursorContents = self.cursorSlot.getContents()
            slot.setContents(cursorContents)
            self.cursorSlot.setContents(slotContents)

    def dropCursorSlot(self):
        self.cursorSlot.clear()

    def dropOneFromCursorSlot(self):
        if not self.cursorSlot.isEmpty():
            self.cursorSlot.pop()

    def handleKeyDownEvent(self, key):
        kb = self.keyBindings
        if key == kb.getKey("inventory") or key == pygame.K_ESCAPE:
            self.switchToWorldScreen()
        elif key == kb.getKey("screenshot"):
            self.renderer.captureScreenshot()

    def drawBackButton(self):
        width, height = self.renderer.getDisplaySize()
        buttonWidth = 100
        buttonHeight = 50
        buttonX = width - buttonWidth - 10
        buttonY = height - buttonHeight - 10
        self.renderer.drawButton(
            buttonX,
            buttonY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
            30,
            "Back",
            self.switchToWorldScreen,
        )

    def isInsideBackButton(self, pos):
        width, height = self.renderer.getDisplaySize()
        buttonWidth = 100
        buttonHeight = 50
        buttonX = width - buttonWidth - 10
        buttonY = height - buttonHeight - 10
        return (
            buttonX <= pos[0] <= buttonX + buttonWidth
            and buttonY <= pos[1] <= buttonY + buttonHeight
        )

    def _takeAllButtonRect(self):
        _, height = self.renderer.getDisplaySize()
        return 10, height - 60, 120, 50

    def drawTakeAllButton(self):
        buttonX, buttonY, buttonWidth, buttonHeight = self._takeAllButtonRect()
        self.renderer.drawButton(
            buttonX,
            buttonY,
            buttonWidth,
            buttonHeight,
            palette.WHITE,
            palette.BLACK,
            24,
            "Take All",
            self.takeAll,
        )

    def isInsideTakeAllButton(self, pos):
        buttonX, buttonY, buttonWidth, buttonHeight = self._takeAllButtonRect()
        return (
            buttonX <= pos[0] <= buttonX + buttonWidth
            and buttonY <= pos[1] <= buttonY + buttonHeight
        )

    def takeAll(self):
        chestInventory = self.getChestInventory()
        items = [
            item
            for slot in chestInventory.getInventorySlots()
            for item in list(slot.getContents())
        ]
        if not items:
            self.status.set("Chest is empty")
            return
        movedAny = False
        leftover = False
        for item in items:
            if self.inventory.placeIntoFirstAvailableInventorySlot(item):
                chestInventory.removeByItem(item)
                movedAny = True
            else:
                leftover = True
        if leftover:
            self.status.set(
                "Inventory full — took what fit" if movedAny else "Inventory full"
            )
        else:
            self.status.set("Took all items")

    def _quickTransfer(self, sourceSlot, destInventory):
        # Move a whole slot's stack to the other container without using the
        # cursor (shift-click), stopping if the destination runs out of room.
        if sourceSlot.isEmpty():
            return
        movedAny = False
        while not sourceSlot.isEmpty():
            item = sourceSlot.getContents()[0]
            if destInventory.placeIntoFirstAvailableInventorySlot(item):
                sourceSlot.remove(item)
                movedAny = True
            else:
                self.status.set("No room to transfer")
                return
        if movedAny:
            self.status.set("Transferred items")

    def _dropButtonRect(self):
        width, height = self.renderer.getDisplaySize()
        buttonWidth = 120
        return width / 2 - buttonWidth / 2, height - 60, buttonWidth, 50

    def drawDropButton(self):
        buttonX, buttonY, buttonWidth, buttonHeight = self._dropButtonRect()
        mouseX, mouseY = pygame.mouse.get_pos()
        hovering = (
            buttonX <= mouseX <= buttonX + buttonWidth
            and buttonY <= mouseY <= buttonY + buttonHeight
        )
        # A muted red marks it as the destructive option, distinct from the
        # white Back / Take All buttons; it brightens on hover.
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

    def handleMouseClickEvent(self, pos, button=1, shift=False):
        # The Back / Take All buttons are actioned by renderer.drawButton during
        # the draw phase; intercept their clicks here so they aren't reprocessed.
        if self.isInsideBackButton(pos) or self.isInsideTakeAllButton(pos):
            return

        # Dropping (discarding) cursor items now happens only via the explicit
        # Drop button, so it can no longer be triggered by an accidental click
        # in empty space (Nielsen #5, error prevention).
        if self.isInsideDropButton(pos):
            if self.cursorSlot.isEmpty():
                return
            if button == 2:  # middle mouse button drops a single item
                self.dropOneFromCursorSlot()
            elif button == 1:  # left mouse button drops the whole stack
                self.dropCursorSlot()
            return

        panels = (
            (self.getChestInventory(), self.getChestPanelRect(), self.inventory),
            (self.inventory, self.getPlayerPanelRect(), self.getChestInventory()),
        )
        for sourceInventory, panelRect, destInventory in panels:
            for index, slot, itemX, itemY, itemWidth, itemHeight in self._slotGeometry(
                sourceInventory, panelRect
            ):
                if (
                    itemX < pos[0] < itemX + itemWidth
                    and itemY < pos[1] < itemY + itemHeight
                ):
                    if shift and button == 1:
                        # Shift-click whisks the whole stack to the other
                        # container without picking it up onto the cursor.
                        self._quickTransfer(slot, destInventory)
                    elif button in (1, 3):
                        self.swapCursorSlotWithSlot(slot)
                    return

        # Clicking outside the panels and buttons keeps the cursor's items
        # rather than discarding them.

    def drawCursorSlot(self):
        if self.cursorSlot.isEmpty():
            return
        item = self.cursorSlot.getContents()[0]
        cursorX, cursorY = pygame.mouse.get_pos()
        scaledImage = pygame.transform.scale(item.getImage(), (50, 50))
        self.renderer.drawImage(scaledImage, (cursorX, cursorY))
        count = self.cursorSlot.getNumItems()
        if count > 1:
            self.renderer.drawText(
                str(count), cursorX + 40, cursorY + 40, 18, palette.WHITE
            )

    def drawInstructions(self):
        # Drawn along the top so it stays clear of the Take All / Drop / Back
        # button row across the bottom of the screen.
        width, _ = self.renderer.getDisplaySize()
        closeKeyName = self.keyBindings.getKeyName("inventory").upper()
        self.renderer.drawText(
            "Left-click: move  -  Shift-click: transfer between chest and inventory",
            width / 2,
            14,
            16,
            palette.MEDIUM_GRAY,
        )
        self.renderer.drawText(
            "press [" + closeKeyName + "] or [Esc] to close",
            width / 2,
            32,
            14,
            palette.MEDIUM_GRAY,
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
                    shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                    self.handleMouseClickEvent(event.pos, event.button, shift)

            self.renderer.clearScreen(palette.BLACK)
            hoveredChestItem = self._drawPanel(
                self.getChestInventory(), self.getChestPanelRect(), self._chestTitle()
            )
            hoveredPlayerItem = self._drawPanel(
                self.inventory, self.getPlayerPanelRect(), "Inventory"
            )
            self.drawInstructions()
            self.drawBackButton()
            self.drawTakeAllButton()
            self.drawDropButton()
            hoveredItemName = hoveredChestItem or hoveredPlayerItem
            if hoveredItemName is not None and self.cursorSlot.isEmpty():
                self._drawTooltip(hoveredItemName)
            self.drawCursorSlot()
            self.status.draw()
            self.renderer.present()

        # Return any held cursor items on close so nothing is lost: prefer the
        # player's inventory, but if it's full, fall back to the chest the items
        # came from rather than silently discarding them.
        if not self.cursorSlot.isEmpty():
            for item in self.cursorSlot.getContents():
                if not self.inventory.placeIntoFirstAvailableInventorySlot(item):
                    self.getChestInventory().placeIntoFirstAvailableInventorySlot(item)
            self.cursorSlot.setContents([])

        if self.onClose is not None:
            self.onClose()

        self.changeScreen = False
        return self.nextScreen
