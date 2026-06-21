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


# --- text mode (_drawText) ---


def _textModeBar(energy, target):
    """Return an EnergyBar wired to a real TextRenderer with the given energy."""
    from unittest.mock import MagicMock
    from rendering.textRenderer import TextRenderer
    from ui.energyBar import EnergyBar

    renderer = TextRenderer(columns=80, rows=24, cellWidth=8, cellHeight=16)
    player = MagicMock()
    player.getEnergy.return_value = energy
    player.getTargetEnergy.return_value = target

    bar = EnergyBar.__new__(EnergyBar)
    bar.renderer = renderer
    bar.player = player
    return bar, renderer


def test_text_mode_full_energy_renders_full_bar():
    bar, renderer = _textModeBar(300, 300)
    bar._drawText(0, 0, 1.0)
    frame = renderer.grid.toString()
    assert "E:[" in frame
    assert "300/300" in frame
    assert "=" * 16 in frame  # all 16 slots filled


def test_text_mode_empty_energy_renders_empty_bar():
    bar, renderer = _textModeBar(0, 300)
    bar._drawText(0, 0, 0.0)
    frame = renderer.grid.toString()
    assert "E:[" in frame
    assert "0/300" in frame
    assert "=" not in frame.split("[")[1].split("]")[0]  # no fills in bar section


def test_text_mode_half_energy_renders_half_bar():
    bar, renderer = _textModeBar(150, 300)
    bar._drawText(0, 0, 0.5)
    frame = renderer.grid.toString()
    bracket_content = frame.split("[")[1].split("]")[0]
    assert bracket_content == "=" * 8 + " " * 8
