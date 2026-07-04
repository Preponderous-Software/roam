"""Agentic (CPC) NPC behavior driven by Claude claude-haiku-4-5 via the Anthropic API.

Falls back transparently to ProgrammaticBehavior when ANTHROPIC_API_KEY is unset
or the `anthropic` package is not installed.
"""
import json
import os
import queue
import threading

try:
    import anthropic as _anthropic_module

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False

from entity.apple import Apple
from entity.banana import Banana
from entity.food import Food
from entity.living.livingEntity import LivingEntity
from entity.oakWood import OakWood
from entity.stone import Stone
from entity.woodFloor import WoodFloor
from npc.npcBehavior import NpcBehavior
from npc.programmaticBehavior import (
    ProgrammaticBehavior,
    _getNeighbor,
    _hasSolid,
    _locationOf,
)

_MODEL = "claude-haiku-4-5"
_CALL_INTERVAL_TICKS = 90  # ~3 s at 30 TPS

_SYSTEM_PROMPT = """You are the brain of a player character in a top-down 2-D survival game.
The world is a grid of tiles. Your character executes one action per game tick.

Available actions:
  move   direction: 0=up 1=left 2=down 3=right
  gather (picks up one item at your current tile — no parameters)
  eat    (eats the first food in your inventory — no parameters)
  place  dx, dy integers: place one OakWood at tile offset (dx,dy) from your position
  idle   (wait one tick — no parameters)

Survival priorities (in order):
  1. Eat food when energy drops below 50 % of max.
  2. Build a small OakWood shelter when carrying 7 or more OakWood pieces.
  3. Gather OakWood (T), Stone (S), or food (A/B) when visible nearby.
  4. Explore/wander otherwise.

Return ONLY a valid JSON object — no markdown fences, no extra keys. Schema:
{
  "goal": "<one-line description of your current objective>",
  "actions": [
    {"type": "move", "direction": 2},
    {"type": "gather"},
    ...
  ]
}
Plan 4–8 coherent sequential actions."""

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {"type": "string"},
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["move", "gather", "eat", "place", "idle"],
                    },
                    "direction": {"type": "integer"},
                    "dx": {"type": "integer"},
                    "dy": {"type": "integer"},
                },
                "required": ["type"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["goal", "actions"],
    "additionalProperties": False,
}


