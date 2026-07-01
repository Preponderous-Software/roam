from unittest.mock import MagicMock, patch

from update.updateChecker import UpdateChecker


def _checker(checkForUpdates=True):
    config = MagicMock()
    config.checkForUpdates = checkForUpdates
    return UpdateChecker(config)


# --- isNewerVersion ---------------------------------------------------------


def test_is_newer_version_higher_patch():
    assert UpdateChecker.isNewerVersion("0.8.1", "0.8.0") is True


def test_is_newer_version_higher_minor():
    assert UpdateChecker.isNewerVersion("0.9.0", "0.8.0") is True


def test_is_newer_version_lower():
    assert UpdateChecker.isNewerVersion("0.7.0", "0.8.0") is False


def test_is_newer_version_equal():
    assert UpdateChecker.isNewerVersion("0.8.0", "0.8.0") is False


def test_is_newer_version_strips_v_prefix():
    assert UpdateChecker.isNewerVersion("v0.9.0", "0.8.0") is True


def test_release_outranks_same_numbered_snapshot():
    assert UpdateChecker.isNewerVersion("0.8.0", "0.8.0-SNAPSHOT") is True


def test_snapshot_does_not_outrank_release():
    assert UpdateChecker.isNewerVersion("0.8.0-SNAPSHOT", "0.8.0") is False


def test_shorter_version_is_padded():
    assert UpdateChecker.isNewerVersion("1.0", "0.8.0") is True


def test_unparseable_version_is_not_newer():
    assert UpdateChecker.isNewerVersion("garbage", "0.8.0") is False
    assert UpdateChecker.isNewerVersion("0.9.0", "also-bad") is False


# --- _fetchLatestVersion (network mocked) -----------------------------------


def test_fetch_latest_version_parses_newest_tag_from_list():
    checker = _checker()
    # /releases returns a list, newest first; the first non-draft tag is taken.
    releases = [{"tag_name": "0.10.0", "draft": False}, {"tag_name": "0.9.0"}]
    with patch("update.updateChecker.urllib.request.urlopen") as mockUrlopen, patch(
        "update.updateChecker.json.load", return_value=releases
    ):
        mockUrlopen.return_value.__enter__.return_value = MagicMock()
        assert checker._fetchLatestVersion() == "0.10.0"


def test_fetch_latest_version_skips_drafts():
    checker = _checker()
    releases = [{"tag_name": "0.11.0", "draft": True}, {"tag_name": "0.10.0"}]
    with patch("update.updateChecker.urllib.request.urlopen") as mockUrlopen, patch(
        "update.updateChecker.json.load", return_value=releases
    ):
        mockUrlopen.return_value.__enter__.return_value = MagicMock()
        assert checker._fetchLatestVersion() == "0.10.0"


def test_fetch_latest_version_returns_none_on_network_error():
    checker = _checker()
    with patch(
        "update.updateChecker.urllib.request.urlopen", side_effect=OSError("offline")
    ):
        assert checker._fetchLatestVersion() is None


def test_fetch_latest_version_none_when_no_releases():
    checker = _checker()
    with patch("update.updateChecker.urllib.request.urlopen") as mockUrlopen, patch(
        "update.updateChecker.json.load", return_value=[]
    ):
        mockUrlopen.return_value.__enter__.return_value = MagicMock()
        assert checker._fetchLatestVersion() is None


# --- _checkForUpdates orchestration -----------------------------------------


def test_check_sets_update_available_when_newer():
    checker = _checker()
    with patch.object(checker, "_fetchLatestVersion", return_value="9.9.9"), patch(
        "update.updateChecker.Config.getVersion", return_value="0.8.0"
    ):
        checker._checkForUpdates()
    assert checker.isUpdateAvailable() is True
    assert checker.getLatestVersion() == "9.9.9"


def test_check_no_update_when_current_is_latest():
    checker = _checker()
    with patch.object(checker, "_fetchLatestVersion", return_value="0.8.0"), patch(
        "update.updateChecker.Config.getVersion", return_value="0.8.0"
    ):
        checker._checkForUpdates()
    assert checker.isUpdateAvailable() is False


def test_check_no_update_when_fetch_fails():
    checker = _checker()
    with patch.object(checker, "_fetchLatestVersion", return_value=None):
        checker._checkForUpdates()
    assert checker.isUpdateAvailable() is False


def test_async_check_is_noop_when_disabled():
    checker = _checker(checkForUpdates=False)
    checker.checkForUpdatesAsync()
    assert checker._checkStarted is False
    assert checker.isUpdateAvailable() is False


def test_async_check_survives_runtime_error_on_thread_start():
    # Pyodide/WASM can't spawn threads; thread.start() raises RuntimeError.
    # checkForUpdatesAsync must not propagate the error so the main menu loads.
    checker = _checker()
    with patch(
        "threading.Thread.start", side_effect=RuntimeError("can't start new thread")
    ):
        checker.checkForUpdatesAsync()
    assert checker.isUpdateAvailable() is False
