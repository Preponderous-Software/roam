# @author Copilot
# @since April 20th, 2026
import time

import pygame

from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from crafting.recipeRegistry import RecipeRegistry
from gameLogging.logger import getLogger
from inventory.inventorySlot import InventorySlot
from lib.graphik.src.graphik import Graphik
from player.player import Player
from screen.screenshotHelper import takeScreenshot
from services.craftingService import CraftingService
from ui.status import Status

_logger = getLogger(__name__)


@component
class InventoryController:
    """Routes inventory interactions including slot management and crafting."""

    def __init__(
        self,
        graphik: Graphik,
        config: Config,
        player: Player,
        status: Status,
        keyBindings: KeyBindings,
        craftingService: CraftingService,
    ):
        self.graphik = graphik
        self.config = config
        self.player = player
        self.status = status
        self.keyBindings = keyBindings
        self.craftingService = craftingService
        self.cursorSlot = InventorySlot()
        self.craftPanelOpen = False
        self.recipeRegistry = RecipeRegistry()
        self.lastCraftToggleTime = 0

    def getInventory(self):
        return self.player.getInventory()

    def swapCursorSlotWithInventorySlotByIndex(self, index):
        inventory = self.getInventory()
        destSlot = inventory.getInventorySlots()[index]
        if self.cursorSlot.isEmpty():
            self.cursorSlot.setContents(destSlot.getContents())
            destSlot.setContents([])
        elif (
            not destSlot.isEmpty()
            and self.cursorSlot.getContents()[0].getName()
            == destSlot.getContents()[0].getName()
        ):
            inventory.mergeIntoSlot(self.cursorSlot, destSlot)
        else:
            temp = destSlot.getContents()
            destSlot.setContents(self.cursorSlot.getContents())
            self.cursorSlot.setContents(temp)

    def handleKeyDownEvent(self, key):
        kb = self.keyBindings
        if key == kb.getKey("screenshot"):
            takeScreenshot(self.graphik.getGameDisplay())
            return
        hotbarMap = [
            ("hotbar_1", 0),
            ("hotbar_2", 1),
            ("hotbar_3", 2),
            ("hotbar_4", 3),
            ("hotbar_5", 4),
            ("hotbar_6", 5),
            ("hotbar_7", 6),
            ("hotbar_8", 7),
            ("hotbar_9", 8),
            ("hotbar_0", 9),
        ]
        for bindingName, index in hotbarMap:
            if key == kb.getKey(bindingName):
                self.swapCursorSlotWithInventorySlotByIndex(index)
                return

    def toggleCraftPanel(self):
        now = time.time()
        if now - self.lastCraftToggleTime < 1:
            return
        self.lastCraftToggleTime = now
        self.craftPanelOpen = not self.craftPanelOpen

    def craftRecipe(self, recipe):
        self.craftingService.craftRecipe(recipe, self.getInventory())

    def handleMouseClickEvent(self, pos, button=1):
        inventory = self.getInventory()
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        itemsPerRow = 5
        row = 0
        column = 0
        margin = 5
        clickedSlot = False
        for inventorySlot in inventory.getInventorySlots():
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
                clickedSlot = True
                index = row * itemsPerRow + column

                if button == 3:
                    inventory.setSelectedInventorySlotIndex(index)
                    return

                if (
                    not self.cursorSlot.isEmpty()
                    and not inventorySlot.isEmpty()
                    and self.cursorSlot.getContents()[0].getName()
                    == inventorySlot.getContents()[0].getName()
                ):
                    inventory.mergeIntoSlot(self.cursorSlot, inventorySlot)
                else:
                    inventorySlotContents = inventorySlot.getContents()
                    cursorSlotContents = self.cursorSlot.getContents()
                    inventorySlot.setContents(cursorSlotContents)
                    self.cursorSlot.setContents(inventorySlotContents)

            column += 1
            if column == itemsPerRow:
                column = 0
                row += 1

        if not clickedSlot and not self._isInsideInventoryPanel(pos):
            if self._isInsideBackButton(pos) or self._isInsideCraftButton(pos):
                return
            if self._isInsideCraftPanel(pos):
                return
            if not self.cursorSlot.isEmpty():
                if button == 2:
                    self.cursorSlot.pop()
                elif button == 1:
                    self.cursorSlot.clear()

    def _isInsideInventoryPanel(self, pos):
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

    def _isInsideBackButton(self, pos):
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

    def _isInsideCraftButton(self, pos):
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

    def _isInsideCraftPanel(self, pos):
        if not self.craftPanelOpen:
            return False
        backgroundX = self.graphik.getGameDisplay().get_width() / 4
        backgroundY = self.graphik.getGameDisplay().get_height() / 4
        backgroundWidth = self.graphik.getGameDisplay().get_width() / 2
        backgroundHeight = self.graphik.getGameDisplay().get_height() / 2
        panelX = backgroundX + backgroundWidth + 10
        panelY = backgroundY
        panelWidth = backgroundWidth * 0.6
        panelHeight = backgroundHeight
        return (
            pos[0] >= panelX
            and pos[0] <= panelX + panelWidth
            and pos[1] >= panelY
            and pos[1] <= panelY + panelHeight
        )
