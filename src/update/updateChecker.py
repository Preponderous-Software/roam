# @author Claude
# @since June 7th, 2026
import json
import threading
import urllib.request

from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger

_logger = getLogger(__name__)

# The releases list (newest first), not /releases/latest: every Roam release is
# published as a GitHub "pre-release", and /releases/latest excludes those (it
# returns 404 when there is no full release), so the list endpoint is the only
# reliable way to find the newest tag.
RELEASES_API_URL = "https://api.github.com/repos/Preponderous-Software/roam/releases"
RELEASES_PAGE_URL = "https://github.com/Preponderous-Software/roam/releases"


@component
class UpdateChecker:
    def __init__(self, config: Config):
        self.config = config
        self._latestVersion = None
        self._updateAvailable = False
        self._checkStarted = False

    def getReleasesUrl(self):
        return RELEASES_PAGE_URL

    def getLatestVersion(self):
        return self._latestVersion

    def isUpdateAvailable(self):
        return self._updateAvailable

    def checkForUpdatesAsync(self):
        # Kick off a single background check. No-op when disabled in config or
        # already started. The game is otherwise offline, so this must never
        # block the main thread — the fetch runs on a daemon thread and fails
        # silently if there is no network.
        if self._checkStarted or not self.config.checkForUpdates:
            return
        self._checkStarted = True
        thread = threading.Thread(target=self._checkForUpdates, daemon=True)
        thread.start()

    def _checkForUpdates(self):
        latest = self._fetchLatestVersion()
        if latest is None:
            return
        self._latestVersion = latest
        if self.isNewerVersion(latest, Config.getVersion()):
            self._updateAvailable = True
            _logger.info("update available", latestVersion=latest)

    def _fetchLatestVersion(self):
        # Return the latest release tag (without a leading "v"), or None on any
        # failure (offline, no releases yet, parse error). Never raises.
        try:
            request = urllib.request.Request(
                RELEASES_API_URL,
                headers={
                    "User-Agent": "Roam-UpdateChecker",
                    "Accept": "application/vnd.github+json",
                },
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                releases = json.load(response)
            # The list is newest-first; take the first non-draft release's tag.
            for release in releases:
                if release.get("draft"):
                    continue
                tag = release.get("tag_name")
                if tag:
                    return tag.lstrip("v")
            return None
        except Exception as e:
            _logger.debug("update check failed", error=str(e))
            return None

    @staticmethod
    def isNewerVersion(latest, current):
        # True if `latest` is a newer version than `current`. The numeric dotted
        # parts are compared; a clean release outranks a same-numbered
        # pre-release (e.g. "0.8.0" > "0.8.0-SNAPSHOT"). Returns False on any
        # parse failure so a malformed tag never shows a spurious update.
        latestParts, latestPre = UpdateChecker._parseVersion(latest)
        currentParts, currentPre = UpdateChecker._parseVersion(current)
        if latestParts is None or currentParts is None:
            return False
        length = max(len(latestParts), len(currentParts))
        latestParts = latestParts + [0] * (length - len(latestParts))
        currentParts = currentParts + [0] * (length - len(currentParts))
        if latestParts > currentParts:
            return True
        if latestParts == currentParts:
            return currentPre and not latestPre
        return False

    @staticmethod
    def _parseVersion(version):
        # "1.2.3-SNAPSHOT" -> ([1, 2, 3], True). Returns (None, False) if the
        # numeric portion cannot be parsed.
        if not version:
            return None, False
        numeric, separator, _suffix = version.strip().lstrip("v").partition("-")
        isPreRelease = separator == "-"
        try:
            parts = [int(part) for part in numeric.split(".")]
        except ValueError:
            return None, False
        return parts, isPreRelease
