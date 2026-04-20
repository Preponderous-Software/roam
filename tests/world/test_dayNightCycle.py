import pytest
import pygame

from world.dayNightCycle import DayNightCycle


@pytest.fixture
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


def createDayNightCycle(resolve, test_config, cycleLengthTicks=43200):
    test_config.dayNightCycleLengthTicks = cycleLengthTicks
    return resolve(DayNightCycle)


def test_midday_opacity_is_zero(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    # tick 0 is midday
    assert cycle.getOverlayOpacity(0) == 0
    # tick 1000 is also midday (full cycle)
    assert cycle.getOverlayOpacity(1000) == 0


def test_midnight_opacity_is_max(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    # halfway point (tick 500) is midnight
    assert cycle.getOverlayOpacity(500) == 200


def test_dusk_opacity_is_half(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    # quarter point (tick 250) is dusk — should be ~100
    assert cycle.getOverlayOpacity(250) == 100


def test_dawn_opacity_is_half(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    # three-quarter point (tick 750) is dawn — should be ~100
    assert cycle.getOverlayOpacity(750) == 100


def test_opacity_wraps_around_cycle(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    # tick 1500 is same as tick 500 (midnight)
    assert cycle.getOverlayOpacity(1500) == 200


def test_opacity_returns_int(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    result = cycle.getOverlayOpacity(123)
    assert isinstance(result, int)


def test_opacity_range(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    for tick in range(0, 1000, 10):
        opacity = cycle.getOverlayOpacity(tick)
        assert 0 <= opacity <= 200


def test_zero_cycle_length_returns_zero_opacity(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 0)
    assert cycle.getOverlayOpacity(100) == 0


def test_phase_at_midday(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    assert cycle.getPhase(0) == "day"


def test_phase_at_dusk(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    assert cycle.getPhase(250) == "dusk"


def test_phase_at_midnight(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    assert cycle.getPhase(500) == "night"


def test_phase_at_dawn(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    assert cycle.getPhase(750) == "dawn"


def test_phase_wraps_around(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    assert cycle.getPhase(1000) == "day"
    assert cycle.getPhase(1250) == "dusk"
    assert cycle.getPhase(1500) == "night"
    assert cycle.getPhase(1750) == "dawn"


def test_phase_zero_cycle_length(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 0)
    assert cycle.getPhase(100) == "day"


def test_default_cycle_length(resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 54000)
    assert cycle.getOverlayOpacity(0) == 0
    assert cycle.getOverlayOpacity(27000) == 200


def test_get_light_mask_returns_surface(pygame_init, resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    mask = cycle.getLightMask(50)
    assert mask.get_width() == 100
    assert mask.get_height() == 100


def test_get_light_mask_is_cached(pygame_init, resolve, test_config):
    cycle = createDayNightCycle(resolve, test_config, 1000)
    mask1 = cycle.getLightMask(50)
    mask2 = cycle.getLightMask(50)
    assert mask1 is mask2


def test_get_light_mask_center_is_transparent(pygame_init, resolve, test_config):
    """Center of the light mask should have alpha near 0 (lit area)."""
    cycle = createDayNightCycle(resolve, test_config, 1000)
    mask = cycle.getLightMask(50)
    centerAlpha = mask.get_at((50, 50))[3]
    assert centerAlpha <= 5


def test_get_light_mask_corner_is_opaque(pygame_init, resolve, test_config):
    """Corners of the light mask (outside radius) should stay at alpha 255."""
    cycle = createDayNightCycle(resolve, test_config, 1000)
    mask = cycle.getLightMask(50)
    cornerAlpha = mask.get_at((0, 0))[3]
    assert cornerAlpha == 255


def test_get_light_mask_edge_approaches_opaque(pygame_init, resolve, test_config):
    """A pixel just inside the radius edge should have high alpha."""
    cycle = createDayNightCycle(resolve, test_config, 1000)
    mask = cycle.getLightMask(50)
    # pixel at (50, 2) is ~48 pixels from center → distance/radius ≈ 0.96
    edgeAlpha = mask.get_at((50, 2))[3]
    assert edgeAlpha >= 200


def test_clear_light_mask_cache(pygame_init, resolve, test_config):
    """clearLightMaskCache should discard cached masks so a new surface is returned."""
    cycle = createDayNightCycle(resolve, test_config, 1000)
    mask1 = cycle.getLightMask(50)
    cycle.clearLightMaskCache()
    mask2 = cycle.getLightMask(50)
    assert mask1 is not mask2


def test_get_light_mask_zero_radius(pygame_init, resolve, test_config):
    """getLightMask with radius 0 should not crash and return a valid mask."""
    cycle = createDayNightCycle(resolve, test_config, 1000)
    mask = cycle.getLightMask(0)
    assert mask.get_width() == 2
    assert mask.get_height() == 2
    # clamped to radius=1 so center should be transparent, corners opaque
    centerAlpha = mask.get_at((1, 1))[3]
    assert centerAlpha <= 5
    cornerAlpha = mask.get_at((0, 0))[3]
    assert cornerAlpha == 255


def test_get_light_mask_negative_radius(pygame_init, resolve, test_config):
    """getLightMask with negative radius should not crash and return a valid mask."""
    cycle = createDayNightCycle(resolve, test_config, 1000)
    mask = cycle.getLightMask(-5)
    assert mask.get_width() == 2
    assert mask.get_height() == 2
    centerAlpha = mask.get_at((1, 1))[3]
    assert centerAlpha <= 5
