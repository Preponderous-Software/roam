import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from unittest.mock import MagicMock

from ui import palette
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


def test_check_for_expiration_keeps_text_on_expiry_tick(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 1280, 720, tick=10)
    status.set("last tick")

    status.checkForExpiration(10 + status.durationInTicks)
    assert status.text == "last tick"


def test_set_records_tick_last_set(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 1280, 720, tick=37)
    assert status.getTickLastSet() == -1

    status.set("hello")
    assert status.getTickLastSet() == 37


def test_set_with_custom_duration_expires_after_that_duration(
    resolve, override_dependency
):
    status, _ = createStatus(resolve, override_dependency, 1280, 720, tick=10)
    status.set("short", duration=5)

    status.checkForExpiration(15)
    assert status.text == "short"
    status.checkForExpiration(16)
    assert status.text == -1


def test_clear_restores_default_duration(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 1280, 720, tick=10)
    status.set("short", duration=5)
    status.clear()

    status.tickLastSet = 10
    status.text = "set directly"
    status.checkForExpiration(16)
    assert status.text == "set directly"


def test_set_hint_shows_text_when_status_empty(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 1280, 720, tick=10)
    status.setHint("press E")

    assert status.text == "press E"
    assert status.getTickLastSet() == 10
    status.checkForExpiration(70)
    assert status.text == "press E"
    status.checkForExpiration(71)
    assert status.text == -1


def test_set_hint_does_not_clobber_existing_text(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 1280, 720, tick=10)
    status.set("picked up apple")
    status.setHint("press E")

    assert status.text == "picked up apple"
    status.checkForExpiration(10 + status.durationInTicks)
    assert status.text == "picked up apple"


def test_default_rect_is_empty_when_no_text(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 1280, 720)
    rect = status.getDefaultRect()
    assert (rect.x, rect.y, rect.width, rect.height) == (0, 0, 0, 0)


def test_default_rect_matches_draw_position_without_offset(
    resolve, override_dependency
):
    status, renderer = createStatus(resolve, override_dependency, 1280, 720)
    status.set("hello world")
    status.draw()

    rect = status.getDefaultRect()
    drawArgs = renderer.drawButton.call_args[0]
    assert (rect.x, rect.y, rect.width, rect.height) == drawArgs[0:4]
    assert rect.width == len("hello world") * 11
    assert rect.height == status.textSize * 2


def test_draw_applies_offset_to_position(resolve, override_dependency):
    status, renderer = createStatus(resolve, override_dependency, 1280, 720)
    status.set("hello")
    rect = status.getDefaultRect()

    status.draw(offsetX=15, offsetY=-20)
    drawArgs = renderer.drawButton.call_args[0]
    assert drawArgs[0] == rect.x + 15
    assert drawArgs[1] == rect.y - 20
    assert drawArgs[2:4] == (rect.width, rect.height)


def test_draw_passes_text_style_and_clear_callback(resolve, override_dependency):
    status, renderer = createStatus(resolve, override_dependency, 1280, 720)
    status.set("hello")
    status.draw()

    drawArgs = renderer.drawButton.call_args[0]
    assert drawArgs[4:8] == (
        palette.WHITE,
        status.textColor,
        status.textSize,
        "hello",
    )
    drawArgs[8]()
    assert status.text == -1


def test_width_is_capped_at_eighty_percent_of_display(resolve, override_dependency):
    status, _ = createStatus(resolve, override_dependency, 500, 720)
    status.set("x" * 100)

    rect = status.getDefaultRect()
    assert rect.width == 400
    assert rect.x == 500 / 2 - 400 / 2
