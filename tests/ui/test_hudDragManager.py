import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()

from src.ui.hudDragManager import HudDragManager, clampPosition


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


def test_register_and_get_offset():
    mgr = HudDragManager()
    mgr.register("test", make_rect_func(10, 20, 100, 50))
    assert mgr.getOffset("test") == (0, 0)


def test_get_offset_unregistered():
    mgr = HudDragManager()
    assert mgr.getOffset("nonexistent") == (0, 0)


def test_is_dragging_false_by_default():
    mgr = HudDragManager()
    assert mgr.isDragging() is False


def test_handle_mouse_down_starts_drag():
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    result = mgr.handleMouseDown(75, 75, 800, 600)
    assert result is True
    assert mgr.isDragging() is True


def test_handle_mouse_down_misses_element():
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    result = mgr.handleMouseDown(200, 200, 800, 600)
    assert result is False
    assert mgr.isDragging() is False


def test_drag_updates_offset():
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75, 800, 600)
    mgr.handleMouseMotion(125, 125, 800, 600)
    ox, oy = mgr.getOffset("box")
    assert ox == 50
    assert oy == 50


def test_drag_completes_on_mouse_up():
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75, 800, 600)
    result = mgr.handleMouseUp(125, 125, 800, 600)
    assert result is True
    assert mgr.isDragging() is False
    ox, oy = mgr.getOffset("box")
    assert ox == 50
    assert oy == 50


def test_mouse_up_without_drag():
    mgr = HudDragManager()
    result = mgr.handleMouseUp(100, 100, 800, 600)
    assert result is False


def test_drag_clamped_at_screen_edge():
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75, 800, 600)
    # try to drag way off the right edge
    mgr.handleMouseMotion(5000, 75, 800, 600)
    ox, oy = mgr.getOffset("box")
    # the element should be clamped so at least 20% visible
    rect = mgr.elements["box"].getRect()
    assert rect.x + rect.width * 0.2 <= 800


def test_drag_clamped_at_top_edge():
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75, 800, 600)
    mgr.handleMouseMotion(75, -5000, 800, 600)
    rect = mgr.elements["box"].getRect()
    assert rect.y + rect.height * 0.2 <= 600


def test_offset_persists_after_drag():
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    mgr.handleMouseDown(75, 75, 800, 600)
    mgr.handleMouseUp(175, 175, 800, 600)
    # Start a second drag
    mgr.handleMouseDown(175, 175, 800, 600)
    mgr.handleMouseUp(225, 225, 800, 600)
    ox, oy = mgr.getOffset("box")
    assert ox == 150
    assert oy == 150


def test_motion_without_drag_is_noop():
    mgr = HudDragManager()
    mgr.register("box", make_rect_func(50, 50, 100, 100))
    result = mgr.handleMouseMotion(100, 100, 800, 600)
    assert result is False
    assert mgr.getOffset("box") == (0, 0)
