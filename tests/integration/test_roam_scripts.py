import glob
import os

import pytest

from roamScript import RoamScriptError, runScript

# Same constraint as test_text_playthrough.py: TextPlaythrough needs a POSIX
# pty, so this only runs on the ubuntu CI job (and skips on a Windows dev
# machine).
pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="roamscript playthroughs need a POSIX pty"
)

_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")
_SCRIPT_PATHS = sorted(glob.glob(os.path.join(_SCRIPTS_DIR, "*.roamscript")))


@pytest.mark.parametrize(
    "scriptPath",
    _SCRIPT_PATHS,
    ids=[os.path.basename(path) for path in _SCRIPT_PATHS],
)
def test_roam_script(scriptPath):
    try:
        runScript(scriptPath)
    except RoamScriptError as e:
        pytest.fail(str(e))
