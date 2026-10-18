"""Camera-relative movement and 3D picking in WorldScreen (Preponderous RFC
0021, behind the browser game's opt-in ?view=3d). With the InputSource
defaults (rotation 0, no tile picking) nothing changes; with the 3D view's
hooks, movement keys turn with the camera and the pointed tile resolves to
exactly the (location, room) the 2D mouse path resolves for that tile."""

from unittest.mock import MagicMock

import pytest

from config.keyBindings import KeyBindings
from rendering.inputSource import InputSource
from rendering.keyCode import KeyCode
from rendering.nullInputSource import NullInputSource
from rendering.webInputSource import WebInputSource
from screen.worldScreen import WorldScreen
from ui.geometry import Rect
from world.room import Room

GRID = 5
UP, LEFT, DOWN, RIGHT = 0, 1, 2, 3


class _FakeInput(InputSource):
    def __init__(self, rotation=0, picking=False, pointed=None, mouse=(0, 0)):
        self.rotation = rotation
        self.picking = picking
        self.pointed = pointed
        self.mouse = mouse

    def pollEvents(self):
        return []

    def isPressed(self, keyCode):
        return False

    def getMousePosition(self):
        return self.mouse

    def getMouseButtons(self):
        return (False, False, False)

    def getMovementRotation(self):
        return self.rotation

    def supportsTilePicking(self):
        return self.picking

    def getPointedTile(self):
        return self.pointed


def test_input_source_defaults_are_the_2d_behaviour():
    source = NullInputSource()

    assert source.getMovementRotation() == 0
    assert source.supportsTilePicking() is False
    assert source.getPointedTile() is None


def test_web_input_source_starts_2d_and_switches_on_the_first_pointed_tile():
    source = WebInputSource()
    assert (source.getMovementRotation(), source.supportsTilePicking()) == (0, False)

    source.setMovementRotation(5)
    source.setPointedTile((40, -3, 0))
    assert source.getMovementRotation() == 1
    assert source.supportsTilePicking() is True
    assert source.getPointedTile() == (40, -3, 0)

    source.setPointedTile(None)
    assert source.supportsTilePicking() is True
    assert source.getPointedTile() is None


# --- camera-relative movement ----------------------------------------------


def _movementScreen(rotation):
    ws = WorldScreen.__new__(WorldScreen)
    ws.inputSource = _FakeInput(rotation=rotation)
    ws.keyBindings = KeyBindings()
    ws.player = MagicMock()
    ws.checkPlayerMovementCooldown = MagicMock(return_value=True)
    ws.movePlayer = MagicMock()
    return ws


# Camera quarter turns counter-clockwise seen from above: 1 = the camera on the
# east side looking west, so "up" (away from the camera) is west.
EXPECTED = {
    0: {KeyCode.W: UP, KeyCode.A: LEFT, KeyCode.S: DOWN, KeyCode.D: RIGHT},
    1: {KeyCode.W: LEFT, KeyCode.A: DOWN, KeyCode.S: RIGHT, KeyCode.D: UP},
    2: {KeyCode.W: DOWN, KeyCode.A: RIGHT, KeyCode.S: UP, KeyCode.D: LEFT},
    3: {KeyCode.W: RIGHT, KeyCode.A: UP, KeyCode.S: LEFT, KeyCode.D: DOWN},
}
ARROWS = {
    KeyCode.UP: KeyCode.W,
    KeyCode.LEFT: KeyCode.A,
    KeyCode.DOWN: KeyCode.S,
    KeyCode.RIGHT: KeyCode.D,
}


@pytest.mark.parametrize("rotation", [0, 1, 2, 3])
def test_movement_keys_follow_the_camera(rotation):
    for key, expected in EXPECTED[rotation].items():
        ws = _movementScreen(rotation)
        ws.handleKeyDownEvent(key)
        ws.player.setDirection.assert_called_once_with(expected)


@pytest.mark.parametrize("rotation", [0, 1, 2, 3])
def test_alt_movement_keys_follow_the_camera_too(rotation):
    for arrow, letter in ARROWS.items():
        ws = _movementScreen(rotation)
        ws.handleKeyDownEvent(arrow)
        ws.player.setDirection.assert_called_once_with(EXPECTED[rotation][letter])


