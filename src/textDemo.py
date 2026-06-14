"""Runnable demonstration of Roam's text frontend.

Renders the real `MainMenuScreen` to the terminal through `TextRenderer` — with
no pygame and no window — showing that the same screen logic drives a second
frontend (frontend-abstraction epic #433, text-UI #239).

    python3 src/textDemo.py [screen]

`screen` may be `menu` (default). More screens become demoable as their data
dependencies are stubbed; the menu needs only a version string and an
update-checker, so it runs without a save file or network.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rendering.textInputSource import TextInputSource
from rendering.textRenderer import TextRenderer
from screen.mainMenuScreen import MainMenuScreen


class _DemoConfig:
    def getVersion(self):
        return "text-demo"


class _DemoUpdateChecker:
    def isUpdateAvailable(self):
        return False

    def checkForUpdatesAsync(self):
        pass


def renderMainMenu():
    renderer = TextRenderer()
    screen = MainMenuScreen(
        renderer, TextInputSource(), _DemoConfig(), _DemoUpdateChecker()
    )
    screen.draw()
    return renderer.grid.toString()


def main(argv):
    which = argv[1] if len(argv) > 1 else "menu"
    if which != "menu":
        print("unknown screen %r; available: menu" % which)
        return 1
    print(renderMainMenu())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
