import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock, call

from src.ui.status import Status


def createMockGraphik(width, height):
    graphik = MagicMock()
    graphik.getGameDisplay().get_size.return_value = (width, height)
    return graphik


def createMockTickCounter(tick=0):
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = tick
    return tickCounter


def test_status_text_does_not_overlap_hotbar_at_720():
    graphik = createMockGraphik(1280, 720)
    tickCounter = createMockTickCounter()
    status = Status(graphik, tickCounter)
    status.set("test message")
    status.draw()

    drawButtonCall = graphik.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = 720 - 50 * 3 - 5
    assert statusBottom <= hotbarTop


def test_status_text_does_not_overlap_hotbar_at_1080():
    graphik = createMockGraphik(1920, 1080)
    tickCounter = createMockTickCounter()
    status = Status(graphik, tickCounter)
    status.set("test message")
    status.draw()

    drawButtonCall = graphik.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = 1080 - 50 * 3 - 5
    assert statusBottom <= hotbarTop


def test_status_text_does_not_overlap_hotbar_at_500():
    graphik = createMockGraphik(800, 500)
    tickCounter = createMockTickCounter()
    status = Status(graphik, tickCounter)
    status.set("test message")
    status.draw()

    drawButtonCall = graphik.drawButton.call_args
    statusYPos = drawButtonCall[0][1]
    statusHeight = drawButtonCall[0][3]
    statusBottom = statusYPos + statusHeight

    hotbarTop = 500 - 50 * 3 - 5
    assert statusBottom <= hotbarTop


def test_status_draw_not_called_when_no_text():
    graphik = createMockGraphik(1280, 720)
    tickCounter = createMockTickCounter()
    status = Status(graphik, tickCounter)
    status.draw()
    graphik.drawButton.assert_not_called()


def test_status_draw_not_called_after_clear():
    graphik = createMockGraphik(1280, 720)
    tickCounter = createMockTickCounter()
    status = Status(graphik, tickCounter)
    status.set("test")
    status.clear()
    status.draw()
    graphik.drawButton.assert_not_called()


def test_status_centered_horizontally():
    graphik = createMockGraphik(1000, 800)
    tickCounter = createMockTickCounter()
    status = Status(graphik, tickCounter)
    status.set("hello")
    status.draw()

    drawButtonCall = graphik.drawButton.call_args
    statusXPos = drawButtonCall[0][0]
    statusWidth = drawButtonCall[0][2]
    center = statusXPos + statusWidth / 2
    assert center == 1000 / 2


def test_check_for_expiration_clears_text():
    graphik = createMockGraphik(1280, 720)
    tickCounter = createMockTickCounter(tick=10)
    status = Status(graphik, tickCounter)
    status.set("expiring text")

    status.checkForExpiration(10 + status.durationInTicks + 1)
    assert status.text == -1


def test_check_for_expiration_keeps_text_before_expiry():
    graphik = createMockGraphik(1280, 720)
    tickCounter = createMockTickCounter(tick=10)
    status = Status(graphik, tickCounter)
    status.set("still here")

    status.checkForExpiration(10 + status.durationInTicks - 1)
    assert status.text == "still here"
