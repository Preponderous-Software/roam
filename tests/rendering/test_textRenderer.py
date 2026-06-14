from rendering.renderer import Renderer
from rendering.textRenderer import TextRenderer
from textDemo import renderMainMenu


def test_text_renderer_is_a_concrete_renderer():
    # Instantiation fails if any abstract Renderer method is unimplemented.
    assert isinstance(TextRenderer(), Renderer)


def test_display_size_is_columns_times_cell_size():
    renderer = TextRenderer(columns=80, rows=24, cellWidth=8, cellHeight=16)
    assert renderer.getDisplaySize() == (640, 384)
    r = renderer.getGameAreaRect()
    assert (r.x, r.y, r.width, r.height) == (128, 0, 384, 384)


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


def test_draw_rectangle_outlines_a_box():
    renderer = TextRenderer(columns=20, rows=10, cellWidth=10, cellHeight=10)
    renderer.drawRectangle(0, 0, 40, 30, (255, 255, 255))
    assert renderer.grid.getChar(0, 0) == "+"  # corner of the 4x3-cell box


def test_load_image_collapses_to_a_glyph_and_draw_image_places_it():
    renderer = TextRenderer(cellWidth=10, cellHeight=10)
    glyph = renderer.loadImage("assets/images/player_down.png")
    assert glyph == "@"
    renderer.drawImage(glyph, (20, 10))
    assert renderer.grid.getChar(2, 1) == "@"


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
