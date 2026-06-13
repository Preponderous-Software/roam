from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from inventory.inventory import Inventory
from inventory.inventorySlot import InventorySlot
from lib.graphik.src.graphik import Graphik
from screen.screenType import ScreenType
from screen.screenshotHelper import takeScreenshot
from ui.status import Status
import pygame


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

    def switchToWorldScreen(self):
        self.nextScreen = ScreenType.WORLD_SCREEN
        self.changeScreen = True

    def getChestPanelRect(self):
        width = self.graphik.getGameDisplay().get_width()
        height = self.graphik.getGameDisplay().get_height()
        return width / 4, height * 0.10, width / 2, height * 0.32

    def getPlayerPanelRect(self):
        width = self.graphik.getGameDisplay().get_width()
        height = self.graphik.getGameDisplay().get_height()
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
        self.graphik.drawText(
            title, panelX + panelWidth / 2, panelY - 15, 20, (255, 255, 255)
        )
        self.graphik.drawRectangle(panelX, panelY, panelWidth, panelHeight, (0, 0, 0))
        for index, slot, itemX, itemY, itemWidth, itemHeight in self._slotGeometry(
            inventory, panelRect
        ):
            if slot.isEmpty():
                self.graphik.drawRectangle(
                    itemX, itemY, itemWidth, itemHeight, (255, 255, 255)
                )
                continue
            item = slot.getContents()[0]
            scaledImage = pygame.transform.scale(
                item.getImage(), (itemWidth, itemHeight)
            )
            self.graphik.gameDisplay.blit(scaledImage, (itemX, itemY))
            self.graphik.drawText(
                str(slot.getNumItems()),
                itemX + itemWidth - 20,
                itemY + itemHeight - 20,
                20,
                (255, 255, 255),
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
            takeScreenshot(self.graphik.getGameDisplay())

    def handleMouseClickEvent(self, pos, button=1):
        panels = (
            (self.getChestInventory(), self.getChestPanelRect()),
            (self.inventory, self.getPlayerPanelRect()),
        )
        for inventory, panelRect in panels:
            for index, slot, itemX, itemY, itemWidth, itemHeight in self._slotGeometry(
                inventory, panelRect
            ):
                if (
                    itemX < pos[0] < itemX + itemWidth
                    and itemY < pos[1] < itemY + itemHeight
                ):
                    if button in (1, 3):
                        self.swapCursorSlotWithSlot(slot)
                    return

        # drop cursor items when clicking outside both panels
        if self.cursorSlot.isEmpty():
            return
        if button == 2:  # middle mouse button drops a single item
            self.dropOneFromCursorSlot()
        elif button == 1:  # left mouse button drops the whole stack
            self.dropCursorSlot()

    def drawCursorSlot(self):
        if self.cursorSlot.isEmpty():
            return
        item = self.cursorSlot.getContents()[0]
        cursorX, cursorY = pygame.mouse.get_pos()
        scaledImage = pygame.transform.scale(item.getImage(), (50, 50))
        self.graphik.gameDisplay.blit(scaledImage, (cursorX, cursorY))
        count = self.cursorSlot.getNumItems()
        if count > 1:
            self.graphik.drawText(
                str(count), cursorX + 40, cursorY + 40, 18, (255, 255, 255)
            )

    def drawInstructions(self):
        playerPanelRect = self.getPlayerPanelRect()
        panelX, panelY, panelWidth, panelHeight = playerPanelRect
        closeKeyName = self.keyBindings.getKeyName("inventory").upper()
        self.graphik.drawText(
            "press [" + closeKeyName + "] or [Esc] to close",
            panelX + panelWidth / 2,
            panelY + panelHeight + 20,
            20,
            (255, 255, 255),
        )
        self.graphik.drawText(
            "Left-click: move item  -  click outside: drop",
            panelX + panelWidth / 2,
            panelY + panelHeight + 45,
            16,
            (180, 180, 180),
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
            self._drawPanel(self.getChestInventory(), self.getChestPanelRect(), "Chest")
            self._drawPanel(self.inventory, self.getPlayerPanelRect(), "Inventory")
            self.drawInstructions()
            self.drawCursorSlot()
            self.status.draw()
            pygame.display.update()

        # Return any held cursor items to the player so nothing is lost on close.
        if not self.cursorSlot.isEmpty():
            for item in self.cursorSlot.getContents():
                self.inventory.placeIntoFirstAvailableInventorySlot(item)
            self.cursorSlot.setContents([])

        if self.onClose is not None:
            self.onClose()

        self.changeScreen = False
        return self.nextScreen
