from unittest.mock import MagicMock


from src.world.dayNightCycle import DayNightCycle


def createDayNightCycle(cycleLengthTicks=43200):
    config = MagicMock()
    config.dayNightCycleLengthTicks = cycleLengthTicks
    return DayNightCycle(config)


def test_midday_opacity_is_zero():
    cycle = createDayNightCycle(1000)
    # tick 0 is midday
    assert cycle.getOverlayOpacity(0) == 0
    # tick 1000 is also midday (full cycle)
    assert cycle.getOverlayOpacity(1000) == 0


def test_midnight_opacity_is_max():
    cycle = createDayNightCycle(1000)
    # halfway point (tick 500) is midnight
    assert cycle.getOverlayOpacity(500) == 200


def test_dusk_opacity_is_half():
    cycle = createDayNightCycle(1000)
    # quarter point (tick 250) is dusk — should be ~100
    assert cycle.getOverlayOpacity(250) == 100


def test_dawn_opacity_is_half():
    cycle = createDayNightCycle(1000)
    # three-quarter point (tick 750) is dawn — should be ~100
    assert cycle.getOverlayOpacity(750) == 100


def test_opacity_wraps_around_cycle():
    cycle = createDayNightCycle(1000)
    # tick 1500 is same as tick 500 (midnight)
    assert cycle.getOverlayOpacity(1500) == 200


def test_opacity_returns_int():
    cycle = createDayNightCycle(1000)
    result = cycle.getOverlayOpacity(123)
    assert isinstance(result, int)


def test_opacity_range():
    cycle = createDayNightCycle(1000)
    for tick in range(0, 1000, 10):
        opacity = cycle.getOverlayOpacity(tick)
        assert 0 <= opacity <= 200


def test_zero_cycle_length_returns_zero_opacity():
    cycle = createDayNightCycle(0)
    assert cycle.getOverlayOpacity(100) == 0


def test_phase_at_midday():
    cycle = createDayNightCycle(1000)
    assert cycle.getPhase(0) == "day"


def test_phase_at_dusk():
    cycle = createDayNightCycle(1000)
    assert cycle.getPhase(250) == "dusk"


def test_phase_at_midnight():
    cycle = createDayNightCycle(1000)
    assert cycle.getPhase(500) == "night"


def test_phase_at_dawn():
    cycle = createDayNightCycle(1000)
    assert cycle.getPhase(750) == "dawn"


def test_phase_wraps_around():
    cycle = createDayNightCycle(1000)
    assert cycle.getPhase(1000) == "day"
    assert cycle.getPhase(1250) == "dusk"
    assert cycle.getPhase(1500) == "night"
    assert cycle.getPhase(1750) == "dawn"


def test_phase_zero_cycle_length():
    cycle = createDayNightCycle(0)
    assert cycle.getPhase(100) == "day"


def test_default_cycle_length():
    cycle = createDayNightCycle(43200)
    assert cycle.getOverlayOpacity(0) == 0
    assert cycle.getOverlayOpacity(21600) == 200
