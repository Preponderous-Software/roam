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
