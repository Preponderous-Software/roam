from rendering.keyCode import KeyCode, displayName, fromInt


# @author Copilot
# @since April 19th, 2026
class KeyBindings:
    """Manages keybinding defaults, remapping, conflict detection, and persistence.

    Bindings are stored as backend-neutral KeyCode members (frontend-abstraction
    epic #433, Phase 4). KeyCode is an IntEnum whose values are the SDL keycodes
    pygame already used, so existing `key_*` ints in config.yml keep working and
    comparisons against a frontend's raw key int still hold."""

    DEFAULT_BINDINGS = {
        "move_up": KeyCode.W,
        "move_left": KeyCode.A,
        "move_down": KeyCode.S,
        "move_right": KeyCode.D,
        "alt_move_up": KeyCode.UP,
        "alt_move_left": KeyCode.LEFT,
        "alt_move_down": KeyCode.DOWN,
        "alt_move_right": KeyCode.RIGHT,
        "run": KeyCode.LSHIFT,
        "crouch": KeyCode.LCTRL,
        "run_toggle": KeyCode.R,
        "crouch_toggle": KeyCode.Z,
        "look": KeyCode.X,
        "inventory": KeyCode.I,
        "hotbar_1": KeyCode.NUM_1,
        "hotbar_2": KeyCode.NUM_2,
        "hotbar_3": KeyCode.NUM_3,
        "hotbar_4": KeyCode.NUM_4,
        "hotbar_5": KeyCode.NUM_5,
        "hotbar_6": KeyCode.NUM_6,
        "hotbar_7": KeyCode.NUM_7,
        "hotbar_8": KeyCode.NUM_8,
        "hotbar_9": KeyCode.NUM_9,
        "hotbar_0": KeyCode.NUM_0,
        "gather": KeyCode.G,
        "place": KeyCode.F,
        "toggle_minimap": KeyCode.M,
        "minimap_zoom_in": KeyCode.EQUALS,
        "minimap_zoom_out": KeyCode.MINUS,
        "screenshot": KeyCode.PRINTSCREEN,
        "toggle_camera_follow": KeyCode.C,
        "toggle_debug": KeyCode.F3,
        "alt_toggle_debug": KeyCode.BACKSLASH,
        "toggle_help": KeyCode.F1,
        "alt_toggle_help": KeyCode.H,
        "codex": KeyCode.L,
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
        "run_toggle": "Run (toggle)",
        "crouch_toggle": "Crouch (toggle)",
        "look": "Look (examine facing tile)",
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
        "gather": "Gather",
        "place": "Place / Interact",
        "toggle_minimap": "Toggle Minimap",
        "minimap_zoom_in": "Minimap Zoom In",
        "minimap_zoom_out": "Minimap Zoom Out",
        "screenshot": "Screenshot",
        "toggle_camera_follow": "Camera Follow",
        "toggle_debug": "Toggle Debug",
        "alt_toggle_debug": "Toggle Debug (Alt)",
        "toggle_help": "Toggle Help",
        "alt_toggle_help": "Toggle Help (Alt)",
        "codex": "Codex",
    }

    CONFIG_PREFIX = "key_"

    def __init__(self):
        self.bindings = dict(self.DEFAULT_BINDINGS)

    def getKey(self, action):
        return self.bindings.get(action)

    def setKey(self, action, key):
        if action in self.bindings:
            # Accept either a KeyCode or a raw frontend int (e.g. a captured
            # key event); store as a KeyCode when we model it, otherwise keep
            # the raw value so unmodeled keys still rebind and compare.
            if not isinstance(key, KeyCode):
                key = fromInt(key) or key
            self.bindings[action] = key

    def getActions(self):
        return list(self.bindings.keys())

    def getLabel(self, action):
        return self.ACTION_LABELS.get(action, action)

    def getKeyName(self, action):
        key = self.bindings.get(action)
        if key is None:
            return "None"
        return displayName(key if isinstance(key, KeyCode) else fromInt(key))

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
        """Load keybinding overrides from config values dict.

        Stored values are the raw SDL ints written by earlier versions (and by
        saveToConfigFile); map each back to a KeyCode so the in-memory model is
        uniform. An int we don't model is kept as-is so a custom binding still
        round-trips."""
        for action in self.DEFAULT_BINDINGS:
            configKey = self.CONFIG_PREFIX + action
            value = configValues.get(configKey)
            if isinstance(value, int) and not isinstance(value, bool):
                self.bindings[action] = fromInt(value) or value

    def saveToConfigFile(self, config):
        """Save current keybindings to config.yml."""
        savedValues = {}
        for action, key in self.bindings.items():
            # Persist the SDL int (KeyCode is an IntEnum) so config.yml stays
            # backward/forward compatible; str(KeyCode) would write "KeyCode.W".
            savedValues[self.CONFIG_PREFIX + action] = str(int(key))

        config._writeKeyValues(
            savedValues, "failed to save key bindings to config file"
        )
