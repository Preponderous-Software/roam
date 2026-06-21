from rendering.renderer import Renderer
from rendering.textRenderer import TextRenderer, _buildDiff
from textDemo import renderMainMenu


def test_text_renderer_is_a_concrete_renderer():
    # Instantiation fails if any abstract Renderer method is unimplemented.
    assert isinstance(TextRenderer(), Renderer)


def test_display_size_is_columns_times_cell_size():
    renderer = TextRenderer(columns=80, rows=24, cellWidth=8, cellHeight=16)
    assert renderer.getDisplaySize() == (640, 384)
    r = renderer.getGameAreaRect()
    # Game area is pinned to the top and shrunk to leave room for the HUD:
    # availHeight = 384 - (150 + 5 + 384//10 + 10) = 384 - 203 = 181
    # side = min(640, 181) = 181; x = (640 - 181) // 2 = 229
    assert r.y == 0
    assert r.width == r.height          # always square
    assert r.x + r.width <= 640        # stays within display
    assert r.y + r.height <= 384


def test_draw_text_is_centered_on_the_pixel_position():
    renderer = TextRenderer(columns=20, rows=5, cellWidth=10, cellHeight=10)
    # centered at pixel (100, 20) -> cell (10, 2); "abcd" starts at 10 - 2 = 8.
    renderer.drawText("abcd", 100, 20, 12, (255, 255, 255))
    assert renderer.grid.getChar(8, 2) == "a"
    assert renderer.grid.getChar(11, 2) == "d"


def test_draw_text_left_aligned_starts_at_the_left_pixel():
    renderer = TextRenderer(columns=20, rows=5, cellWidth=10, cellHeight=10)
    renderer.drawTextLeftAligned("hi", 30, 25, 12, (255, 255, 255))
    assert renderer.grid.getChar(3, 2) == "h"  # leftX 30 -> col 3, centerY 25 -> row 2


def test_draw_rectangle_fills_with_spaces():
    renderer = TextRenderer(columns=20, rows=10, cellWidth=10, cellHeight=10)
    # Pre-fill the area with a non-space char so we can confirm it was cleared.
    for c in range(4):
        for r in range(3):
            renderer.grid.setChar(c, r, "X")
    renderer.drawRectangle(0, 0, 40, 30, (255, 255, 255))
    assert renderer.grid.getChar(0, 0) == " "  # filled with spaces, not a box corner


def test_load_image_collapses_to_a_glyph_and_draw_image_places_it():
    renderer = TextRenderer(cellWidth=10, cellHeight=10)
    glyph = renderer.loadImage("assets/images/player_down.png")
    assert glyph == "@"
    renderer.drawImage(glyph, (20, 10))
    assert renderer.grid.getChar(2, 1) == "@"


def test_draw_image_applies_ansi_color_for_known_glyphs():
    renderer = TextRenderer(cellWidth=10, cellHeight=10)
    renderer.drawImage("@", (0, 0))   # player — bright yellow (93)
    frame = renderer.grid.toString()
    assert "\033[93m@\033[0m" in frame


def test_draw_image_no_color_for_unknown_glyphs():
    renderer = TextRenderer(cellWidth=10, cellHeight=10)
    renderer.drawImage("?", (0, 0))   # not in color map
    frame = renderer.grid.toString()
    assert "\033[" not in frame


def test_game_area_rect_does_not_overlap_hud():
    renderer = TextRenderer(columns=80, rows=24, cellWidth=8, cellHeight=16)
    r = renderer.getGameAreaRect()
    _, displayH = renderer.getDisplaySize()
    from ui.hotbarLayout import HOTBAR_BOTTOM_OFFSET
    # game area must end above the hotbar top
    assert r.y + r.height <= displayH - HOTBAR_BOTTOM_OFFSET


def test_present_only_outputs_when_the_frame_changes():
    frames = []
    renderer = TextRenderer(output=frames.append)
    renderer.clearScreen((0, 0, 0))
    renderer.drawText("hi", 80, 16, 12, (255, 255, 255))
    renderer.present()
    renderer.present()  # nothing changed -> no repaint
    assert len(frames) == 1
    renderer.clearScreen((0, 0, 0))
    renderer.drawText("bye", 80, 16, 12, (255, 255, 255))
    renderer.present()  # changed -> repaint
    assert len(frames) == 2


