# @author Daniel McCoy Stephenson
# @since August 6th, 2022
from pathlib import Path

import pygame


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
        if (
            (value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))
        ):
            return value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            listText = value[1:-1].strip()
            if listText == "":
                return []
            return [Config.parseConfigValue(item.strip()) for item in listText.split(",")]
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

    def __init__(self):
        configValues = self.readConfigFile()
        displayDimensionDefault = pygame.display.Info().current_h * 0.90

        # static (cannot be changed in game)
        self.displayWidth = self.getFloatValue(
            configValues, "displayWidth", displayDimensionDefault
        )
        self.displayHeight = self.getFloatValue(
            configValues, "displayHeight", displayDimensionDefault
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
        self.worldBorder = self.getIntValue(configValues, "worldBorder", 0)  # 0 = no border
        self.excrementDecayTicks = self.getIntValue(
            configValues, "excrementDecayTicks", 30 * 60 * 2
        )  # 2 minutes at 30 tps
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
        self.vsync = self.getBoolValue(configValues, "vsync", True)
