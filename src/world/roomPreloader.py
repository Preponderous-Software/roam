import os
import threading
from concurrent.futures import ThreadPoolExecutor

from config.config import Config
from gameLogging.logger import getLogger
from rendering.renderer import Renderer
from world.map import Map
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


# @author Copilot
# @since April 19th, 2026
class RoomPreloader:
    """Asynchronously pre-loads or generates rooms adjacent to the player's
    current position so that room transitions feel instant."""

    NEIGHBOR_OFFSETS = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    def __init__(
        self,
        gridSize,
        renderer: Renderer,
        tickCounter: TickCounter,
        config: Config,
        roomJsonReaderWriterFactory=None,
    ):
        self.gridSize = gridSize
        self.renderer = renderer
        self.tickCounter = tickCounter
        self.config = config
        self._roomJsonReaderWriterFactory = roomJsonReaderWriterFactory
        self._executor = ThreadPoolExecutor(
            max_workers=2
        )  # balance responsiveness with resource usage
        self._pending = set()
        self._pendingLock = threading.Lock()

    def preloadNearbyRooms(self, currentX, currentY, gameMap: Map, z=0):
        """Submit background tasks to load/generate the four rooms adjacent
        to (currentX, currentY) that are not already loaded."""
        for dx, dy in self.NEIGHBOR_OFFSETS:
            nx, ny = currentX + dx, currentY + dy

            if self.config.worldBorder != 0 and (
                abs(nx) > self.config.worldBorder or abs(ny) > self.config.worldBorder
            ):
                continue

            key = (nx, ny, z)
            with self._pendingLock:
                if key in self._pending:
                    continue
                self._pending.add(key)

            if gameMap.hasRoom(nx, ny, z):
                with self._pendingLock:
                    self._pending.discard(key)
                continue

            self._executor.submit(self._loadOrGenerate, nx, ny, z, gameMap)

    def _loadOrGenerate(self, x, y, z, gameMap: Map):
        """Load a room from disk or generate a new one, then add it to the
        map.  Runs on a background thread."""
        key = (x, y, z)
        try:
            if gameMap.hasRoom(x, y, z):
                return

            nextRoomPath = self.config.getRoomFilePath(x, y, z)
            if os.path.exists(nextRoomPath):
                roomJsonReaderWriter = self._roomJsonReaderWriterFactory()
                room = roomJsonReaderWriter.loadRoom(nextRoomPath)
                gameMap.addRoom(room)
                _logger.debug("preloaded room from file", roomX=x, roomY=y, roomZ=z)
            else:
                gameMap.generateNewRoom(x, y, z)
                _logger.debug(
                    "preloaded room via generation", roomX=x, roomY=y, roomZ=z
                )
        except Exception:
            _logger.exception("room preload failed", roomX=x, roomY=y, roomZ=z)
        finally:
            with self._pendingLock:
                self._pending.discard(key)

    def shutdown(self, wait=False):
        """Cleanly shut down the background thread pool and recreate it so the
        same RoomPreloader instance can be reused after a screen transition."""
        self._executor.shutdown(wait=wait)
        self._executor = ThreadPoolExecutor(max_workers=2)
