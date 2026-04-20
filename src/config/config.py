# @author Daniel McCoy Stephenson
# @since August 6th, 2022
from pathlib import Path

import pygame

from gameLogging.logger import getLogger

_logger = getLogger(__name__)


class Config:
    @staticmethod
    def getConfigFilePath():
        return Path(__file__).resolve().parents[2] / "config.yml"

    @staticmethod
    def parseConfigValue(value):
        value = value.strip()
        if value == "":
            return None
        lowerValue = value.lower()
        if lowerValue == "true":
            return True
        if lowerValue == "false":
            return False
        if lowerValue == "none" or lowerValue == "null":
            return None
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            listText = value[1:-1].strip()
            if listText == "":
                return []
            return [
                Config.parseConfigValue(item.strip()) for item in listText.split(",")
            ]
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            return value

    @classmethod
    def readConfigFile(cls):
        configValues = {}
        configFilePath = cls.getConfigFilePath()
        if not configFilePath.exists():
            return configValues
        try:
            with configFilePath.open("r", encoding="utf-8") as configFile:
                for line in configFile:
                    strippedLine = line.strip()
                    if strippedLine == "" or strippedLine.startswith("#"):
                        continue
                    keyAndValue = strippedLine.split(":", 1)
                    if len(keyAndValue) != 2:
                        continue
                    key = keyAndValue[0].strip()
                    value = cls.removeInlineComment(keyAndValue[1]).strip()
                    configValues[key] = cls.parseConfigValue(value)
        except (OSError, UnicodeDecodeError):
            return configValues
        return configValues

    @staticmethod
    def removeInlineComment(value):
        quoteCharacter = None

        def isEscapedQuote(index):
            backslashCount = 0
            currentIndex = index - 1
            while currentIndex >= 0 and value[currentIndex] == "\\":
                backslashCount += 1
                currentIndex -= 1
            return backslashCount % 2 == 1

        for i, character in enumerate(value):
            if character in ('"', "'") and not isEscapedQuote(i):
                if quoteCharacter is None:
                    quoteCharacter = character
                elif quoteCharacter == character:
                    quoteCharacter = None
            elif character == "#" and quoteCharacter is None:
                return value[:i]
        return value

    @staticmethod
    def getBoolValue(configValues, key, default):
        value = configValues.get(key)
        if isinstance(value, bool):
            return value
        return default

    @staticmethod
    def getIntValue(configValues, key, default):
        value = configValues.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        return default

    @staticmethod
    def getFloatValue(configValues, key, default):
        value = configValues.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return default

    @staticmethod
    def getStringValue(configValues, key, default):
        value = configValues.get(key)
        if isinstance(value, str) and value.strip() != "":
            return value
        return default

    @staticmethod
    def getColorValue(configValues, key, default):
        value = configValues.get(key)
        if not isinstance(value, (list, tuple)):
            return default
        if len(value) != len(default):
            return default

        colorValues = []
        for colorValue in value:
            if isinstance(colorValue, bool) or not isinstance(colorValue, int):
                return default
            if colorValue < 0 or colorValue > 255:
                return default
            colorValues.append(colorValue)
        return tuple(colorValues)

    MIN_WINDOW_SIZE = 400

    def __init__(self):
        configValues = self.readConfigFile()
        screenHeight = pygame.display.Info().current_h
        displayDimensionDefault = screenHeight * 0.90

        # Resolve effective display dimensions: manual displayWidth /
        # displayHeight take priority, then savedWindowWidth /
        # savedWindowHeight, then the computed default.
        savedW = configValues.get("savedWindowWidth")
        savedH = configValues.get("savedWindowHeight")
        if (
            isinstance(savedW, (int, float))
            and not isinstance(savedW, bool)
            and isinstance(savedH, (int, float))
            and not isinstance(savedH, bool)
        ):
            savedW = float(savedW)
            savedH = float(savedH)
            savedW = max(savedW, self.MIN_WINDOW_SIZE)
            savedH = max(savedH, self.MIN_WINDOW_SIZE)
            screenWidth = pygame.display.Info().current_w
            if savedW <= screenWidth and savedH <= screenHeight:
                displayDimensionDefaultW = savedW
                displayDimensionDefaultH = savedH
            else:
                displayDimensionDefaultW = displayDimensionDefault
                displayDimensionDefaultH = displayDimensionDefault
        else:
            displayDimensionDefaultW = displayDimensionDefault
            displayDimensionDefaultH = displayDimensionDefault

        # static (cannot be changed in game)
        self.displayWidth = self.getFloatValue(
            configValues, "displayWidth", displayDimensionDefaultW
        )
        self.displayHeight = self.getFloatValue(
            configValues, "displayHeight", displayDimensionDefaultH
        )
        self.black = self.getColorValue(configValues, "black", (0, 0, 0))
        self.white = self.getColorValue(configValues, "white", (255, 255, 255))
        self.playerMovementEnergyCost = self.getFloatValue(
            configValues, "playerMovementEnergyCost", 0.2
        )
        self.playerInteractionEnergyCost = self.getFloatValue(
            configValues, "playerInteractionEnergyCost", 0.05
        )
        self.runSpeedFactor = self.getFloatValue(configValues, "runSpeedFactor", 2)
        self.energyDepletionRate = self.getFloatValue(
            configValues, "energyDepletionRate", 0.01
        )
        self.playerInteractionDistanceLimit = self.getIntValue(
            configValues, "playerInteractionDistanceLimit", 5
        )
        self.ticksPerSecond = self.getIntValue(configValues, "ticksPerSecond", 30)
        self.gridSize = self.getIntValue(configValues, "gridSize", 17)
        self.worldBorder = self.getIntValue(
            configValues, "worldBorder", 0
        )  # 0 = no border
        self.excrementDecayTicks = self.getIntValue(
            configValues, "excrementDecayTicks", 30 * 60 * 2
        )  # 2 minutes at 30 tps
        self.cropGrowthTicks = self.getIntValue(
            configValues, "cropGrowthTicks", 1800
        )  # 1 minute per stage at 30 tps
        self.pathToSaveDirectory = self.getStringValue(
            configValues, "pathToSaveDirectory", "saves/defaultsavefile"
        )

        # dynamic (can be changed in game)
        self.debug = self.getBoolValue(configValues, "debug", True)
        self.fullscreen = self.getBoolValue(configValues, "fullscreen", False)
        self.autoEatFoodInInventory = self.getBoolValue(
            configValues, "autoEatFoodInInventory", True
        )
        self.removeDeadEntities = self.getBoolValue(
            configValues, "removeDeadEntities", True
        )
        self.showMiniMap = self.getBoolValue(configValues, "showMiniMap", True)
        self.cameraFollowPlayer = self.getBoolValue(
            configValues, "cameraFollowPlayer", True
        )
        self.limitTps = self.getBoolValue(configValues, "limitTps", True)
        self.pushableStone = self.getBoolValue(configValues, "pushableStone", True)

        _logger.debug(
            "config loaded",
            displayWidth=self.displayWidth,
            displayHeight=self.displayHeight,
            ticksPerSecond=self.ticksPerSecond,
            gridSize=self.gridSize,
            worldBorder=self.worldBorder,
            fullscreen=self.fullscreen,
            debug=self.debug,
        )

    def saveWindowSize(self, width, height):
        width = max(int(width), self.MIN_WINDOW_SIZE)
        height = max(int(height), self.MIN_WINDOW_SIZE)
        configFilePath = self.getConfigFilePath()
        lines = []
        if configFilePath.exists():
            try:
                lines = configFilePath.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                lines = []

        savedValues = {
            "savedWindowWidth": str(width),
            "savedWindowHeight": str(height),
        }
        updatedKeys = set()
        newLines = []
        for line in lines:
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#"):
                newLines.append(line)
                continue
            parts = stripped.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                if key in savedValues:
                    newLines.append(key + ": " + savedValues[key])
                    updatedKeys.add(key)
                    continue
            newLines.append(line)

        for key, value in savedValues.items():
            if key not in updatedKeys:
                newLines.append(key + ": " + value)

        try:
            configFilePath.write_text("\n".join(newLines) + "\n", encoding="utf-8")
        except OSError:
            pass
