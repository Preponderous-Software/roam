import os
import threading
from concurrent.futures import ThreadPoolExecutor

from config.config import Config
from lib.graphik.src.graphik import Graphik
from world.map import Map
from world.tickCounter import TickCounter


# @author Copilot
# @since April 19th, 2026
class RoomPreloader:
    """Asynchronously pre-loads or generates rooms adjacent to the player's
    current position so that room transitions feel instant."""

    NEIGHBOR_OFFSETS = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def __init__(
        self,
        gridSize,
        graphik: Graphik,
        tickCounter: TickCounter,
        config: Config,
        roomJsonReaderWriterFactory=None,
    ):
        self.gridSize = gridSize
        self.graphik = graphik
        self.tickCounter = tickCounter
        self.config = config
        self._roomJsonReaderWriterFactory = roomJsonReaderWriterFactory
        self._executor = ThreadPoolExecutor(max_workers=2)  # balance responsiveness with resource usage
        self._pending = set()
        self._pendingLock = threading.Lock()

    def preloadNearbyRooms(self, currentX, currentY, gameMap: Map):
        """Submit background tasks to load/generate the four rooms adjacent
        to (currentX, currentY) that are not already loaded."""
        for dx, dy in self.NEIGHBOR_OFFSETS:
            nx, ny = currentX + dx, currentY + dy

            if self.config.worldBorder != 0 and (
                abs(nx) > self.config.worldBorder
                or abs(ny) > self.config.worldBorder
            ):
                continue

            with self._pendingLock:
                if (nx, ny) in self._pending:
                    continue
                self._pending.add((nx, ny))

            if gameMap.hasRoom(nx, ny):
                with self._pendingLock:
                    self._pending.discard((nx, ny))
                continue

            self._executor.submit(self._loadOrGenerate, nx, ny, gameMap)

    def _loadOrGenerate(self, x, y, gameMap: Map):
        """Load a room from disk or generate a new one, then add it to the
        map.  Runs on a background thread."""
        try:
            # Double-check the room was not loaded while queued
            if gameMap.hasRoom(x, y):
                return

            nextRoomPath = (
                self.config.pathToSaveDirectory
                + "/rooms/room_"
                + str(x)
                + "_"
                + str(y)
                + ".json"
            )
            if os.path.exists(nextRoomPath):
                roomJsonReaderWriter = self._roomJsonReaderWriterFactory()
                room = roomJsonReaderWriter.loadRoom(nextRoomPath)
                gameMap.addRoom(room)
            else:
                gameMap.generateNewRoom(x, y)
        finally:
            with self._pendingLock:
                self._pending.discard((x, y))

    def shutdown(self, wait=False):
        """Cleanly shut down the background thread pool."""
        self._executor.shutdown(wait=wait)