class AgenticBehavior(NpcBehavior):
    """NPC driven by Claude; degrades gracefully to ProgrammaticBehavior when
    the API is not reachable.
    """

    def __init__(self):
        self._fallback = ProgrammaticBehavior()
        self._client = self._buildClient()
        self._actionQueue: queue.Queue = queue.Queue()
        self._pendingCall = False
        self._ticksSinceCall = _CALL_INTERVAL_TICKS  # trigger on first opportunity
        self._stateName = "cpc-idle"
        self._goalDescription = ""

    # ------------------------------------------------------------------ #
    # NpcBehavior interface                                                #
    # ------------------------------------------------------------------ #

    def getStateName(self):
        return self._stateName

    def getGoalDescription(self):
        return self._goalDescription

    def tick(self, npc, room, tick, config):
        if self._client is None:
            self._fallback.tick(npc, room, tick, config)
            self._stateName = "fsm:" + self._fallback.getStateName()
            self._goalDescription = self._fallback.getGoalDescription()
            return

        tps = config.ticksPerSecond
        if tick <= npc.getTickLastMoved() + tps / npc.getMovementSpeed():
            return

        # Execute one queued action if available.
        try:
            action = self._actionQueue.get_nowait()
            self._executeAction(action, npc, room, tick)
            return
        except queue.Empty:
            pass

        # Schedule an AI call when the queue is drained and the interval elapsed.
        self._ticksSinceCall = min(self._ticksSinceCall + 1, _CALL_INTERVAL_TICKS)
        if self._ticksSinceCall >= _CALL_INTERVAL_TICKS and not self._pendingCall:
            self._ticksSinceCall = 0
            self._pendingCall = True
            worldState = self._buildWorldState(npc, room)
            threading.Thread(
                target=self._callAI,
                args=(worldState,),
                daemon=True,
            ).start()

    # ------------------------------------------------------------------ #
    # Anthropic client construction                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _buildClient():
        if not _ANTHROPIC_AVAILABLE:
            return None
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return None
        try:
            return _anthropic_module.Anthropic(api_key=key)
        except Exception:
            return None

    # ------------------------------------------------------------------ #
    # AI call (runs in a daemon background thread)                        #
    # ------------------------------------------------------------------ #

    def _callAI(self, worldState: str):
        try:
            response = self._client.messages.create(
                model=_MODEL,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": worldState}],
            )
            text = next((b.text for b in response.content if b.type == "text"), "{}")
            # Strip markdown fences the model may add despite instructions.
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
            goal = data.get("goal", "")
            if goal:
                self._goalDescription = goal
            for action in data.get("actions", []):
                if isinstance(action, dict) and "type" in action:
                    self._actionQueue.put(action)
        except Exception:
            pass
        finally:
            self._pendingCall = False

    # ------------------------------------------------------------------ #
    # World-state serialisation (called from main thread)                 #
    # ------------------------------------------------------------------ #

    def _buildWorldState(self, npc, room) -> str:
        location = _locationOf(npc, room)
        if location is None:
            return "Position unknown. Idle."

        x, y = location.getX(), location.getY()
        energy = int(npc.getEnergy())
        maxEnergy = getattr(npc, "targetEnergy", 100)

        invParts = []
        for slot in npc.getInventory().getInventorySlots():
            if not slot.isEmpty():
                contents = slot.getContents()
                invParts.append(f"{contents[0].__class__.__name__}×{len(contents)}")
        invStr = ", ".join(invParts) if invParts else "empty"

        # 5×5 ASCII grid centred on the NPC (north = up)
        rows = []
        for dy in range(-2, 3):
            row = []
            for dx in range(-2, 3):
                if dx == 0 and dy == 0:
                    row.append("@")
                    continue
                loc = room.getGrid().getLocationByCoordinates(x + dx, y + dy)
                row.append("?" if loc == -1 else _cellGlyph(loc))
            rows.append(" ".join(row))
        gridStr = "\n".join(rows)

        return (
            f"Position ({x},{y})  Energy {energy}/{maxEnergy}\n"
            f"Inventory: {invStr}\n"
            f"Grid (5×5, @ = you, top = north):\n{gridStr}\n"
            "Legend: . empty  T OakWood  S Stone  A Apple  B Banana"
            "  W wood-floor  # solid/wall  ? creature"
        )

    # ------------------------------------------------------------------ #
    # Action execution (called from main thread)                          #
    # ------------------------------------------------------------------ #

    def _executeAction(self, action, npc, room, tick):
        atype = action.get("type", "idle")
        location = _locationOf(npc, room)
        if location is None:
            return

        if atype == "move":
            direction = int(action.get("direction", 2)) % 4
            self._doMove(npc, location, room, tick, direction)
            self._stateName = "cpc-move"

        elif atype == "gather":
            self._doGather(npc, location, room, tick)
            self._stateName = "cpc-gather"

        elif atype == "eat":
            self._doEat(npc, tick)
            self._stateName = "cpc-eat"

        elif atype == "place":
            dx = int(action.get("dx", 0))
            dy = int(action.get("dy", 0))
            self._doPlace(npc, location, room, tick, dx, dy)
            self._stateName = "cpc-place"

        else:
            npc.setTickLastMoved(tick)
            self._stateName = "cpc-idle"

    def _doMove(self, npc, location, room, tick, direction):
        grid = room.getGrid()
        neighbor = _getNeighbor(location, direction, grid)
        if neighbor is None or _hasSolid(neighbor):
            for alt in [(direction + 1) % 4, (direction + 3) % 4, (direction + 2) % 4]:
                candidate = _getNeighbor(location, alt, grid)
                if candidate is not None and not _hasSolid(candidate):
                    neighbor = candidate
                    direction = alt
                    break
            else:
                npc.setTickLastMoved(tick)
                return
        location.removeEntity(npc)
        neighbor.addEntity(npc)
        npc.setLocationID(neighbor.getID())
        npc.setDirection(direction)
        npc.setTickLastMoved(tick)
        npc.removeEnergy(0.5)

    def _doGather(self, npc, location, room, tick):
        for entity in list(location.getEntities().values()):
            if entity is npc or isinstance(entity, LivingEntity):
                continue
            if isinstance(entity, (OakWood, Stone, Apple, Banana)):
                if npc.getInventory().placeIntoFirstAvailableInventorySlot(entity):
                    room.removeEntity(entity)
                    npc.setTickLastGathered(tick)
                    npc.setTickLastMoved(tick)
                break

    def _doEat(self, npc, tick):
        for slot in npc.getInventory().getInventorySlots():
            if slot.isEmpty():
                continue
            item = slot.getContents()[0]
            if isinstance(item, Food) and item.getEnergy() > 0:
                npc.addEnergy(item.getEnergy())
                npc.getInventory().removeByItem(item)
                npc.setTickLastMoved(tick)
                break

    def _doPlace(self, npc, location, room, tick, dx, dy):
        woodSlot = None
        for slot in npc.getInventory().getInventorySlots():
            if not slot.isEmpty() and isinstance(slot.getContents()[0], OakWood):
                woodSlot = slot
                break
        if woodSlot is None:
            npc.setTickLastMoved(tick)
            return

        nx = location.getX() + dx
        ny = location.getY() + dy
        target = room.getGrid().getLocationByCoordinates(nx, ny)
        if target == -1:
            npc.setTickLastMoved(tick)
            return
        for e in target.getEntities().values():
            if e.isSolid() or isinstance(e, LivingEntity):
                npc.setTickLastMoved(tick)
                return

        item = woodSlot.pop()
        if item == -1:
            npc.setTickLastMoved(tick)
            return
        room.addEntityToLocation(item, target)
        npc.setTickLastPlaced(tick)
        npc.setTickLastMoved(tick)


# ------------------------------------------------------------------ #
# Module-level helpers                                                #
# ------------------------------------------------------------------ #


def _cellGlyph(location) -> str:
    entities = list(location.getEntities().values())
    if not entities:
        return "."
    for e in entities:
        if isinstance(e, LivingEntity):
            return "?"
    for e in entities:
        if isinstance(e, Apple):
            return "A"
        if isinstance(e, Banana):
            return "B"
        if isinstance(e, OakWood):
            return "T"
        if isinstance(e, Stone):
            return "S"
        if isinstance(e, WoodFloor):
            return "W"
        if e.isSolid():
            return "#"
    return "."
