import os
import runpy
from unittest.mock import MagicMock

import pytest

from src.config.config import Config

SPEC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "roam.spec")
DISTRIBUTION_ENTRY = (os.path.join("build", "distribution.txt"), ".")

# roam.spec runs inside PyInstaller, which supplies these names. PyInstaller is
# not a test dependency, so they are stubbed and the spec is run in a temporary
# directory, which leaves any real build/ folder alone. The build itself is
# exercised by the packaging workflows, for the default distribution only.
PYINSTALLER_NAMES = ("Analysis", "PYZ", "EXE", "COLLECT", "BUNDLE")


def _runSpec(monkeypatch, tmp_path, distribution):
    monkeypatch.chdir(tmp_path)
    if distribution is None:
        monkeypatch.delenv("ROAM_DISTRIBUTION", raising=False)
    else:
        monkeypatch.setenv("ROAM_DISTRIBUTION", distribution)
    stubs = {name: MagicMock() for name in PYINSTALLER_NAMES}
    runpy.run_path(SPEC_PATH, init_globals=stubs)
    return stubs["Analysis"].call_args.kwargs["datas"]


def test_default_build_bundles_no_distribution_file(monkeypatch, tmp_path):
    datas = _runSpec(monkeypatch, tmp_path, None)

    assert DISTRIBUTION_ENTRY not in datas
    assert not (tmp_path / "build").exists()
    assert ("version.txt", ".") in datas


def test_empty_distribution_is_the_default_build(monkeypatch, tmp_path):
    datas = _runSpec(monkeypatch, tmp_path, "")

    assert DISTRIBUTION_ENTRY not in datas


def test_stale_distribution_file_is_not_bundled_by_a_default_build(
    monkeypatch, tmp_path
):
    # A Steam build leaves build/distribution.txt behind; the GitHub build made
    # next in the same checkout must not pick it up.
    _runSpec(monkeypatch, tmp_path, "steam")

    datas = _runSpec(monkeypatch, tmp_path, None)

    assert DISTRIBUTION_ENTRY not in datas


@pytest.mark.parametrize("distribution", ["steam", " Steam "])
def test_steam_build_bundles_a_file_config_reads_as_steam(
    monkeypatch, tmp_path, distribution
):
    datas = _runSpec(monkeypatch, tmp_path, distribution)

    assert DISTRIBUTION_ENTRY in datas
    monkeypatch.setattr(
        "src.config.config.getBundleDirectory", lambda: str(tmp_path / "build")
    )
    assert Config.isSteamBuild() is True


def test_unknown_distribution_stops_the_build(monkeypatch, tmp_path):
    with pytest.raises(SystemExit, match="stem"):
        _runSpec(monkeypatch, tmp_path, "stem")
