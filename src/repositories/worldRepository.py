# @author Copilot
# @since April 20th, 2026
import json
import os

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from world.roomJsonReaderWriter import RoomJsonReaderWriter

_logger = getLogger(__name__)


@component
class WorldRepository:
    """Handles all persistence for world/room data."""

    def __init__(self, config: Config, roomJsonReaderWriter: RoomJsonReaderWriter):
        self.config = config
        self.roomJsonReaderWriter = roomJsonReaderWriter

    def buildRoomPath(self, roomX, roomY):
        return (
            self.config.pathToSaveDirectory
            + "/rooms/room_"
            + str(roomX)
            + "_"
            + str(roomY)
            + ".json"
        )

    def saveRoom(self, room):
        roomPath = self.buildRoomPath(room.getX(), room.getY())
        _logger.info("saving room", path=roomPath)
        if not os.path.exists(self.config.pathToSaveDirectory + "/rooms"):
            os.makedirs(self.config.pathToSaveDirectory + "/rooms")

        jsonRoom = self.roomJsonReaderWriter.generateJsonForRoom(room)
        with open(roomPath, "w") as outfile:
            json.dump(jsonRoom, outfile, indent=4)

    def saveRoomJson(self, roomJson, roomPath):
        """Write a pre-built JSON dict to disk."""
        try:
            dirPath = os.path.dirname(roomPath)
            if not os.path.exists(dirPath):
                os.makedirs(dirPath, exist_ok=True)
            with open(roomPath, "w") as outfile:
                json.dump(roomJson, outfile, indent=4)
        except Exception as e:
            _logger.error("error writing room JSON file", error=str(e), path=roomPath)
