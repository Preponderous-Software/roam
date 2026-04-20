import threading
from concurrent.futures import ThreadPoolExecutor

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from mapimage.mapImageGenerator import MapImageGenerator
from world.tickCounter import TickCounter

_logger = getLogger(__name__)


# @author Daniel McCoy Stephenson
# @since February 2nd, 2023
@component
class MapImageUpdater:
    def __init__(self, tickCounter: TickCounter, config: Config):
        self.tickCounter = tickCounter
        self.config = config
        self.mapImageGenerator = MapImageGenerator(self.config)
        self.tickLastUpdated = self.tickCounter.getTick()
        self.updateCooldownInTicks = 300
        self._executor = ThreadPoolExecutor(
            max_workers=1
        )  # serialize map updates to avoid concurrent Pillow operations
        self._updateInProgress = False
        self._lock = threading.Lock()
        self.roompngsLock = (
            threading.Lock()
        )  # shared with WorldScreen to synchronize roompngs access

    def updateIfCooldownOver(self):
        if (
            self.tickCounter.getTick() - self.tickLastUpdated
            > self.updateCooldownInTicks
        ):
            self.updateMapImageAsync()

    def updateMapImageAsync(self):
        """Submit a map image update to run in the background.
        Skips if an update is already in progress."""
        with self._lock:
            if self._updateInProgress:
                return
            self._updateInProgress = True
        self.tickLastUpdated = self.tickCounter.getTick()
        self._executor.submit(self._doUpdateMapImage)
        _logger.info("map image update started")

    def updateMapImage(self):
        """Run a map image update in the background (non-blocking)."""
        self.updateMapImageAsync()

    def _doUpdateMapImage(self):
        """Perform the actual map image generation. Runs on a background thread."""
        try:
            with self.roompngsLock:
                image = self.mapImageGenerator.generate()
                image.save(self.mapImageGenerator.mapImagePath)
                self.mapImageGenerator.clearRoomImages()
            _logger.info("map image update completed")
        except Exception:
            _logger.exception("error updating map image")
        finally:
            with self._lock:
                self._updateInProgress = False

    def shutdown(self, wait=False):
        """Cleanly shut down the background thread pool and recreate it so the
        same MapImageUpdater instance can be reused after a screen transition."""
        self._executor.shutdown(wait=wait)
        self._executor = ThreadPoolExecutor(max_workers=1)
