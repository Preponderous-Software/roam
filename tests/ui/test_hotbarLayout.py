from ui.hotbarLayout import (
    HOTBAR_BOTTOM_OFFSET,
    HOTBAR_PADDING,
    HOTBAR_SLOT_SIZE,
    getHotbarTop,
)


def test_get_hotbar_top_offsets_up_from_the_display_bottom():
    assert getHotbarTop(600) == 600 - HOTBAR_BOTTOM_OFFSET - HOTBAR_PADDING
    assert getHotbarTop(1080) == 1080 - HOTBAR_BOTTOM_OFFSET - HOTBAR_PADDING


def test_bottom_offset_is_three_slot_sizes():
    assert HOTBAR_BOTTOM_OFFSET == HOTBAR_SLOT_SIZE * 3
