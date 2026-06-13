from ui.geometry import Rect
from ui.hudDragManager import HudDragManager


def test_construction_and_basic_attributes():
    r = Rect(10, 20, 30, 40)
    assert (r.x, r.y, r.width, r.height) == (10, 20, 30, 40)


def test_edge_and_center_accessors():
    r = Rect(10, 20, 30, 40)
    assert r.left == 10
    assert r.top == 20
    assert r.right == 40
    assert r.bottom == 60
    assert r.centerx == 25
    assert r.centery == 40
    assert r.center == (25, 40)


def test_collidepoint_is_inclusive_of_top_left_and_exclusive_of_bottom_right():
    r = Rect(10, 10, 20, 20)
    assert r.collidepoint(10, 10)
    assert r.collidepoint(29, 29)
    assert not r.collidepoint(30, 30)
    assert not r.collidepoint(9, 10)


def test_move_returns_a_shifted_copy_without_mutating():
    r = Rect(0, 0, 5, 5)
    moved = r.move(3, 4)
    assert (moved.x, moved.y) == (3, 4)
    assert (r.x, r.y) == (0, 0)


def test_x_y_are_mutable_for_offset_application():
    r = Rect(0, 0, 5, 5)
    r.x += 7
    r.y += 8
    assert (r.x, r.y) == (7, 8)


def test_equality_and_copy():
    r = Rect(1, 2, 3, 4)
    assert r.copy() == r
    assert r != Rect(1, 2, 3, 5)


def test_hud_drag_manager_works_with_geometry_rect():
    # The drag manager is backend-neutral; geometry.Rect must satisfy the same
    # contract pygame.Rect did (mutable x/y, width/height, collidepoint).
    manager = HudDragManager()
    manager.register("box", lambda: Rect(100, 100, 50, 50))

    assert manager.handleMouseDown(120, 120) is True
    manager.handleMouseMotion(140, 130, 800, 600)
    assert manager.getOffset("box") == (20, 10)
    assert manager.handleMouseDown(0, 0) is False
