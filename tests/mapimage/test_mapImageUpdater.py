from unittest.mock import MagicMock

from mapimage.mapImageUpdater import MapImageUpdater
from world.tickCounter import TickCounter


def _createUpdater(resolve, override_dependency, test_config, tmp_path):
    tickCounter = MagicMock()
    tickCounter.getTick.return_value = 0
    test_config.pathToSaveDirectory = str(tmp_path)
    test_config.debug = False
    override_dependency(TickCounter, tickCounter)
    updater = resolve(MapImageUpdater)
    return updater, tickCounter


def test_initialization(resolve, override_dependency, test_config, tmp_path):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)

    assert updater.updateCooldownInTicks == 300
    assert updater._updateInProgress is False
    updater.shutdown(wait=True)


def test_update_map_image_async_runs_in_background(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    updater.mapImageGenerator = MagicMock()
    mockImage = MagicMock()
    updater.mapImageGenerator.generate.return_value = mockImage

    updater.updateMapImageAsync()
    updater.shutdown(wait=True)

    updater.mapImageGenerator.generate.assert_called_once()
    mockImage.save.assert_called_once()
    updater.mapImageGenerator.clearRoomImages.assert_called_once()


def test_update_map_image_delegates_to_async(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    updater.mapImageGenerator = MagicMock()
    mockImage = MagicMock()
    updater.mapImageGenerator.generate.return_value = mockImage

    updater.updateMapImage()
    updater.shutdown(wait=True)

    updater.mapImageGenerator.generate.assert_called_once()


def test_skips_if_update_already_in_progress(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    updater.mapImageGenerator = MagicMock()
    mockImage = MagicMock()
    updater.mapImageGenerator.generate.return_value = mockImage

    # Simulate in-progress state
    updater._updateInProgress = True

    updater.updateMapImageAsync()
    updater.shutdown(wait=True)

    # Should not have been called since already in progress
    updater.mapImageGenerator.generate.assert_not_called()


def test_update_in_progress_flag_resets_after_completion(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    updater.mapImageGenerator = MagicMock()
    mockImage = MagicMock()
    updater.mapImageGenerator.generate.return_value = mockImage

    updater.updateMapImageAsync()
    updater.shutdown(wait=True)

    assert updater._updateInProgress is False


def test_update_in_progress_flag_resets_on_error(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    updater.mapImageGenerator = MagicMock()
    updater.mapImageGenerator.generate.side_effect = RuntimeError("test error")

    updater.updateMapImageAsync()
    updater.shutdown(wait=True)

    # Flag should reset even after an error
    assert updater._updateInProgress is False


def test_update_if_cooldown_over_triggers_when_past_cooldown(
    resolve, override_dependency, test_config, tmp_path
):
    updater, tickCounter = _createUpdater(
        resolve, override_dependency, test_config, tmp_path
    )
    updater.mapImageGenerator = MagicMock()
    mockImage = MagicMock()
    updater.mapImageGenerator.generate.return_value = mockImage
    updater.tickLastUpdated = 0

    # Simulate enough ticks passing
    tickCounter.getTick.return_value = 301

    updater.updateIfCooldownOver()
    updater.shutdown(wait=True)

    updater.mapImageGenerator.generate.assert_called_once()


def test_update_if_cooldown_over_skips_when_within_cooldown(
    resolve, override_dependency, test_config, tmp_path
):
    updater, tickCounter = _createUpdater(
        resolve, override_dependency, test_config, tmp_path
    )
    updater.mapImageGenerator = MagicMock()
    updater.tickLastUpdated = 0

    # Only 100 ticks, cooldown is 300
    tickCounter.getTick.return_value = 100

    updater.updateIfCooldownOver()
    updater.shutdown(wait=True)

    updater.mapImageGenerator.generate.assert_not_called()


def test_shutdown(resolve, override_dependency, test_config, tmp_path):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)

    updater.shutdown(wait=True)
    # Should not raise