def test_a_move_uses_the_rotated_direction():
    ws = _movementScreen(1)
    ws.player.direction = None

    def setDirection(direction):
        ws.player.direction = direction

    ws.player.setDirection.side_effect = setDirection
    ws.handleKeyDownEvent(KeyCode.W)

    ws.movePlayer.assert_called_once_with(LEFT)


# --- picking -----------------------------------------------------------------


def _pickingScreen(worldBorder=0, currentRoomXY=(0, -1)):
    rooms = {}
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = currentRoomXY[0] + dx, currentRoomXY[1] + dy
            rooms[(x, y)] = Room("r", GRID, (0, 0, 0), x, y, MagicMock())
    ws = WorldScreen.__new__(WorldScreen)
    ws.config = MagicMock()
    ws.config.gridSize = GRID
    ws.config.worldBorder = worldBorder
    ws.config.cameraFollowPlayer = True
    ws.currentZ = 0
    ws.currentRoom = rooms[currentRoomXY]
    ws.renderer = MagicMock()
    ws.renderer.getGameAreaRect.return_value = Rect(280, 0, 720, 720)
    ws.locationWidth = 40
    ws.locationHeight = 40
    playerLocation = ws.currentRoom.getGrid().getLocationByCoordinates(2, 3)
    ws.getLocationOfPlayer = MagicMock(return_value=playerLocation)
    ws.getOrLoadRoom = MagicMock(side_effect=lambda x, y, z=None: rooms[(x, y)])
    return ws, rooms


def _pixelCentreOf(ws, relX, relY):
    # Inverse of the 2D follow-camera math in getLocationAndRoomAtMousePosition.
    gameArea = ws.renderer.getGameAreaRect()
    player = ws.getLocationOfPlayer()
    offsetX = gameArea.x + gameArea.width / 2 - (player.getX() * 40 + 20)
    offsetY = gameArea.y + gameArea.height / 2 - (player.getY() * 40 + 20)
    return (offsetX + relX * 40 + 20, offsetY + relY * 40 + 20)


def test_picking_resolves_the_same_tile_as_the_2d_path():
    ws, _ = _pickingScreen()
    roomX, roomY = ws.currentRoom.getX(), ws.currentRoom.getY()
    checked = 0
    # Every tile of the current room and a band of each neighbour.
    for relX in range(-GRID, 2 * GRID):
        for relY in range(-GRID, 2 * GRID):
            ws.inputSource = _FakeInput(mouse=_pixelCentreOf(ws, relX, relY))
            twoD = ws.getLocationAndRoomAtMousePosition()
            ws.inputSource = _FakeInput(
                picking=True,
                pointed=(roomX * GRID + relX, roomY * GRID + relY, 0),
            )
            threeD = ws.getLocationAndRoomAtMousePosition()

            assert threeD[0] is twoD[0], (relX, relY)
            assert threeD[1] is twoD[1], (relX, relY)
            checked += 1
    assert checked == (3 * GRID) ** 2


def test_pointing_at_nothing_or_another_level_picks_nothing():
    ws, _ = _pickingScreen()
    ws.inputSource = _FakeInput(picking=True, pointed=None)
    assert ws.getLocationAndRoomAtMousePosition() == (-1, None)

    ws.inputSource = _FakeInput(picking=True, pointed=(10, -5, -1))
    assert ws.getLocationAndRoomAtMousePosition() == (-1, None)
    ws.getOrLoadRoom.assert_not_called()


def test_world_border_applies_the_same_in_3d_and_2d():
    ws, _ = _pickingScreen(worldBorder=2, currentRoomXY=(2, 0))
    # One room east of the current room is outside the border (x = 3).
    ws.inputSource = _FakeInput(mouse=_pixelCentreOf(ws, GRID + 1, 1))
    twoD = ws.getLocationAndRoomAtMousePosition()
    ws.inputSource = _FakeInput(picking=True, pointed=(3 * GRID + 1, 1, 0))
    threeD = ws.getLocationAndRoomAtMousePosition()

    assert twoD == threeD == (-1, None)


def test_without_picking_the_2d_math_is_used_even_if_a_tile_was_pointed():
    ws, _ = _pickingScreen()
    ws.inputSource = _FakeInput(
        picking=False, pointed=(999, 999, 0), mouse=_pixelCentreOf(ws, 1, 1)
    )

    location, room = ws.getLocationAndRoomAtMousePosition()

    assert room is ws.currentRoom
    assert (location.getX(), location.getY()) == (1, 1)
