# @author Daniel McCoy Stephenson
# @since August 6th, 2022
import os
import shutil
import sys

import pygame

from appPaths import getBundleDirectory
from gameLogging.logger import getLogger

_logger = getLogger(__name__)


class Config:
    @staticmethod
    def getVersion():
        # The build's version string, read from the bundled version.txt (which
        # is the repository root from source and the PyInstaller bundle when
        # frozen). Returns "unknown" if the file is missing.
        versionPath = os.path.join(getBundleDirectory(), "version.txt")
        try:
            with open(versionPath, "r", encoding="utf-8") as versionFile:
                return versionFile.read().strip()
        except OSError:
            return "unknown"

    @staticmethod
    def getUserDataDirectory():
        # Writable per-user directory for config and screenshots. On Windows
        # this is %APPDATA%\Roam and on macOS ~/Library/Application Support/Roam,
        # so writes succeed even when the game is installed to a read-only
        # location (Program Files, /Applications). Other platforms use the
        # repository/bundle root (the current from-source behavior). (Saves have
        # their own getSavesBaseDirectory, which resolves the same way.)
        if os.name == "nt":
            appData = os.environ.get("APPDATA")
            if appData:
                return os.path.join(appData, "Roam")
        elif sys.platform == "darwin":
            return os.path.join(
                os.path.expanduser("~"), "Library", "Application Support", "Roam"
            )
        return getBundleDirectory()

    @staticmethod
    def getBundledConfigFilePath():
        # The config.yml shipped with the app (read-only when frozen). Uses
        # os.path (not pathlib) so it stays correct under os.name monkeypatching
        # in cross-platform tests.
        return os.path.join(getBundleDirectory(), "config.yml")

    @staticmethod
    def getConfigFilePath():
        # The user's read/write config file, in the writable user-data
        # directory. From source this resolves to the repository root, matching
        # the previous behavior.
        return os.path.join(Config.getUserDataDirectory(), "config.yml")

    @staticmethod
    def ensureUserConfigExists():
        # On first run, seed the writable user config from the bundled defaults
        # so shipped settings are preserved and the file is writable. No-op when
        # the user config and the bundled config are the same file (from source)
        # or the user config already exists.
        userConfig = Config.getConfigFilePath()
        bundled = Config.getBundledConfigFilePath()
        if str(userConfig) == str(bundled) or os.path.exists(userConfig):
            return
        if os.path.exists(bundled):
            os.makedirs(os.path.dirname(userConfig), exist_ok=True)
            shutil.copyfile(bundled, userConfig)

    @staticmethod
    def getSavesBaseDirectory():
        # The single source of truth for where save folders live. On Windows we
        # store them under %APPDATA% (e.g. C:\Users\<you>\AppData\Roaming\Roam\saves)
        # and on macOS under ~/Library/Application Support/Roam/saves, so saves
        # live with the user rather than in a possibly read-only install
        # directory (Program Files, /Applications). Other platforms keep the
        # repository-relative "saves" directory.
        if os.name == "nt":
            appData = os.environ.get("APPDATA")
            if appData:
                return os.path.join(appData, "Roam", "saves")
        elif sys.platform == "darwin":
            return os.path.join(Config.getUserDataDirectory(), "saves")
        return "saves"

    @staticmethod
    def getDefaultSaveDirectory():
        # The default save slot, used when config.yml does not pin
        # pathToSaveDirectory explicitly.
        return os.path.join(Config.getSavesBaseDirectory(), "defaultsavefile")

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
        if not os.path.exists(configFilePath):
            return configValues
        try:
            with open(configFilePath, "r", encoding="utf-8") as configFile:
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
        self.ensureUserConfigExists()
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
            configValues, "pathToSaveDirectory", Config.getDefaultSaveDirectory()
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
        self.dayNightCycleEnabled = self.getBoolValue(
            configValues, "dayNightCycleEnabled", True
        )
        self.dayNightCycleLengthTicks = self.getIntValue(
            configValues,
            "dayNightCycleLengthTicks",
            self.ticksPerSecond * 30 * 60,
        )  # 30 minutes at the configured ticksPerSecond
        self.pushableStone = self.getBoolValue(configValues, "pushableStone", True)
        self.checkForUpdates = self.getBoolValue(configValues, "checkForUpdates", True)

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

    def getRoomsDirectory(self):
        """Return the directory holding per-room JSON files: the single source
        of truth for the `<saveDir>/rooms` location."""
        return self.pathToSaveDirectory + "/rooms"

    def getRoomFilePath(self, x, y):
        """Return the path to a room's JSON save file, built on top of
        getRoomsDirectory so the `/rooms` layout lives in one place."""
        return self.getRoomsDirectory() + "/room_" + str(x) + "_" + str(y) + ".json"

    def _writeKeyValues(self, savedValues, errorMessage):
        configFilePath = self.getConfigFilePath()
        lines = []
        if os.path.exists(configFilePath):
            try:
                with open(configFilePath, "r", encoding="utf-8") as configFile:
                    lines = configFile.read().splitlines()
            except (OSError, UnicodeDecodeError):
                lines = []

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
            with open(configFilePath, "w", encoding="utf-8") as configFile:
                configFile.write("\n".join(newLines) + "\n")
        except OSError as e:
            _logger.warning(
                errorMessage,
                error=str(e),
                path=str(configFilePath),
            )

    def saveWindowSize(self, width, height):
        width = max(int(width), self.MIN_WINDOW_SIZE)
        height = max(int(height), self.MIN_WINDOW_SIZE)
        savedValues = {
            "savedWindowWidth": str(width),
            "savedWindowHeight": str(height),
        }
        self._writeKeyValues(savedValues, "failed to save window size to config file")
