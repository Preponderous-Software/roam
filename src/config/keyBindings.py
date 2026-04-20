import pygame


# @author Copilot
# @since April 19th, 2026
class KeyBindings:
    """Manages keybinding defaults, remapping, conflict detection, and persistence."""

    DEFAULT_BINDINGS = {
        "move_up": pygame.K_w,
        "move_left": pygame.K_a,
        "move_down": pygame.K_s,
        "move_right": pygame.K_d,
        "alt_move_up": pygame.K_UP,
        "alt_move_left": pygame.K_LEFT,
        "alt_move_down": pygame.K_DOWN,
        "alt_move_right": pygame.K_RIGHT,
        "run": pygame.K_LSHIFT,
        "crouch": pygame.K_LCTRL,
        "inventory": pygame.K_i,
        "hotbar_1": pygame.K_1,
        "hotbar_2": pygame.K_2,
        "hotbar_3": pygame.K_3,
        "hotbar_4": pygame.K_4,
        "hotbar_5": pygame.K_5,
        "hotbar_6": pygame.K_6,
        "hotbar_7": pygame.K_7,
        "hotbar_8": pygame.K_8,
        "hotbar_9": pygame.K_9,
        "hotbar_0": pygame.K_0,
        "toggle_minimap": pygame.K_m,
        "minimap_zoom_in": pygame.K_EQUALS,
        "minimap_zoom_out": pygame.K_MINUS,
        "screenshot": pygame.K_PRINTSCREEN,
        "toggle_camera_follow": pygame.K_c,
        "toggle_debug": pygame.K_F3,
        "toggle_help": pygame.K_F1,
        "codex": pygame.K_l,
    }

    ACTION_LABELS = {
        "move_up": "Move Up",
        "move_left": "Move Left",
        "move_down": "Move Down",
        "move_right": "Move Right",
        "alt_move_up": "Move Up (Alt)",
        "alt_move_left": "Move Left (Alt)",
        "alt_move_down": "Move Down (Alt)",
        "alt_move_right": "Move Right (Alt)",
        "run": "Run",
        "crouch": "Crouch",
        "inventory": "Inventory",
        "hotbar_1": "Hotbar 1",
        "hotbar_2": "Hotbar 2",
        "hotbar_3": "Hotbar 3",
        "hotbar_4": "Hotbar 4",
        "hotbar_5": "Hotbar 5",
        "hotbar_6": "Hotbar 6",
        "hotbar_7": "Hotbar 7",
        "hotbar_8": "Hotbar 8",
        "hotbar_9": "Hotbar 9",
        "hotbar_0": "Hotbar 0",
        "toggle_minimap": "Toggle Minimap",
        "minimap_zoom_in": "Minimap Zoom In",
        "minimap_zoom_out": "Minimap Zoom Out",
        "screenshot": "Screenshot",
        "toggle_camera_follow": "Camera Follow",
        "toggle_debug": "Toggle Debug",
        "toggle_help": "Toggle Help",
        "codex": "Codex",
    }

    CONFIG_PREFIX = "key_"

    def __init__(self):
        self.bindings = dict(self.DEFAULT_BINDINGS)

    def getKey(self, action):
        return self.bindings.get(action)

    def setKey(self, action, key):
        if action in self.bindings:
            self.bindings[action] = key

    def getActions(self):
        return list(self.bindings.keys())

    def getLabel(self, action):
        return self.ACTION_LABELS.get(action, action)

    def getKeyName(self, action):
        key = self.bindings.get(action)
        if key is None:
            return "None"
        return pygame.key.name(key)

    def getConflicts(self):
        """Return a set of actions that share a key with another action."""
        return self.getConflictsForBindings(self.bindings)

    def getConflictsForBindings(self, bindings):
        """Return a set of actions that share a key with another action in the given bindings dict."""
        keyToActions = {}
        for action, key in bindings.items():
            keyToActions.setdefault(key, []).append(action)
        conflicting = set()
        for actions in keyToActions.values():
            if len(actions) > 1:
                conflicting.update(actions)
        return conflicting

    def hasConflicts(self):
        return len(self.getConflicts()) > 0

    def resetToDefaults(self):
        self.bindings = dict(self.DEFAULT_BINDINGS)

    def loadFromConfig(self, configValues):
        """Load keybinding overrides from config values dict."""
        for action in self.DEFAULT_BINDINGS:
            configKey = self.CONFIG_PREFIX + action
            value = configValues.get(configKey)
            if isinstance(value, int) and not isinstance(value, bool):
                self.bindings[action] = value

    def saveToConfigFile(self, config):
        """Save current keybindings to config.yml."""
        configFilePath = config.getConfigFilePath()
        lines = []
        if configFilePath.exists():
            try:
                lines = configFilePath.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                lines = []

        savedValues = {}
        for action, key in self.bindings.items():
            savedValues[self.CONFIG_PREFIX + action] = str(key)

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
