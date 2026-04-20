import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

from ui.hotbarLayout import getHotbarTop
from ui.status import Status
from world.tickCounter import TickCounter
from lib.graphik.src.graphik import Graphik


def createMockGraphik(width, height):
    graphik = MagicMock()
    graphik.getGameDisplay().get_size.return_value = (width, height)
    return graphik


def createMockTickCounter(tick=0):
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = tick
    return tickCounter


def createStatus(resolve, override_dependency, width, height, tick=0):
    graphik = createMockGraphik(width, height)
    tickCounter = createMockTickCounter(tick)
    override_dependency(Graphik, graphik)
    override_dependency(TickCounter, tickCounter)
    status = resolve(Status)
    return status, graphik


def test_status_text_does_not_overlap_hotbar_at_720(resolve, override_dependency):
    graphik = createMockGraphik(1280, 720)
    tickCounter = createMockTickCounter()
    override_dependency(Graphik, graphik)
    override_dependency(TickCounter, tickCounter)
    status = resolve(Status)
    status.set("test message")
    status.draw()

    drawButtonCall = graphik.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = getHotbarTop(720)
    assert statusBottom <= hotbarTop


def test_status_text_does_not_overlap_hotbar_at_1080(resolve, override_dependency):
    status, graphik = createStatus(resolve, override_dependency, 1920, 1080)
    status.set("test message")
    status.draw()

    drawButtonCall = graphik.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = getHotbarTop(1080)
    assert statusBottom <= hotbarTop


def test_status_text_does_not_overlap_hotbar_at_500(resolve, override_dependency):
    status, graphik = createStatus(resolve, override_dependency, 800, 500)
    status.set("test message")
    status.draw()

    drawButtonCall = graphik.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = getHotbarTop(500)
    assert statusBottom <= hotbarTop


def test_status_draw_not_called_when_no_text(resolve, override_dependency):
    status, graphik = createStatus(resolve, override_dependency, 1280, 720)
    status.draw()
    graphik.drawButton.assert_not_called()


def test_status_draw_not_called_after_clear(resolve, override_dependency):
    status, graphik = createStatus(resolve, override_dependency, 1280, 720)
    status.set("test")
    status.clear()
    status.draw()
    graphik.drawButton.assert_not_called()


def test_status_centered_horizontally(resolve, override_dependency):
    status, graphik = createStatus(resolve, override_dependency, 1000, 800)
    status.set("hello")
    status.draw()

    drawButtonCall = graphik.drawButton.call_args
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
