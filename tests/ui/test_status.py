import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

from ui.hotbarLayout import getHotbarTop
from ui.status import Status
from world.tickCounter import TickCounter
from rendering.renderer import Renderer


def createMockRenderer(width, height):
    renderer = MagicMock()
    renderer.getDisplaySize.return_value = (width, height)
    return renderer


def createMockTickCounter(tick=0):
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = tick
    return tickCounter


def createStatus(resolve, override_dependency, width, height, tick=0):
    renderer = createMockRenderer(width, height)
    tickCounter = createMockTickCounter(tick)
    override_dependency(Renderer, renderer)
    override_dependency(TickCounter, tickCounter)
    status = resolve(Status)
    return status, renderer


def test_status_text_does_not_overlap_hotbar_at_720(resolve, override_dependency):
    renderer = createMockRenderer(1280, 720)
    tickCounter = createMockTickCounter()
    override_dependency(Renderer, renderer)
    override_dependency(TickCounter, tickCounter)
    status = resolve(Status)
    status.set("test message")
    status.draw()

    drawButtonCall = renderer.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = getHotbarTop(720)
    assert statusBottom <= hotbarTop


def test_status_text_does_not_overlap_hotbar_at_1080(resolve, override_dependency):
    status, renderer = createStatus(resolve, override_dependency, 1920, 1080)
    status.set("test message")
    status.draw()

    drawButtonCall = renderer.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = getHotbarTop(1080)
    assert statusBottom <= hotbarTop


def test_status_text_does_not_overlap_hotbar_at_500(resolve, override_dependency):
    status, renderer = createStatus(resolve, override_dependency, 800, 500)
    status.set("test message")
    status.draw()

    drawButtonCall = renderer.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = getHotbarTop(500)
    assert statusBottom <= hotbarTop


def test_status_draw_not_called_when_no_text(resolve, override_dependency):
    status, renderer = createStatus(resolve, override_dependency, 1280, 720)
    status.draw()
    renderer.drawButton.assert_not_called()


def test_status_draw_not_called_after_clear(resolve, override_dependency):
    status, renderer = createStatus(resolve, override_dependency, 1280, 720)
    status.set("test")
    status.clear()
    status.draw()
    renderer.drawButton.assert_not_called()


def test_status_centered_horizontally(resolve, override_dependency):
    status, renderer = createStatus(resolve, override_dependency, 1000, 800)
    status.set("hello")
    status.draw()

    drawButtonCall = renderer.drawButton.call_args
    statusXPos = drawButtonCall[0][0]
    statusWidth = drawButtonCall[0][2]
    center = statusXPos + statusWidth / 2
    assert center == 1000 / 2


def test_check_for_expiration_clears_text(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 1280, 720, tick=10)
    status.set("expiring text")

    status.checkForExpiration(10 + status.durationInTicks + 1)
    assert status.text == -1


def test_check_for_expiration_keeps_text_before_expiry(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 1280, 720, tick=10)
    status.set("still here")

    status.checkForExpiration(10 + status.durationInTicks - 1)
    assert status.text == "still here"
