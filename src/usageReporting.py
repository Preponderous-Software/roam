# @author Claude
# @since September 11th, 2026
"""Anonymous usage reporting to the trace service.

Roam reports two events to https://trace.danielstephenson.dev so the number
of installations actually being played can be seen: ``startup`` once per
launch and ``world-loaded`` each time a save is opened. Each carries the
program name ("roam"), the game version (the tag ``version``) and a random
installation ID (the tag ``install``, see ``installIdFile``), both added to
every event by the client — nothing else. No usernames, hostnames, IPs, paths
or save names are ever sent.

The transport is the vendored ``lib.trace_client`` (standard library only),
which posts from a single daemon thread, never raises into the game, and
drops reports rather than queueing more than a few hundred. Reporting is on
by default and turned off with ``usageReportingEnabled: false`` in
config.yml. It is never on in the browser (Pyodide) build, which has no real
threads or sockets, and it can be forced off for a process with the
``ROAM_USAGE_REPORTING=0`` environment variable — the test harness does that
so a test run is never counted as a player — or, for every program that
reports to trace, with ``TRACE_USAGE_REPORTING=off`` or ``DO_NOT_TRACK=1``.
Details: https://danielstephenson.dev/usage-reporting
"""
import os
import sys

from appPaths import getBundleDirectory
from config.config import Config
from gameLogging.logger import getLogger
from lib.trace_client import TraceClient, environment_opts_out

_logger = getLogger(__name__)

# The program name the trace key was issued for. Not the display name.
APPLICATION = "roam"

# Environment override, for test harnesses and containers: any of these values
# (case-insensitive) forces reporting off regardless of config.yml.
ENVIRONMENT_VARIABLE = "ROAM_USAGE_REPORTING"
_OFF_VALUES = frozenset({"0", "false", "off", "no"})

# Sent as the version when version.txt is missing or empty: the client requires
# a non-blank version, and a missing one must never stop the game starting.
UNKNOWN_VERSION = "unknown"

# The file the client keeps this installation's random ID in (see installIdFile).
INSTALL_ID_FILE_NAME = "trace-install-id"

# Pins the installation ID for a process (a container, say) instead of the file.
INSTALL_ID_ENVIRONMENT_VARIABLE = "TRACE_INSTALL_ID"

OPT_OUT_INSTRUCTION = "usageReportingEnabled: false in config.yml"

# Where what is sent, what is not, and every opt-out are written up.
DETAILS_URL = "https://danielstephenson.dev/usage-reporting"

FIRST_RUN_NOTICE = (
    "Usage reporting is on: roam sends a startup event and a world-loaded "
    "event (program name, version and a random installation ID only) to "
    "https://trace.danielstephenson.dev - nothing about you or your saves. "
    "Turn it off with "
    + OPT_OUT_INSTRUCTION
    + ", or for every trace-reporting program with the environment variable "
    "TRACE_USAGE_REPORTING=off. Details: " + DETAILS_URL
)


def isBrowserBuild():
    # The Pyodide build runs the same sources under Emscripten, where there
    # are no OS threads and no sockets; the client must not even be started.
    return sys.platform == "emscripten"


def isDisabledByEnvironment():
    """Roam's own ROAM_USAGE_REPORTING override, or the TRACE_USAGE_REPORTING
    / DO_NOT_TRACK variables every trace client honours. Checked before the
    config so the notice is never shown for a run that will not report."""
    if environment_opts_out():
        return True
    value = os.environ.get(ENVIRONMENT_VARIABLE)
    if value is None:
        return False
    return value.strip().lower() in _OFF_VALUES


def isReportingActive(config):
    """Whether this process reports at all: on in config, not the browser
    build, and not switched off through the environment."""
    return (
        bool(config.usageReportingEnabled)
        and not isBrowserBuild()
        and not isDisabledByEnvironment()
    )


def installIdFile():
    """Where the client keeps this installation's random ID: Roam's own
    per-user data directory where it has one (%APPDATA%\\Roam on Windows,
    ~/Library/Application Support/Roam on macOS, next to the user config.yml),
    otherwise $XDG_DATA_HOME/roam (or ~/.local/share/roam) — on Linux the
    user data directory is the repository/bundle root, which is neither
    per-user nor, for a frozen build, kept between runs. The client only
    reads or creates the file when reporting is on; deleting it resets the
    ID."""
    userDataDirectory = Config.getUserDataDirectory()
    if os.path.normpath(userDataDirectory) != os.path.normpath(getBundleDirectory()):
        return os.path.join(userDataDirectory, INSTALL_ID_FILE_NAME)
    base = os.environ.get("XDG_DATA_HOME", "").strip() or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return os.path.join(base, APPLICATION, INSTALL_ID_FILE_NAME)


def createTraceClient(config):
    """Build the client for this run. Returns a disabled client (which does
    nothing and starts no thread) whenever reporting is not active, and never
    raises: a bad endpoint or key in config.yml costs the report, not the
    game."""
    if not isReportingActive(config):
        return TraceClient.disabled()
    try:
        return TraceClient(
            config.usageReportingEndpoint,
            APPLICATION,
            programVersion(),
            key=config.usageReportingKey,
            enabled=True,
            # Resolved by the client after its own opt-out checks; a disabled
            # client never reads or creates the file.
            install_id=os.environ.get(INSTALL_ID_ENVIRONMENT_VARIABLE),
            install_id_file=installIdFile(),
        )
    except Exception as failure:  # noqa: BLE001 - reporting must never stop the game
        _logger.warning("usage reporting could not be started", error=str(failure))
        return TraceClient.disabled()


def showFirstRunNotice(config):
    """Log the one-line notice the first time the game starts with reporting
    active and no usageReporting* setting in the config file yet, then write
    the setting so the notice is not shown again. Returns True when shown."""
    if not isReportingActive(config) or config.usageReportingAcknowledged:
        return False
    _logger.info(FIRST_RUN_NOTICE)
    config.acknowledgeUsageReporting()
    return True


def programVersion():
    """The game version every event carries: version.txt, or UNKNOWN_VERSION
    when it is missing or blank."""
    version = Config.getVersion()
    if not isinstance(version, str) or not version.strip():
        return UNKNOWN_VERSION
    return version
