from ui.energyBar import EnergyBar


# Coverage for the EnergyBar HUD widget (sibling of ui/status, which has a test
# but EnergyBar did not): its default layout rect and a headless draw smoke.


def test_default_rect_spans_full_width_at_the_bottom(resolve):
    bar = resolve(EnergyBar)
    width, height = bar.renderer.getDisplaySize()

    rect = bar.getDefaultRect()

    assert rect.x == 0
    assert rect.width == width  # full display width
    assert rect.height == height / 64
    assert rect.y == height - height / 64  # flush to the bottom edge


def test_draw_renders_the_bar_through_the_renderer(resolve):
    # Headless smoke: the bar's draw path (black frame, white interior, energy
    # fill, centered text) must run against the renderer without raising.
    bar = resolve(EnergyBar)

    bar.draw()

    assert bar.renderer.drawRectangle.called
    assert bar.renderer.drawText.called
