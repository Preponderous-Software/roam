from ui import palette

# Every public constant in the palette, so the suite guards against a malformed
# entry (wrong length, out-of-range channel) being introduced.
ALL_COLORS = {
    name: value
    for name, value in vars(palette).items()
    if name.isupper() and not name.startswith("_")
}


def test_palette_exposes_named_colors():
    assert "WHITE" in ALL_COLORS
    assert "BLACK" in ALL_COLORS
    assert len(ALL_COLORS) >= 10


def test_every_color_is_a_valid_rgb_tuple():
    for name, value in ALL_COLORS.items():
        assert isinstance(value, tuple), name
        assert len(value) == 3, name
        for channel in value:
            assert isinstance(channel, int), name
            assert 0 <= channel <= 255, name


def test_grayscale_ramp_is_ordered_light_to_dark():
    ramp = [
        palette.WHITE,
        palette.LIGHT_GRAY,
        palette.GRAY,
        palette.MEDIUM_GRAY,
        palette.DIM_GRAY,
        palette.DARK_GRAY,
        palette.DARKER_GRAY,
        palette.CHARCOAL,
        palette.NEAR_BLACK,
        palette.BLACK,
    ]
    brightnesses = [sum(color) for color in ramp]
    assert brightnesses == sorted(brightnesses, reverse=True)


def test_white_and_black_are_extremes():
    assert palette.WHITE == (255, 255, 255)
    assert palette.BLACK == (0, 0, 0)
