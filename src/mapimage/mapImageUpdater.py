import threading
from concurrent.futures import ThreadPoolExecutor

from appContainer import component
from config.config import Config
from mapimage.mapImageGenerator import MapImageGenerator
from world.tickCounter import TickCounter


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
        self._executor = ThreadPoolExecutor(max_workers=1)  # serialize map updates to avoid concurrent Pillow operations
        self._updateInProgress = False
        self._lock = threading.Lock()

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

    def updateMapImage(self):
        """Run a map image update in the background (non-blocking)."""
        self.updateMapImageAsync()

    def _doUpdateMapImage(self):
        """Perform the actual map image generation. Runs on a background thread."""
        try:
            image = self.mapImageGenerator.generate()
            image.save(self.mapImageGenerator.mapImagePath)
            self.mapImageGenerator.clearRoomImages()
        except Exception as e:
            print("Error updating map image: " + str(e))
        finally:
            with self._lock:
                self._updateInProgress = False

    def shutdown(self, wait=False):
        """Cleanly shut down the background thread pool."""
        self._executor.shutdown(wait=wait)
