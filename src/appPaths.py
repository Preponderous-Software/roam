# @author Claude
# @since June 7th, 2026
import os
import sys
from pathlib import Path


def isFrozen():
    # True when running from a PyInstaller-built executable.
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def getBundleDirectory():
    # The directory that holds the bundled data files (assets, schemas,
    # config.yml). When frozen this is PyInstaller's extraction/install
    # directory; otherwise it is the repository root (one level up from src/).
    if isFrozen():
        return sys._MEIPASS
    return str(Path(__file__).resolve().parents[1])


def prepareWorkingDirectory():
    # A frozen executable starts with an arbitrary working directory, but the
    # game loads assets and schemas through paths relative to the repository
    # root (e.g. "assets/images/stone.png", "schemas/tick.json"). Change into
    # the bundle directory so those relative paths resolve. No-op when running
    # from source, where the working directory is already the repository root.
    if isFrozen():
        os.chdir(getBundleDirectory())
