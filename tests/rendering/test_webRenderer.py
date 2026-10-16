import json

from rendering.renderer import Renderer
from rendering.webRenderer import WebRenderer
from ui.geometry import Rect


class _FakeInputSource:
    def __init__(self, position=(0, 0), buttons=(False, False, False)):
        self.position = position
        self.buttons = buttons
        self.consumed = 0

    def getMousePosition(self):
        return self.position

    def getMouseButtons(self):
        return self.buttons

    def consumeLeftClick(self):
        self.consumed += 1
        self.buttons = (False,) + tuple(self.buttons[1:])


def _rendererCapturing(**kwargs):
    sent = []
    return WebRenderer(sent.append, **kwargs), sent


def _calls(payload):
    return json.loads(payload)["calls"]


def test_is_an_instantiable_renderer_with_default_size():
    renderer, _ = _rendererCapturing()
    assert isinstance(renderer, Renderer)
    assert renderer.getDisplaySize() == (800, 600)
    assert renderer.getDisplayWidth() == 800
    assert renderer.getDisplayHeight() == 600


def test_supports_image_loading_and_returns_paths_as_images():
    renderer, _ = _rendererCapturing()
    assert renderer.supportsImageLoading() is True
    assert renderer.loadImage("assets/images/grass.png") == "assets/images/grass.png"
    assert renderer.tryLoadImage("anything.png") is None
    assert renderer.captureScreenshot() is False


def test_resize_coerces_to_int():
    renderer, _ = _rendererCapturing()
    renderer.resize(1024.7, "300")
    assert renderer.getDisplaySize() == (1024, 300)


def test_game_area_rect_is_a_centred_square_on_a_wide_display():
    renderer, _ = _rendererCapturing(width=800, height=600)
    rect = renderer.getGameAreaRect()
    assert isinstance(rect, Rect)
    assert (rect.x, rect.y, rect.width, rect.height) == (100, 0, 600, 600)


def test_game_area_rect_is_a_centred_square_on_a_tall_display():
    renderer, _ = _rendererCapturing(width=400, height=700)
    rect = renderer.getGameAreaRect()
    assert (rect.x, rect.y, rect.width, rect.height) == (0, 150, 400, 400)


def test_present_sends_one_compact_json_frame_and_clears_calls():
    renderer, sent = _rendererCapturing(width=320, height=240)
    renderer.clearScreen((1, 2, 3, 99))
    renderer.drawRectangle(1.9, 2, 3, 4, (10, 20, 30))
    renderer.present()
    assert len(sent) == 1
    assert " " not in sent[0]
    frame = json.loads(sent[0])
    assert frame["type"] == "frame"
    assert (frame["w"], frame["h"]) == (320, 240)
    assert frame["calls"] == [
        {"op": "clear", "color": [1, 2, 3]},
        {"op": "rect", "x": 1, "y": 2, "w": 3, "h": 4, "color": [10, 20, 30]},
    ]
    renderer.present()
    assert len(sent) == 1  # nothing drawn since the last present


def test_present_skips_a_frame_identical_to_the_last_one_sent():
    renderer, sent = _rendererCapturing()
    renderer.clearScreen((0, 0, 0))
    renderer.present()
    renderer.clearScreen((0, 0, 0))
    renderer.present()
    assert len(sent) == 1
    renderer.clearScreen((9, 9, 9))
    renderer.present()
    assert len(sent) == 2


def test_present_with_no_calls_sends_nothing():
    renderer, sent = _rendererCapturing()
    renderer.present()
    assert sent == []


def test_text_calls_record_alignment():
    renderer, sent = _rendererCapturing()
    renderer.drawText(42, 10, 20, 18, (255, 255, 255))
    renderer.drawTextLeftAligned("hi", 1, 2, 12, (0, 0, 0))
    renderer.present()
    centred, left = _calls(sent[0])
    assert centred == {
        "op": "text",
        "text": "42",
        "x": 10,
        "y": 20,
        "size": 18,
        "color": [255, 255, 255],
        "align": "c",
    }
    assert left["align"] == "l"
    assert left["text"] == "hi"


def test_draw_image_accepts_a_path_and_a_tuple_position():
    renderer, sent = _rendererCapturing()
    renderer.drawImage("a.png", (3.5, 4))
    renderer.present()
    assert _calls(sent[0]) == [{"op": "img", "path": "a.png", "x": 3, "y": 4}]


def test_scaled_image_carries_its_size_into_the_draw_call():
    renderer, sent = _rendererCapturing()
    scaled = renderer.scaleImage("a.png", (16.2, 32))
    assert scaled == {"path": "a.png", "w": 16, "h": 32}
    rescaled = renderer.scaleImage(scaled, (8, 8))
    assert rescaled == {"path": "a.png", "w": 8, "h": 8}
    renderer.drawImage(scaled, Rect(5, 6, 1, 1))
    renderer.present()
    assert _calls(sent[0]) == [
        {"op": "img", "path": "a.png", "w": 16, "h": 32, "x": 5, "y": 6}
    ]


