from src.screen.screenType import ScreenType


def test_screen_type_constants():
    """Test that ScreenType constants are defined correctly"""
    assert ScreenType.MAIN_MENU_SCREEN == "menu_screen"
    assert ScreenType.WORLD_SCREEN == "world_screen"
    assert ScreenType.OPTIONS_SCREEN == "options_screen"
    assert ScreenType.STATS_SCREEN == "stats_screen"
    assert ScreenType.INVENTORY_SCREEN == "inventory_screen"
    assert ScreenType.CONFIG_SCREEN == "config_screen"
    assert ScreenType.NONE == "none_screen"


def test_screen_type_uniqueness():
    """Test that all screen type constants are unique"""
    screen_types = [
        ScreenType.MAIN_MENU_SCREEN,
        ScreenType.WORLD_SCREEN,
        ScreenType.OPTIONS_SCREEN,
        ScreenType.STATS_SCREEN,
        ScreenType.INVENTORY_SCREEN,
        ScreenType.CONFIG_SCREEN,
        ScreenType.NONE
    ]
    
    # Check that all values are unique
    assert len(screen_types) == len(set(screen_types))
    
    # Check that all are strings
    for screen_type in screen_types:
        assert isinstance(screen_type, str)
        assert len(screen_type) > 0