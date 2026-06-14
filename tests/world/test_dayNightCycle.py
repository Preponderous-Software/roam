from world.dayNightCycle import DayNightCycle


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
