import math
import time

from rendering.worldViewSink import WorldViewSink

MESSAGE_TYPE = "worldview"
MESSAGE_VERSION = 1


# @author Claude
# @since October 18th, 2026
#
# The WorldViewSink of the opt-in browser 3D view (/play?view=3d; RFC 0017
# stage 3, wire format proposed in Preponderous RFC 0018). It turns each
# published WorldView into a "worldview" message for the page and hands it to
# post(): the first message (and any after requestFull()) carries every room
# in view; later ones carry only rooms whose revision changed, plus the rooms
# that left the view, the player, the lights and the time of day.
#
# Cadence: it times its own cost (from the wantsWorldView() that said yes to
# the end of publish(), so build + encode + post) as a moving average, and asks
# for a view only every k-th tick, k = clamp(ceil(average / BUDGET_MS), 1,
# MAX_EVERY), so the average stays near the per-tick budget; and never more
# than 30 times a second of wall time.
class Web3DWorldViewSink(WorldViewSink):
    BUDGET_MS = 2.0
    MAX_EVERY = 6
    EMA_ALPHA = 0.2
    # Never more often than the page can show: the browser build's loop is
    # not always held to 30 TPS, and a message per tick beyond the display
    # rate only costs both threads time.
    MIN_INTERVAL_SECONDS = 1.0 / 30.0

    def __init__(self, post, radiusRooms=1, clock=time.perf_counter):
        self._post = post
        self._radius = radiusRooms
        self._clock = clock
        self._every = 1
        self._ticksUntilNext = 0
        self._wantedAt = None
        self._lastPublishedAt = None
        self._averageMs = None
        self._sentRevisions = {}
        self._classes = []
        self._classIndex = {}
        self._classImages = []
        self._seq = 0
        self._needFull = True

    # --- WorldViewSink ------------------------------------------------------

    def wantsWorldView(self):
        if self._ticksUntilNext > 0:
            self._ticksUntilNext -= 1
            return False
        now = self._clock()
        if (
            self._lastPublishedAt is not None
            and now - self._lastPublishedAt < self.MIN_INTERVAL_SECONDS * 0.9
        ):
            return False
        self._wantedAt = now
        return True

    def getWantedRadiusRooms(self):
        return self._radius

    def publish(self, worldView):
        self._post(self.encode(worldView))
        now = self._clock()
        # Spaced by when publishing started, so a tick-paced loop at exactly
        # 30 TPS publishes every tick.
        self._lastPublishedAt = self._wantedAt if self._wantedAt is not None else now
        if self._wantedAt is not None:
            self._recordCost((now - self._wantedAt) * 1000.0)
            self._wantedAt = None
        self._ticksUntilNext = self._every - 1

    # --- page requests ------------------------------------------------------

    def requestFull(self):
        """The page lost its state (or asked to resync): send every room next."""
        self._needFull = True

    # --- diagnostics --------------------------------------------------------

    def getEvery(self):
        return self._every

    def getAverageMs(self):
        return self._averageMs

    # --- encoding -----------------------------------------------------------

    def encode(self, worldView):
        full = self._needFull
        self._needFull = False
        if full:
            self._sentRevisions = {}
        images = dict(worldView.getClassImages())
        rooms = []
        inView = set()
        for roomView in worldView.getRooms():
            key = roomView.getKey()
            inView.add(key)
            if self._sentRevisions.get(key) == roomView.getRevision():
                continue
            self._sentRevisions[key] = roomView.getRevision()
            rooms.append(
                {
                    "x": roomView.getX(),
                    "y": roomView.getY(),
                    "z": roomView.getZ(),
                    "revision": roomView.getRevision(),
                    "roomType": roomView.getRoomType(),
                    "biome": roomView.getBiome(),
                    "backgroundColor": [int(c) for c in roomView.getBackgroundColor()],
                    "tiles": [
                        [self._indexOf(name, images) for name in stack]
                        for stack in roomView.getTiles()
                    ],
                }
            )
        dropped = [list(key) for key in self._sentRevisions if key not in inView]
        for key in dropped:
            del self._sentRevisions[tuple(key)]
        player = worldView.getPlayer()
        self._seq += 1
        return {
            "type": MESSAGE_TYPE,
            "v": MESSAGE_VERSION,
            "seq": self._seq,
            "full": full,
            "tick": worldView.getTick(),
            "gridSize": worldView.getGridSize(),
            "radius": worldView.getCameraHint().getVisibleRadiusRooms(),
            "dayNight": {
                "enabled": worldView.isDayNightEnabled(),
                "cycleLengthTicks": worldView.getCycleLengthTicks(),
                "overlayOpacity": worldView.getOverlayOpacity(),
                "phase": worldView.getPhase(),
            },
            "player": {
                "room": list(player.getRoom()),
                "x": player.getTileX(),
                "y": player.getTileY(),
                "direction": player.getDirection(),
            },
            "classes": list(self._classes),
            "classImages": list(self._classImages),
            "rooms": rooms,
            "dropped": dropped,
            "lights": [
                {
                    "room": list(light.getRoom()),
                    "x": light.getTileX(),
                    "y": light.getTileY(),
                    "radiusTiles": light.getRadiusTiles(),
                    "entityClass": light.getEntityClass(),
                }
                for light in worldView.getLights()
            ],
            "buildMs": self._averageMs,
            "every": self._every,
        }

    def _indexOf(self, name, images):
        index = self._classIndex.get(name)
        if index is None:
            index = self._classIndex[name] = len(self._classes)
            self._classes.append(name)
            self._classImages.append(images.get(name))
        return index

    def _recordCost(self, elapsedMs):
        if self._averageMs is None:
            self._averageMs = elapsedMs
        else:
            self._averageMs += self.EMA_ALPHA * (elapsedMs - self._averageMs)
        self._every = max(
            1, min(self.MAX_EVERY, math.ceil(self._averageMs / self.BUDGET_MS))
        )
