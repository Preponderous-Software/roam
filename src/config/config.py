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
        with configFilePath.open("r", encoding="utf-8") as configFile:
            for line in configFile:
                strippedLine = line.strip()
                if strippedLine == "" or strippedLine.startswith("#"):
                    continue
                keyAndValue = strippedLine.split(":", 1)
                if len(keyAndValue) != 2:
                    continue
                key = keyAndValue[0].strip()
                value = keyAndValue[1].split("#", 1)[0].strip()
                configValues[key] = cls.parseConfigValue(value)
        return configValues

    def __init__(self):
        configValues = self.readConfigFile()
        displaySizeDefault = pygame.display.Info().current_h * 0.90

        # static (cannot be changed in game)
        self.displayWidth = configValues.get("displayWidth", displaySizeDefault)
        self.displayHeight = configValues.get("displayHeight", displaySizeDefault)
        self.black = tuple(configValues.get("black", (0, 0, 0)))
        self.white = tuple(configValues.get("white", (255, 255, 255)))
        self.playerMovementEnergyCost = configValues.get("playerMovementEnergyCost", 0.2)
        self.playerInteractionEnergyCost = configValues.get("playerInteractionEnergyCost", 0.05)
        self.runSpeedFactor = configValues.get("runSpeedFactor", 2)
        self.energyDepletionRate = configValues.get("energyDepletionRate", 0.01)
        self.playerInteractionDistanceLimit = configValues.get("playerInteractionDistanceLimit", 5)
        self.ticksPerSecond = configValues.get("ticksPerSecond", 30)
        self.gridSize = configValues.get("gridSize", 17)
        self.worldBorder = configValues.get("worldBorder", 0)  # 0 = no border
        self.excrementDecayTicks = configValues.get("excrementDecayTicks", 30 * 60 * 2)  # 2 minutes at 30 tps
        self.pathToSaveDirectory = configValues.get("pathToSaveDirectory", "saves/defaultsavefile")

        # dynamic (can be changed in game)
        self.debug = configValues.get("debug", True)
        self.fullscreen = configValues.get("fullscreen", False)
        self.autoEatFoodInInventory = configValues.get("autoEatFoodInInventory", True)
        self.removeDeadEntities = configValues.get("removeDeadEntities", True)
        self.showMiniMap = configValues.get("showMiniMap", True)
        self.cameraFollowPlayer = configValues.get("cameraFollowPlayer", True)
