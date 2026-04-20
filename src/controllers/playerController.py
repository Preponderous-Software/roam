# @author Copilot
# @since April 20th, 2026
import pygame

from appContainer import component
from config.config import Config
from config.keyBindings import KeyBindings
from gameLogging.logger import getLogger
from player.player import Player
from screen.screenType import ScreenType
from screen.screenshotHelper import takeScreenshot
from services.inventoryService import InventoryService
from services.movementService import MovementService
from lib.graphik.src.graphik import Graphik

_logger = getLogger(__name__)


@component
class PlayerController:
    """Routes player input to the appropriate services."""

    def __init__(
        self,
        config: Config,
        player: Player,
        keyBindings: KeyBindings,
        movementService: MovementService,
        inventoryService: InventoryService,
        graphik: Graphik,
    ):
        self.config = config
        self.player = player
        self.keyBindings = keyBindings
        self.movementService = movementService
        self.inventoryService = inventoryService
        self.graphik = graphik

    def handleMovementKey(self, direction, currentRoom, map, worldService, save_callback=None):
        self.player.setDirection(direction)
        if self.movementService.checkPlayerMovementCooldown(
            self.player.getTickLastMoved()
        ):
            return self.movementService.movePlayer(
                self.player.direction, currentRoom, map, worldService, save_callback
            )
        return currentRoom

    def handleKeyDownEvent(
        self, key, currentRoom, map, worldService, save_callback=None
    ):
        """Handle a key-down event. Returns updated currentRoom."""
        kb = self.keyBindings
        if key == kb.getKey("move_up") or key == kb.getKey("alt_move_up"):
            return self.handleMovementKey(
                0, currentRoom, map, worldService, save_callback
            )
        elif key == kb.getKey("move_left") or key == kb.getKey("alt_move_left"):
            return self.handleMovementKey(
                1, currentRoom, map, worldService, save_callback
            )
        elif key == kb.getKey("move_down") or key == kb.getKey("alt_move_down"):
            return self.handleMovementKey(
                2, currentRoom, map, worldService, save_callback
            )
        elif key == kb.getKey("move_right") or key == kb.getKey("alt_move_right"):
            return self.handleMovementKey(
                3, currentRoom, map, worldService, save_callback
            )
        elif key == kb.getKey("screenshot"):
            takeScreenshot(self.graphik.getGameDisplay())
        elif key == kb.getKey("run"):
            self.player.setMovementSpeed(
                self.player.getMovementSpeed() * self.config.runSpeedFactor
            )
        elif key == kb.getKey("crouch"):
            self.player.setCrouching(True)
        else:
            self._handleHotbarKey(key)
        return currentRoom

    def handleKeyUpEvent(self, key):
        kb = self.keyBindings
        if (
            key == kb.getKey("move_up") or key == kb.getKey("alt_move_up")
        ) and self.player.getDirection() == 0:
            self.player.setDirection(-1)
        elif (
            key == kb.getKey("move_left") or key == kb.getKey("alt_move_left")
        ) and self.player.getDirection() == 1:
            self.player.setDirection(-1)
        elif (
            key == kb.getKey("move_down") or key == kb.getKey("alt_move_down")
        ) and self.player.getDirection() == 2:
            self.player.setDirection(-1)
        elif (
            key == kb.getKey("move_right") or key == kb.getKey("alt_move_right")
        ) and self.player.getDirection() == 3:
            self.player.setDirection(-1)
        elif key == kb.getKey("run"):
            self.player.setMovementSpeed(
                self.player.getMovementSpeed() / self.config.runSpeedFactor
            )
        elif key == kb.getKey("crouch"):
            self.player.setCrouching(False)

    def _handleHotbarKey(self, key):
        kb = self.keyBindings
        hotbarKeys = [
            (kb.getKey("hotbar_1"), 0),
            (kb.getKey("hotbar_2"), 1),
            (kb.getKey("hotbar_3"), 2),
            (kb.getKey("hotbar_4"), 3),
            (kb.getKey("hotbar_5"), 4),
            (kb.getKey("hotbar_6"), 5),
            (kb.getKey("hotbar_7"), 6),
            (kb.getKey("hotbar_8"), 7),
            (kb.getKey("hotbar_9"), 8),
            (kb.getKey("hotbar_0"), 9),
        ]
        for hotbarKey, index in hotbarKeys:
            if key == hotbarKey:
                self.inventoryService.changeSelectedInventorySlot(index)
                return True
        return False
