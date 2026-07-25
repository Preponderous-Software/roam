import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

from config.config import Config
from ui.hudDragManager import HudDragManager, clampPosition


@pytest.fixture(scope="module", autouse=True)
def pygameLifecycle():
    pygame.init()
    yield
    pygame.quit()


def make_rect_func(x, y, w, h):
    return lambda: pygame.Rect(x, y, w, h)


def test_clamp_position_within_bounds():
    cx, cy = clampPosition(100, 100, 200, 50, 800, 600)
    assert cx == 100
    assert cy == 100


def test_clamp_position_left_edge():
    cx, cy = clampPosition(-300, 100, 200, 50, 800, 600)
    minX = -200 * (1 - 0.2)
    assert cx == minX


def test_clamp_position_right_edge():
    cx, cy = clampPosition(900, 100, 200, 50, 800, 600)
    maxX = 800 - 200 * 0.2
    assert cx == maxX


def test_clamp_position_top_edge():
    cx, cy = clampPosition(100, -200, 200, 50, 800, 600)
    minY = -50 * (1 - 0.2)
    assert cy == minY


def test_clamp_position_bottom_edge():
    cx, cy = clampPosition(100, 700, 200, 50, 800, 600)
    maxY = 600 - 50 * 0.2
    assert cy == maxY


def test_register_and_get_offset(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("test", make_rect_func(10, 20, 100, 50))
    assert mgr.getOffset("test") == (0, 0)


def test_get_offset_unregistered(resolve):
    mgr = resolve(HudDragManager)
    assert mgr.getOffset("nonexistent") == (0, 0)


def test_is_dragging_false_by_default(resolve):
    mgr = resolve(HudDragManager)
    assert mgr.isDragging() is False


def test_handle_mouse_down_starts_drag(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    result = mgr.handleMouseDown(75, 75)
    assert result is True
    assert mgr.isDragging() is True


def test_handle_mouse_down_misses_element(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    result = mgr.handleMouseDown(200, 200)
    assert result is False
    assert mgr.isDragging() is False


def test_drag_updates_offset(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75)
    mgr.handleMouseMotion(125, 125, 800, 600)
    ox, oy = mgr.getOffset("box")
    assert ox == 50
    assert oy == 50


def test_drag_completes_on_mouse_up(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75)
    result = mgr.handleMouseUp(125, 125, 800, 600)
    assert result is True
    assert mgr.isDragging() is False
    ox, oy = mgr.getOffset("box")
    assert ox == 50
    assert oy == 50


def test_mouse_up_without_drag(resolve):
    mgr = resolve(HudDragManager)
    result = mgr.handleMouseUp(100, 100, 800, 600)
    assert result is False


def test_drag_clamped_at_screen_edge(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75)
    # try to drag way off the right edge
    mgr.handleMouseMotion(5000, 75, 800, 600)
    ox, oy = mgr.getOffset("box")
    # the element should be clamped so at least 20% visible
    rect = mgr.elements["box"].getRect()
    assert rect.x + rect.width * 0.2 <= 800


def test_drag_clamped_at_top_edge(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75)
    mgr.handleMouseMotion(75, -5000, 800, 600)
    rect = mgr.elements["box"].getRect()
    assert rect.y >= -rect.height * 0.8


def test_offset_persists_after_drag(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75)
    mgr.handleMouseUp(175, 175, 800, 600)
    # Start a second drag
    mgr.handleMouseDown(175, 175)
    mgr.handleMouseUp(225, 225, 800, 600)
    ox, oy = mgr.getOffset("box")
    assert ox == 150
    assert oy == 150


def test_motion_without_drag_is_noop(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    result = mgr.handleMouseMotion(100, 100, 800, 600)
    assert result is False
    assert mgr.getOffset("box") == (0, 0)


def test_save_writes_offset_entries(resolve, tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("debug: true\n", encoding="utf-8")
    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75)
    mgr.handleMouseUp(125, 125, 800, 600)

    mgr.save(config)

    content = configFilePath.read_text(encoding="utf-8")
    assert "hudOffset_box_x: 50" in content
    assert "hudOffset_box_y: 50" in content
    assert "debug: true" in content


def test_save_writes_zero_offset_for_undragged_element(resolve, tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))

    mgr.save(config)

    content = configFilePath.read_text(encoding="utf-8")
    assert "hudOffset_box_x: 0" in content
    assert "hudOffset_box_y: 0" in content


def test_load_restores_saved_offset(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))

    configValues = {"hudOffset_box_x": 30, "hudOffset_box_y": 20}
    mgr.load(configValues, 800, 600)

    assert mgr.getOffset("box") == (30, 20)


def test_load_missing_keys_falls_back_to_default(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))

    mgr.load({}, 800, 600)

    assert mgr.getOffset("box") == (0, 0)


def test_load_ignores_malformed_entries(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))

    configValues = {"hudOffset_box_x": "not-a-number", "hudOffset_box_y": 20}
    mgr.load(configValues, 800, 600)

    # Malformed pair is skipped entirely rather than crashing or applying
    # only half of it.
    assert mgr.getOffset("box") == (0, 0)


def test_load_clamps_offset_to_screen_bounds(resolve):
    mgr = resolve(HudDragManager)
    mgr.register("box", make_rect_func(50, 50, 100, 100))

    # A huge saved offset (e.g. from a previous, larger display) should be
    # clamped to the current screen size rather than pushing the element
    # fully off-screen.
    configValues = {"hudOffset_box_x": 100000, "hudOffset_box_y": 0}
    mgr.load(configValues, 800, 600)

    rect = mgr.elements["box"].getRect()
    assert rect.x + rect.width * 0.2 <= 800


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    configFilePath = tmp_path / "config.yml"
    configFilePath.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        Config, "getConfigFilePath", staticmethod(lambda: configFilePath)
    )

    config = Config()
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75)
    mgr.handleMouseUp(150, 90, 800, 600)
    savedOffset = mgr.getOffset("box")
    mgr.save(config)

    # Simulate a fresh process by creating a brand new manager instance.
    mgr2 = HudDragManager()
    mgr2.register("box", make_rect_func(50, 50, 100, 100))
    mgr2.load(Config.readConfigFile(), 800, 600)

    assert mgr2.getOffset("box") == savedOffset