def test_translucent_overlay_defaults_alpha_to_128():
    renderer, sent = _rendererCapturing()
    renderer.drawTranslucentOverlay((1, 2, 3))
    renderer.drawTranslucentOverlay((1, 2, 3, 200))
    renderer.present()
    assert [c["color"] for c in _calls(sent[0])] == [[1, 2, 3, 128], [1, 2, 3, 200]]


def test_day_night_overlay_accepts_a_rect_or_a_tuple():
    renderer, sent = _rendererCapturing()
    renderer.drawDayNightOverlay(Rect(1, 2, 3, 4), 120.6, [(5, 6.9, 7)])
    renderer.drawDayNightOverlay((8, 9, 10, 11), 0, [])
    renderer.present()
    first, second = _calls(sent[0])
    assert first == {
        "op": "daynight",
        "opacity": 120,
        "lights": [[5, 6, 7]],
        "rect": [1, 2, 3, 4],
    }
    assert second["rect"] == [8, 9, 10, 11]
    assert second["lights"] == []


def test_clip_region_emits_clip_and_unclip():
    renderer, sent = _rendererCapturing()
    renderer.setClipRegion(Rect(1, 2, 3, 4))
    renderer.setClipRegion(None)
    renderer.present()
    assert _calls(sent[0]) == [
        {"op": "clip", "x": 1, "y": 2, "w": 3, "h": 4},
        {"op": "unclip"},
    ]


def test_offscreen_target_discards_draw_calls_and_suppresses_present():
    renderer, sent = _rendererCapturing()
    screen = renderer.getRenderTarget()
    surface = renderer.createSurface((10, 10))
    renderer.setRenderTarget(surface)
    assert renderer.getRenderTarget() is surface
    renderer.drawRectangle(0, 0, 1, 1, (1, 1, 1))
    renderer.present()
    assert sent == []
    renderer.setRenderTarget(None)
    assert renderer.getRenderTarget() is screen
    renderer.clearScreen((2, 2, 2))
    renderer.present()
    assert _calls(sent[0]) == [{"op": "clear", "color": [2, 2, 2]}]


def test_button_fires_callback_and_consumes_click_when_left_pressed_inside():
    source = _FakeInputSource(position=(15, 25), buttons=(True, False, False))
    renderer, sent = _rendererCapturing(inputSource=source)
    clicks = []
    renderer.drawButton(
        10, 20, 30, 40, (1, 1, 1), (2, 2, 2), 12, "OK", lambda: clicks.append(1)
    )
    assert clicks == [1]
    assert source.consumed == 1
    # A second frame with the click already consumed must not re-fire.
    renderer.drawButton(
        10, 20, 30, 40, (1, 1, 1), (2, 2, 2), 12, "OK", lambda: clicks.append(1)
    )
    assert clicks == [1]
    renderer.present()
    assert _calls(sent[0])[0] == {
        "op": "button",
        "x": 10,
        "y": 20,
        "w": 30,
        "h": 40,
        "bc": [1, 1, 1],
        "tc": [2, 2, 2],
        "text": "OK",
    }


def test_button_hit_test_excludes_the_right_and_bottom_edges():
    clicks = []
    for position in [(40, 25), (15, 60), (9, 25)]:
        source = _FakeInputSource(position=position, buttons=(True, False, False))
        renderer, _ = _rendererCapturing(inputSource=source)
        renderer.drawButton(
            10, 20, 30, 40, (0, 0, 0), (0, 0, 0), 12, "", lambda: clicks.append(1)
        )
    assert clicks == []


def test_button_ignores_a_right_click():
    source = _FakeInputSource(position=(15, 25), buttons=(False, False, True))
    renderer, _ = _rendererCapturing(inputSource=source)
    clicks = []
    renderer.drawButton(
        10, 20, 30, 40, (0, 0, 0), (0, 0, 0), 12, "", lambda: clicks.append(1)
    )
    assert clicks == []


def test_button_without_input_source_only_draws():
    renderer, sent = _rendererCapturing()
    renderer.drawButton(0, 0, 10, 10, (0, 0, 0), (0, 0, 0), 12, "x", lambda: 1 / 0)
    renderer.present()
    assert _calls(sent[0])[0]["op"] == "button"


def test_button_on_an_offscreen_target_does_not_fire():
    source = _FakeInputSource(position=(5, 5), buttons=(True, False, False))
    renderer, _ = _rendererCapturing(inputSource=source)
    renderer.setRenderTarget(renderer.createSurface((10, 10)))
    clicks = []
    renderer.drawButton(
        0, 0, 10, 10, (0, 0, 0), (0, 0, 0), 12, "", lambda: clicks.append(1)
    )
    assert clicks == []
    assert source.consumed == 0