def test_a_real_screen_renders_to_text_with_no_pygame():
    # The payoff: MainMenuScreen drawn through the text frontend produces a
    # recognizable menu — same screen logic, different backend, no pygame.
    frame = renderMainMenu()
    assert "Roam" in frame
    assert "Play" in frame
    assert "Quit" in frame
    assert "Settings" in frame


# --- _buildDiff: differential rendering tests ---

def test_build_diff_first_frame_positions_rows_explicitly():
    diff = _buildDiff(["hello", "world"], [])
    # Each row must be written at an explicit position so \r\n on the last row
    # never triggers a terminal scroll (which would shift all content up by one
    # line, causing duplicate HUD elements on stable rows).
    assert "\033[1;1H" in diff       # row 1 positioned explicitly
    assert "\033[2;1H" in diff       # row 2 positioned explicitly
    assert "hello" in diff
    assert "world" in diff
    assert "\033[K" in diff          # erase-to-EOL present
    assert "\033[2J" not in diff     # NO full-screen clear
    assert "\r\n" not in diff        # NO \r\n — that would scroll on last row


def test_build_diff_subsequent_frame_only_updates_changed_lines():
    old = ["line A", "line B", "line C"]
    new = ["line A", "line X", "line C"]   # only row 1 changed
    diff = _buildDiff(new, old)
    assert "line X" in diff
    assert "line A" not in diff    # unchanged — not retransmitted
    assert "line C" not in diff    # unchanged — not retransmitted
    assert "\033[2;1H" in diff     # jumped to row 2 (1-based)
    assert "\033[2J" not in diff   # NO full-screen clear


def test_build_diff_erases_lines_that_disappeared():
    old = ["row0", "row1", "row2"]
    new = ["row0"]                 # two rows removed
    diff = _buildDiff(new, old)
    assert "\033[2;1H\033[2K" in diff   # row 2 blanked
    assert "\033[3;1H\033[2K" in diff   # row 3 blanked


def test_build_diff_identical_frames_produce_empty_string():
    lines = ["same", "content"]
    diff = _buildDiff(lines, lines[:])
    assert diff == ""


def test_present_output_contains_no_full_screen_clear():
    frames = []
    renderer = TextRenderer(output=frames.append)
    renderer.clearScreen((0, 0, 0))
    renderer.drawText("hi", 80, 16, 12, (255, 255, 255))
    renderer.present()
    assert len(frames) == 1
    assert "\033[2J" not in frames[0]   # flicker-free: no full clear


# --- drawImage edge clamping (max(0, col)) ---

def test_draw_image_at_negative_x_clamps_to_col_0():
    # Tile positioned at -1px (the 1px left-overlap from room.drawWithOffset)
    # must land at col 0, not be silently dropped.
    renderer = TextRenderer(columns=20, rows=5, cellWidth=8, cellHeight=16)
    renderer.drawImage("@", (-1, 0))
    assert renderer.grid.getChar(0, 0) == "@"


def test_draw_image_at_exact_zero_places_at_col_0():
    renderer = TextRenderer(columns=20, rows=5, cellWidth=8, cellHeight=16)
    renderer.drawImage("@", (0, 0))
    assert renderer.grid.getChar(0, 0) == "@"


def test_draw_image_at_negative_y_clamps_to_row_0():
    renderer = TextRenderer(columns=20, rows=5, cellWidth=8, cellHeight=16)
    renderer.drawImage("@", (0, -1))
    assert renderer.grid.getChar(0, 0) == "@"


def test_draw_image_far_negative_x_clamped_but_clip_hides_it():
    # Glyph clamps to col 0, but if the clip region starts at col 5 the cell
    # is still rejected by the clip — prevents off-screen tiles leaking in.
    from ui.geometry import Rect
    renderer = TextRenderer(columns=20, rows=5, cellWidth=8, cellHeight=16)
    renderer.setClipRegion(Rect(40, 0, 80, 80))  # clip starts at col 5
    renderer.drawImage("@", (-1, 0))
    char = renderer.grid.getChar(0, 0)
    assert char != "@"


