import os
import re


from rendering.renderer import Renderer
from rendering.pygameRenderer import PygameRenderer

# Directories whose modules draw through the Renderer interface.
SOURCE_DIRS = ["src/screen", "src/ui"]
RENDERER_CALL = re.compile(r"self\.renderer\.([a-zA-Z_]+)\(")


def _iter_source_files():
    for directory in SOURCE_DIRS:
        for name in sorted(os.listdir(directory)):
            if name.endswith(".py"):
                yield os.path.join(directory, name)


def _called_renderer_methods():
    calls = {}
    for path in _iter_source_files():
        with open(path) as fh:
            for method in RENDERER_CALL.findall(fh.read()):
                calls.setdefault(method, set()).add(path)
    return calls


def test_pygame_renderer_is_concrete():
    # Fails if PygameRenderer leaves any abstract Renderer method unimplemented.
    PygameRenderer(graphik=_StubGraphik())


def test_every_called_method_exists_on_the_interface():
    missing = {
        method: sorted(paths)
        for method, paths in _called_renderer_methods().items()
        if not hasattr(Renderer, method)
    }
    assert not missing, "renderer methods called but not on the interface: " + repr(
        missing
    )


def test_interface_has_no_unused_dead_methods():
    # Every abstract method should be exercised somewhere in the codebase, so a
    # method is not added to the interface and then left orphaned. getGameAreaRect
    # and setClipRegion are used by worldScreen (migrated separately); allow them.
    called = set(_called_renderer_methods())
    declared = {
        name
        for name in vars(Renderer)
        if not name.startswith("_") and callable(getattr(Renderer, name))
    }
    allowed_pending = {"getGameAreaRect", "setClipRegion"}
    orphaned = declared - called - allowed_pending
    assert not orphaned, "declared but never called: " + repr(sorted(orphaned))


class _StubGraphik:
    """Minimal stand-in so PygameRenderer can be constructed without pygame."""

    def getGameDisplay(self):
        return None
