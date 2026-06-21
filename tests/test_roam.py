import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
import pytest

from roam import _shouldUseTextMode


def test_text_flag_forces_text_mode():
    assert _shouldUseTextMode(["roam.py", "--text"]) is True


def test_no_flag_with_dummy_driver_selects_text_mode():
    # SDL_VIDEODRIVER=dummy is set at module level above; display.init()
    # will pick the dummy driver and _shouldUseTextMode must return True.
    assert _shouldUseTextMode(["roam.py"]) is True


def test_text_flag_takes_precedence_over_other_args():
    assert _shouldUseTextMode(["roam.py", "--selftest", "--text"]) is True


def test_display_init_failure_falls_back_to_text_mode(monkeypatch):
    import pygame as pg

    monkeypatch.setattr(
        pg.display, "init", lambda: (_ for _ in ()).throw(pg.error("no display"))
    )
    assert _shouldUseTextMode(["roam.py"]) is True