# --- setClipRegion left-extension (max(0, _col(x) - 1)) ---

def test_set_clip_region_extends_left_by_one_cell():
    # Rect at x=8 maps to _col(8)=1; the fix subtracts 1 → clip starts at
    # col 0. A char written at x=0 (col 0) must therefore pass the clip.
    from ui.geometry import Rect
    renderer = TextRenderer(columns=20, rows=5, cellWidth=8, cellHeight=16)
    renderer.setClipRegion(Rect(8, 0, 80, 80))
    renderer.drawImage("#", (0, 0))   # pixel 0 → col 0, inside extended clip
    assert renderer.grid.getChar(0, 0) == "#"


def test_set_clip_region_none_removes_restriction():
    from ui.geometry import Rect
    renderer = TextRenderer(columns=20, rows=5, cellWidth=8, cellHeight=16)
    renderer.setClipRegion(Rect(40, 0, 80, 80))   # col 0 excluded
    renderer.drawImage("X", (0, 0))
    assert renderer.grid.getChar(0, 0) != "X"
    renderer.setClipRegion(None)
    renderer.drawImage("Y", (0, 0))
    assert renderer.grid.getChar(0, 0) == "Y"


def test_left_edge_tile_visible_when_game_area_starts_at_pixel_0():
    # Regression: when gameArea.x=0, tile at -1px → col -1 was silently
    # dropped. Now clamps to col 0 and the clip (extended by 1) lets it through.
    from ui.geometry import Rect
    renderer = TextRenderer(columns=20, rows=5, cellWidth=8, cellHeight=16)
    renderer.setClipRegion(Rect(0, 0, 80, 80))
    renderer.drawImage("[", (-1, 0))   # chest at leftmost tile column
    assert renderer.grid.getChar(0, 0) == "["


# --- drawSelectionHighlight ---

def test_draw_selection_highlight_colors_cells_yellow_without_erasing_glyphs():
    renderer = TextRenderer(columns=10, rows=5, cellWidth=8, cellHeight=16)
    renderer.drawImage("@", (0, 0))
    renderer.drawSelectionHighlight(0, 0, 8, 16, None)
    assert renderer.grid.getChar(0, 0) == "@"     # glyph preserved
    assert renderer.grid._colors[0][0] == 93       # bright yellow


# --- drawTranslucentOverlay ---

def test_draw_translucent_overlay_dims_all_cells():
    renderer = TextRenderer(columns=10, rows=5, cellWidth=8, cellHeight=16)
    renderer.drawImage("@", (0, 0))
    renderer.drawTranslucentOverlay((0, 0, 0))
    assert renderer.grid._colors[0][0] == 90   # dark grey


# --- drawDayNightOverlay ---

def test_draw_day_night_overlay_dims_cells_in_game_area():
    renderer = TextRenderer(columns=20, rows=10, cellWidth=8, cellHeight=16)
    # Place a non-player tile so no implicit light source interferes.
    renderer.drawImage(".", (0, 0))
    renderer.drawDayNightOverlay((0, 0, 80, 64), 200, [])
    # At full darkness (opacity=200) all cells in the area must have a color set.
    color = renderer.grid._colors[0][0]
    assert color is not None


def test_draw_day_night_overlay_skips_at_low_opacity():
    renderer = TextRenderer(columns=20, rows=10, cellWidth=8, cellHeight=16)
    renderer.drawDayNightOverlay((0, 0, 80, 64), 20, [])   # below threshold of 30
    assert renderer.grid._colors[0][0] is None   # nothing dimmed


# --- resize ---

def test_resize_rebuilds_grid_and_forces_full_repaint():
    frames = []
    renderer = TextRenderer(columns=10, rows=5, cellWidth=8, cellHeight=16, output=frames.append)
    renderer.drawImage("@", (0, 0))
    renderer.present()
    assert len(frames) == 1

    renderer.resize(12, 6)
    # Old char must be gone — grid was rebuilt
    assert renderer.grid.getChar(0, 0) != "@"
    # present must re-output a full frame (lastFrame reset to None)
    renderer.drawImage("#", (0, 0))
    renderer.present()
    assert len(frames) == 2
