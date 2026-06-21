import os
import subprocess
import sys
import textwrap

from rendering.inputEvent import EventType, InputEvent
from rendering.inputSource import InputSource
from rendering.keyCode import KeyCode
from rendering.nullInputSource import NullInputSource
from rendering.nullRenderer import NullRenderer
from rendering.renderer import Renderer
from screen.screen import Screen
from screen.screenType import ScreenType

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _OneFrameScreen(Screen):
    """Minimal Screen that draws a single frame and then exits, so the base
    run loop can be exercised end-to-end against any frontend."""

    def __init__(self, renderer, inputSource):
        self.renderer = renderer
        self.inputSource = inputSource
        self.nextScreen = ScreenType.NONE
        self.changeScreen = False
        self.framesDrawn = 0

    def draw(self):
        self.renderer.clearScreen((0, 0, 0))
        self.renderer.drawText("hello", 10, 10, 12, (255, 255, 255))
        self.framesDrawn += 1
        self.changeScreen = True


def test_null_renderer_implements_the_renderer_interface():
    renderer = NullRenderer(640, 480)
    assert isinstance(renderer, Renderer)

    assert renderer.getDisplaySize() == (640, 480)
    assert renderer.getDisplayWidth() == 640
    assert renderer.getDisplayHeight() == 480
    # getGameAreaRect is the centered square play area.
    r = renderer.getGameAreaRect()
    assert (r.x, r.y, r.width, r.height) == (80, 0, 480, 480)
    # Drawing calls are no-ops that must not raise.
    renderer.clearScreen((0, 0, 0))
    renderer.drawRectangle(0, 0, 10, 10, (1, 2, 3))
    renderer.drawText("x", 1, 1, 8, (1, 2, 3))
    renderer.drawTextLeftAligned("x", 1, 1, 8, (1, 2, 3))
    renderer.drawTranslucentOverlay((0, 0, 0, 100))
    renderer.drawButton(0, 0, 1, 1, (0, 0, 0), (0, 0, 0), 8, "ok", lambda: None)
    renderer.setClipRegion(None)
    renderer.captureScreenshot()
    renderer.present()
    # loadImage/scaleImage return opaque non-None handles.
    image = renderer.loadImage("assets/images/player_down.png")
    assert image is not None
    assert renderer.scaleImage(image, (24, 24)) is not None
    # createSurface yields a headless surface; saveImage is a no-op; tryLoadImage
    # never finds anything.
    assert renderer.createSurface((4, 4)) is not None
    renderer.saveImage(renderer.createSurface((2, 2)), "ignored.png")
    assert renderer.tryLoadImage("anything.png") is None


def test_null_renderer_render_target_round_trips():
    renderer = NullRenderer()
    original = renderer.getRenderTarget()
    sentinel = object()
    renderer.setRenderTarget(sentinel)
    assert renderer.getRenderTarget() is sentinel
    renderer.setRenderTarget(original)
    assert renderer.getRenderTarget() is original


def test_null_input_source_implements_the_interface():
    source = NullInputSource()
    assert isinstance(source, InputSource)
    assert source.pollEvents() == []
    assert source.getMousePosition() == (0, 0)
    assert source.getMouseButtons() == (False, False, False)
    assert source.isPressed(KeyCode.W) is False


def test_null_input_source_replays_scripted_event_frames():
    source = NullInputSource([[InputEvent(EventType.KEY_DOWN, key=KeyCode.ESCAPE)], []])
    first = source.pollEvents()
    assert len(first) == 1 and first[0].key is KeyCode.ESCAPE
    assert source.pollEvents() == []
    # Exhausted -> empty forever.
    assert source.pollEvents() == []


def test_a_screen_renders_one_frame_through_the_null_frontend():
    screen = _OneFrameScreen(NullRenderer(), NullInputSource())

    result = screen.run()

    assert screen.framesDrawn == 1
    assert result == ScreenType.NONE


def test_the_seam_drives_a_screen_with_pygame_imports_blocked():
    # The executable proof of the abstraction (epic #433, Phase 5): block any
    # `import pygame`, then drive the Screen base loop one frame through the Null
    # frontend. If any module on that path imported pygame, this subprocess would
    # die with ImportError instead of printing the sentinel.
    script = textwrap.dedent("""
        import sys
        # Poison pygame: any `import pygame` now raises ImportError.
        sys.modules["pygame"] = None
        sys.path.insert(0, "src")
        sys.path.insert(0, ".")

        from rendering.nullRenderer import NullRenderer
        from rendering.nullInputSource import NullInputSource
        from screen.screen import Screen
        from screen.screenType import ScreenType

        class OneFrame(Screen):
            def __init__(self):
                self.renderer = NullRenderer()
                self.inputSource = NullInputSource()
                self.nextScreen = ScreenType.NONE
                self.changeScreen = False
                self.frames = 0
            def draw(self):
                self.renderer.clearScreen((0, 0, 0))
                self.renderer.drawText("hi", 10, 10, 12, (255, 255, 255))
                self.frames += 1
                self.changeScreen = True

        screen = OneFrame()
        screen.run()
        assert screen.frames == 1
        assert "pygame" not in sys.modules or sys.modules["pygame"] is None
        print("NULL_FRONTEND_OK")
        """)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        "seam pulled in pygame or failed:\n"
        + completed.stdout
        + "\n"
        + completed.stderr
    )
    assert "NULL_FRONTEND_OK" in completed.stdout
