from rendering.textGrid import TextGrid


def test_write_text_places_characters_left_to_right():
    grid = TextGrid(10, 3)
    grid.writeText(2, 1, "hi")
    assert grid.getChar(2, 1) == "h"
    assert grid.getChar(3, 1) == "i"
    assert grid.toString().splitlines()[1] == "  hi"


def test_writes_are_clipped_to_bounds_without_raising():
    grid = TextGrid(4, 2)
    grid.writeText(2, 0, "abcd")  # runs off the right edge
    grid.setChar(-1, 0, "x")  # off the left edge
    grid.setChar(0, 9, "y")  # off the bottom
    assert grid.getChar(2, 0) == "a"
    assert grid.getChar(3, 0) == "b"  # 'c'/'d' clipped
    assert grid.getChar(-1, 0) is None


def test_fill_rect_fills_a_block():
    grid = TextGrid(5, 5)
    grid.fillRect(1, 1, 2, 2, "#")
    assert grid.getChar(1, 1) == "#"
    assert grid.getChar(2, 2) == "#"
    assert grid.getChar(0, 0) == " "


def test_draw_box_outlines_a_rectangle():
    grid = TextGrid(6, 4)
    grid.drawBox(0, 0, 4, 3)
    assert grid.getChar(0, 0) == "+" and grid.getChar(3, 0) == "+"
    assert grid.getChar(1, 0) == "-"  # top edge
    assert grid.getChar(0, 1) == "|"  # left edge
    assert grid.getChar(1, 1) == " "  # hollow interior


def test_to_string_has_one_newline_separator_per_row_boundary():
    grid = TextGrid(3, 4)
    assert grid.toString().count("\n") == 3  # 4 rows -> 3 separators


def test_set_color_wraps_char_in_ansi_codes():
    grid = TextGrid(5, 2)
    grid.setChar(1, 0, "@")
    grid.setColor(1, 0, 93)  # bright yellow
    line = grid.toString().splitlines()[0]
    assert "\033[93m@\033[0m" in line


def test_uncolored_chars_are_output_plain():
    grid = TextGrid(5, 2)
    grid.setChar(2, 0, ".")
    line = grid.toString().splitlines()[0]
    assert "." in line
    assert "\033[" not in line


def test_color_does_not_affect_trailing_space_strip():
    grid = TextGrid(6, 1)
    grid.setChar(0, 0, "B")
    grid.setColor(0, 0, 31)
    # columns 1-5 remain spaces — should not appear in output
    line = grid.toString()
    assert line.endswith("\033[0m")  # ends at the colored char, no trailing spaces


def test_clear_resets_colors():
    grid = TextGrid(4, 2)
    grid.setChar(0, 0, "#")
    grid.setColor(0, 0, 37)
    grid.clear()
    line = grid.toString().splitlines()[0]
    assert "\033[" not in line


# --- clip region ---

def test_clip_region_restricts_writes():
    grid = TextGrid(6, 4)
    # clip to cols 1-3 (exclusive 3), rows 0-1 (exclusive 1)
    grid.setClipRegion(1, 0, 3, 1)
    grid.setChar(0, 0, "X")   # col 0 is outside clip — should be rejected
    grid.setChar(2, 0, "Y")   # col 2 is inside clip — should land
    assert grid.getChar(0, 0) != "X"
    assert grid.getChar(2, 0) == "Y"


def test_clip_region_none_clears_restriction():
    grid = TextGrid(6, 4)
    grid.setClipRegion(3, 0, 6, 4)   # col 0 excluded
    grid.setChar(0, 0, "A")
    assert grid.getChar(0, 0) != "A"   # blocked by clip
    grid.setClipRegion(None, None, None, None)  # clear
    grid.setChar(0, 0, "B")
    assert grid.getChar(0, 0) == "B"   # now accepted


def test_clip_region_col0_allows_leftmost_column():
    grid = TextGrid(6, 4)
    grid.setClipRegion(0, 0, 4, 4)   # clip starts at col 0
    grid.setChar(0, 0, "Z")
    assert grid.getChar(0, 0) == "Z"


# --- additional edge cases ---

def test_draw_box_with_zero_width_or_height_does_not_raise():
    grid = TextGrid(6, 4)
    grid.drawBox(0, 0, 0, 3)  # zero width
    grid.drawBox(0, 0, 3, 0)  # zero height
    # Grid must be unmodified (all spaces)
    assert grid.getChar(0, 0) == " "


def test_set_color_none_clears_an_existing_color():
    grid = TextGrid(4, 2)
    grid.setChar(1, 0, "X")
    grid.setColor(1, 0, 31)   # red
    grid.setColor(1, 0, None)  # clear
    line = grid.toString().splitlines()[0]
    assert "\033[" not in line


def test_color_not_applied_to_space_cells():
    grid = TextGrid(4, 2)
    # Set a color on a cell that stays a space — toString must skip ANSI wrapping.
    grid.setColor(0, 0, 93)
    line = grid.toString().splitlines()[0]
    assert "\033[93m" not in line


def test_fill_rect_with_zero_dimensions_does_nothing():
    grid = TextGrid(5, 5)
    grid.fillRect(0, 0, 0, 3, "#")  # zero width
    grid.fillRect(0, 0, 3, 0, "#")  # zero height
    assert grid.getChar(0, 0) == " "


def test_write_text_clips_at_right_edge():
    grid = TextGrid(4, 2)
    grid.writeText(3, 0, "abc")   # only "a" fits at col 3; b,c are off the right edge
    assert grid.getChar(3, 0) == "a"
    assert grid.getChar(4, 0) is None  # out of bounds


def test_get_char_out_of_bounds_returns_none():
    grid = TextGrid(4, 2)
    assert grid.getChar(-1, 0) is None
    assert grid.getChar(0, -1) is None
    assert grid.getChar(99, 0) is None


# --- third batch ---

def test_draw_box_2x2_has_all_four_corners_and_no_edges():
    # 2×2 is the smallest box with distinct corners; edge loops produce empty
    # ranges so only "+" appears — no "-" or "|".
    grid = TextGrid(4, 4)
    grid.drawBox(0, 0, 2, 2)
    assert grid.getChar(0, 0) == "+"
    assert grid.getChar(1, 0) == "+"
    assert grid.getChar(0, 1) == "+"
    assert grid.getChar(1, 1) == "+"
    assert grid.getChar(2, 0) == " "  # outside box


def test_draw_box_1x1_places_single_corner_character():
    # All four corner calls target the same cell → just "+".
    grid = TextGrid(6, 4)
    grid.drawBox(2, 1, 1, 1)
    assert grid.getChar(2, 1) == "+"
    assert grid.getChar(0, 0) == " "  # grid otherwise blank


def test_clear_resets_chars_to_space():
    grid = TextGrid(4, 2)
    grid.setChar(0, 0, "X")
    grid.clear()
    assert grid.getChar(0, 0) == " "


def test_write_text_empty_string_is_noop():
    grid = TextGrid(4, 2)
    grid.writeText(0, 0, "")
    assert grid.getChar(0, 0) == " "


def test_to_string_single_row_has_no_newlines():
    grid = TextGrid(5, 1)
    assert grid.toString().count("\n") == 0


def test_fill_rect_all_out_of_bounds_does_nothing():
    grid = TextGrid(4, 2)
    grid.fillRect(10, 10, 3, 3, "#")  # entirely outside bounds
    assert grid.getChar(0, 0) == " "
