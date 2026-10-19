import pygame
import pytest

from codex.codex import (
    ALL_ENTITY_TYPES,
    ALL_LIVING_ENTITY_TYPES,
    ENTITY_DISPLAY_NAMES,
    ENTITY_IMAGE_PATHS,
)
from rendering.inputEvent import EventType, InputEvent
from rendering.keyCode import KeyCode
from screen.codexScreen import CodexScreen
from screen.screenType import ScreenType
from ui import palette


@pytest.fixture
def pygame_init():
    pygame.init()
    yield
    pygame.quit()


def createCodexScreen(pygame_init, resolve, test_graphik):
    display = pygame.Surface((800, 600))
    test_graphik.getGameDisplay.return_value = display
    return resolve(CodexScreen)


def test_initialization(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    assert screen.scrollOffset == 0
    assert screen.changeScreen is False


def test_switch_to_world_screen(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.switchToReturnScreen()
    assert screen.changeScreen is True
    assert screen.nextScreen == "world_screen"


def test_set_return_screen(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.setReturnScreen("options_screen")
    screen.switchToReturnScreen()
    assert screen.changeScreen is True
    assert screen.nextScreen == "options_screen"


def test_handle_escape_key(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.handleKeyDownEvent(pygame.K_ESCAPE)
    assert screen.changeScreen is True


def test_handle_scroll_event_down(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.handleScrollEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))
    assert screen.scrollOffset == 1


def test_handle_scroll_event_up(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.scrollOffset = 1
    screen.handleScrollEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=1))
    assert screen.scrollOffset == 0


def test_scroll_does_not_go_below_zero(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.handleScrollEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=1))
    assert screen.scrollOffset == 0


def test_all_living_entity_types_defined():
    assert "Bear" in ALL_LIVING_ENTITY_TYPES
    assert "Chicken" in ALL_LIVING_ENTITY_TYPES


def test_all_entity_types_includes_non_living():
    assert "Apple" in ALL_ENTITY_TYPES
    assert "Grass" in ALL_ENTITY_TYPES
    assert "Campfire" in ALL_ENTITY_TYPES
    assert len(ALL_ENTITY_TYPES) > len(ALL_LIVING_ENTITY_TYPES)


def test_codex_screen_shows_discovered(pygame_init, resolve, test_graphik):
    screen = createCodexScreen(pygame_init, resolve, test_graphik)
    screen.codex.discover("Bear")
    assert screen.codex.hasDiscovered("Bear") is True
    assert screen.codex.hasDiscovered("Chicken") is False


# Characterization tests for the key/event dispatch and the draw path, which
# run against the PygameRenderer-spec mock registered by conftest (display
# 1280x720, so 12 of the 37 codex rows fit and the list scrolls).


def _textCalls(renderer, method):
    return [c.args for c in getattr(renderer, method).call_args_list]


def test_codex_key_returns_to_the_return_screen(resolve):
    screen = resolve(CodexScreen)
    screen.setReturnScreen(ScreenType.OPTIONS_SCREEN)

    screen.handleKeyDownEvent(screen.keyBindings.getKey("codex"))

    assert screen.changeScreen is True
    assert screen.nextScreen == ScreenType.OPTIONS_SCREEN


def test_down_and_s_keys_scroll_forward(resolve):
    screen = resolve(CodexScreen)

    screen.handleKeyDownEvent(KeyCode.DOWN)
    screen.handleKeyDownEvent(KeyCode.S)

    assert screen.scrollOffset == 2
    assert screen.changeScreen is False


def test_up_and_w_keys_scroll_back_and_stop_at_zero(resolve):
    screen = resolve(CodexScreen)
    screen.scrollOffset = 2

    screen.handleKeyDownEvent(KeyCode.UP)
    screen.handleKeyDownEvent(KeyCode.W)
    assert screen.scrollOffset == 0

    screen.handleKeyDownEvent(KeyCode.UP)
    assert screen.scrollOffset == 0


def test_unbound_key_changes_nothing(resolve):
    screen = resolve(CodexScreen)
    screen.scrollOffset = 3

    screen.handleKeyDownEvent(KeyCode.A)

    assert screen.scrollOffset == 3
    assert screen.changeScreen is False


def test_handle_event_dispatches_key_down_and_mouse_wheel(resolve):
    screen = resolve(CodexScreen)

    screen.handleEvent(InputEvent(EventType.KEY_DOWN, key=KeyCode.DOWN))
    assert screen.scrollOffset == 1

    screen.handleEvent(InputEvent(EventType.MOUSE_WHEEL, scrollY=-1))
    assert screen.scrollOffset == 2

    screen.handleEvent(InputEvent(EventType.MOUSE_DOWN, position=(0, 0), button=1))
    assert screen.scrollOffset == 2
    assert screen.changeScreen is False


def test_on_start_resets_scroll_offset(resolve):
    screen = resolve(CodexScreen)
    screen.scrollOffset = 7

    screen.onStart()

    assert screen.scrollOffset == 0


def test_draw_title_shows_discovered_count(resolve):
    screen = resolve(CodexScreen)
    screen.codex.discover("Bear")
    screen.codex.discover("Apple")

    screen.drawTitle()

    texts = [args[0] for args in _textCalls(screen.renderer, "drawText")]
    assert "Codex" in texts
    assert f"2 of {len(ALL_ENTITY_TYPES)} discovered" in texts


def test_undiscovered_entries_draw_as_question_marks_without_images(resolve):
    screen = resolve(CodexScreen)

    screen.drawEntries()

    names = _textCalls(screen.renderer, "drawTextLeftAligned")
    assert len(names) == 12
    assert all(args[0] == "???" for args in names)
    assert all(args[4] == palette.DARK_GRAY for args in names)
    screen.renderer.loadImage.assert_not_called()
    screen.renderer.drawImage.assert_not_called()


def test_discovered_entry_draws_display_name_and_scaled_image(resolve):
    # Row 0 is ALL_ENTITY_TYPES[0]; "BearMeat" checks the display-name mapping.
    screen = resolve(CodexScreen)
    first = ALL_ENTITY_TYPES[0]
    screen.codex.discover(first)
    screen.codex.discover("BearMeat")

    screen.drawEntries()

    names = _textCalls(screen.renderer, "drawTextLeftAligned")
    # imageX = 1280 * 0.25 = 320; nameX = 320 + 32 + 16; row 0 at y = 85.
    assert names[0] == (ENTITY_DISPLAY_NAMES[first], 368, 85 + 22.5, 22, palette.WHITE)
    assert "Bear Meat" in [args[0] for args in names]
    screen.renderer.loadImage.assert_any_call(ENTITY_IMAGE_PATHS[first])
    screen.renderer.scaleImage.assert_any_call(
        screen.renderer.loadImage.return_value, (32, 32)
    )
    screen.renderer.drawImage.assert_any_call(
        screen.renderer.scaleImage.return_value, (320, 87)
    )


def test_entity_images_are_loaded_once_and_cached(resolve):
    screen = resolve(CodexScreen)
    screen.codex.discover(ALL_ENTITY_TYPES[0])

    screen.drawEntries()
    screen.drawEntries()

    assert screen.renderer.loadImage.call_count == 1
    assert screen.renderer.drawImage.call_count == 2


def test_entity_without_image_path_yields_no_image(resolve):
    screen = resolve(CodexScreen)

    assert screen._getEntityImage("NotAnEntity") is None
    assert screen._getEntityImage("NotAnEntity") is None
    screen.renderer.loadImage.assert_not_called()


def test_scroll_info_shows_visible_range(resolve):
    screen = resolve(CodexScreen)

    screen.drawEntries()

    texts = [args[0] for args in _textCalls(screen.renderer, "drawText")]
    assert f"1-12 of {len(ALL_ENTITY_TYPES)}" in texts
    assert "Up/Down to see more" in texts


def test_draw_entries_clamps_scroll_offset_past_the_end(resolve):
    screen = resolve(CodexScreen)
    total = len(ALL_ENTITY_TYPES)
    screen.scrollOffset = 1000

    screen.drawEntries()

    assert screen.scrollOffset == total - 12
    names = _textCalls(screen.renderer, "drawTextLeftAligned")
    assert len(names) == 12
    texts = [args[0] for args in _textCalls(screen.renderer, "drawText")]
    assert f"{total - 11}-{total} of {total}" in texts


def test_tall_display_shows_every_entry_without_scroll_info(resolve):
    screen = resolve(CodexScreen)
    screen.renderer.getDisplaySize.return_value = (1280, 85 + 80 + 45 * 40)
    screen.scrollOffset = 5

    screen.drawEntries()

    assert screen.scrollOffset == 0
    names = _textCalls(screen.renderer, "drawTextLeftAligned")
    assert len(names) == len(ALL_ENTITY_TYPES)
    screen.renderer.drawText.assert_not_called()


def test_back_button_returns_to_the_return_screen(resolve):
    screen = resolve(CodexScreen)
    screen.setReturnScreen(ScreenType.OPTIONS_SCREEN)

    screen.drawBackButton()

    args = screen.renderer.drawButton.call_args.args
    # Centered button one fifth of the width, 45px above the bottom edge.
    assert args[:4] == (512, 675, 256, 35)
    assert args[7] == "Back"
    args[8]()
    assert screen.changeScreen is True
    assert screen.nextScreen == ScreenType.OPTIONS_SCREEN


def test_draw_clears_and_draws_title_entries_and_back_button(resolve):
    screen = resolve(CodexScreen)

    screen.draw()

    screen.renderer.clearScreen.assert_called_once_with(palette.BLACK)
    texts = [args[0] for args in _textCalls(screen.renderer, "drawText")]
    assert "Codex" in texts
    assert screen.renderer.drawTextLeftAligned.called
    screen.renderer.drawButton.assert_called_once()
