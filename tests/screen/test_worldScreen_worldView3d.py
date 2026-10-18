"""WorldScreen.draw with a frontend that draws the world from WorldViews
(RFC 0017 stage 3): the world tiles and day/night overlay are skipped, a
transparent hole is cut, the HUD is still drawn, and the same rooms are loaded
as in 2D, so the view mode cannot change which rooms exist or get saved."""

from unittest.mock import MagicMock

import pytest

from rendering.renderer import Renderer
from rendering.worldViewSink import WorldViewSink
from screen.worldScreen import WorldScreen
from ui.geometry import Rect

GAME_AREA = Rect(280, 0, 720, 720)


def _screen(drawsWorldFromView):
    ws = WorldScreen.__new__(WorldScreen)
    ws.renderer = MagicMock()
    ws.renderer.getGameAreaRect.return_value = GAME_AREA
    ws.renderer.drawsWorldFromView.return_value = drawsWorldFromView
    ws.renderer.supportsImageLoading.return_value = True
    ws.config = MagicMock()
    ws.config.showMiniMap = False
    ws.config.debug = False
    ws.config.dayNightCycleEnabled = True
    ws.config.cameraFollowPlayer = True
    ws.currentRoom = MagicMock()
    ws.currentZ = 0
    ws.showHelp = False
    ws.deathRespawnTicksRemaining = 0
    ws.pausedByFocusLoss = False
    ws.minimapScaleFactor = 0
    ws.hudDragManager = MagicMock()
    ws.hudDragManager.getOffset.return_value = (0, 0)
    ws.status = MagicMock()
    ws.energyBar = MagicMock()
    ws.keyBindings = MagicMock()
    ws.keyBindings.getKeyName.return_value = "f1"
    for name in (
        "drawFollowMode",
        "_drawDayNightOverlay",
        "_drawHotbar",
        "_drawDayNightPhaseIndicator",
        "_drawTextMinimap",
        "drawCursorSlot",
        "getOrLoadRoom",
    ):
        setattr(ws, name, MagicMock())
    ws._iterateVisibleRoomOffsets = MagicMock(
        return_value=[(0, 0, 280, 0), (1, 0, 1000, 0), (0, -1, 280, -720)]
    )
    return ws


def test_2d_frontends_draw_the_world_as_before():
    ws = _screen(drawsWorldFromView=False)

    ws.draw()

    ws.drawFollowMode.assert_called_once()
    ws._drawDayNightOverlay.assert_called_once_with(GAME_AREA)
    ws.renderer.clearRegion.assert_not_called()
    ws.status.draw.assert_called_once()


def test_3d_frontend_gets_a_hole_and_the_hud():
    ws = _screen(drawsWorldFromView=True)

    ws.draw()

    ws.drawFollowMode.assert_not_called()
    ws._drawDayNightOverlay.assert_not_called()
    ws.renderer.drawImage.assert_not_called()
    ws.renderer.clearRegion.assert_called_once_with(GAME_AREA)
    ws.status.draw.assert_called_once()
    ws.energyBar.draw.assert_called_once()
    ws._drawHotbar.assert_called_once()


def test_3d_frontend_loads_the_same_rooms_the_2d_view_would():
    ws = _screen(drawsWorldFromView=True)

    ws.draw()

    assert [c.args for c in ws.getOrLoadRoom.call_args_list] == [
        (0, 0),
        (1, 0),
        (0, -1),
    ]


def test_renderer_base_defaults_keep_every_2d_backend_unchanged():
    assert Renderer.drawsWorldFromView(MagicMock()) is False
    assert Renderer.clearRegion(MagicMock(), GAME_AREA) is None


class _Sink(WorldViewSink):
    pass


@pytest.mark.parametrize("offersSink", [False, True])
def test_roam_registers_a_frontend_sink_only_when_offered(offersSink):
    from roam import registerFrontendWorldViewSink

    sink = _Sink()
    frontend = MagicMock(spec=["getRenderer", "getInputSource", "getClock"])
    if offersSink:
        frontend.getWorldViewSink = MagicMock(return_value=sink)
    container = MagicMock()

    registerFrontendWorldViewSink(container, frontend)

    calls = [c.args for c in container.registerInstance.call_args_list]
    assert calls == ([(WorldViewSink, sink)] if offersSink else [])
