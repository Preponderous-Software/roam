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


def _mockGenerator(updater, levels=(0,)):
    """Swap in a mock generator reporting `levels` as having captures waiting,
    and return the image its generate() hands back."""
    updater.mapImageGenerator = MagicMock()
    updater.mapImageGenerator.getLevelsWithRoomImages.return_value = list(levels)
    mockImage = MagicMock()
    updater.mapImageGenerator.generate.return_value = mockImage
    return mockImage


def test_initialization(resolve, override_dependency, test_config, tmp_path):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)

    assert updater.updateCooldownInTicks == 300
    assert updater._updateInProgress is False
    updater.shutdown(wait=True)


def test_update_map_image_async_runs_in_background(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    mockImage = _mockGenerator(updater)

    updater.updateMapImageAsync()
    updater.shutdown(wait=True)

    updater.mapImageGenerator.generate.assert_called_once()
    mockImage.save.assert_called_once()
    updater.mapImageGenerator.clearRoomImages.assert_called_once()


def test_update_map_image_delegates_to_async(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    _mockGenerator(updater)

    updater.updateMapImage()
    updater.shutdown(wait=True)

    updater.mapImageGenerator.generate.assert_called_once()


def test_skips_if_update_already_in_progress(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    _mockGenerator(updater)

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
    _mockGenerator(updater)

    updater.updateMapImageAsync()
    updater.shutdown(wait=True)

    assert updater._updateInProgress is False


def test_update_in_progress_flag_resets_on_error(
    resolve, override_dependency, test_config, tmp_path
):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    _mockGenerator(updater)
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
    _mockGenerator(updater)
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
    _mockGenerator(updater)
    updater.tickLastUpdated = 0

    # Only 100 ticks, cooldown is 300
    tickCounter.getTick.return_value = 100

    updater.updateIfCooldownOver()
    updater.shutdown(wait=True)

    updater.mapImageGenerator.generate.assert_not_called()


def test_map_image_written_to_active_save_directory_after_change(
    resolve, override_dependency, test_config, tmp_path
):
    # Regression (#495): the updater/generator is constructed at startup with the
    # default save dir, then saveSelectionScreen.selectSave() reassigns
    # config.pathToSaveDirectory. The map image must be written to the active
    # save dir (read by drawMiniMap), not the one captured at construction. The
    # bug was that the pygame minimap never appeared because the file landed in
    # the stale directory.
    from PIL import Image

    # generator captured tmp_path (the "startup default") at construction
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    startupDir = tmp_path

    saveDir = tmp_path / "save1"
    (saveDir / "roompngs").mkdir(parents=True)
    Image.new("RGB", (10, 10), "red").save(str(saveDir / "roompngs" / "0_0.png"))
    test_config.pathToSaveDirectory = str(saveDir)  # selectSave()

    updater._doUpdateMapImage()  # run synchronously
    updater.shutdown(wait=True)

    assert (saveDir / "mapImage.png").is_file()
    assert not (startupDir / "mapImage.png").is_file()


def test_every_level_with_captures_is_stitched_into_its_own_map_image(
    resolve, override_dependency, test_config, tmp_path
):
    # #557: surface and cave captures at the same (x, y) used to land in one
    # flat mapImage.png and overwrite each other. Each level now gets its own.
    from PIL import Image

    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    roompngs = tmp_path / "roompngs"
    roompngs.mkdir()
    Image.new("RGB", (10, 10), "green").save(str(roompngs / "0_0.png"))
    Image.new("RGB", (10, 10), "gray").save(str(roompngs / "0_0_-1.png"))

    updater._doUpdateMapImage()
    updater.shutdown(wait=True)

    assert (tmp_path / "mapImage.png").is_file()
    assert (tmp_path / "mapImage_z-1.png").is_file()
    # Every level's captures are consumed once stitched.
    assert list(roompngs.iterdir()) == []


def test_captures_are_not_stitched_into_another_levels_map(
    resolve, override_dependency, test_config, tmp_path
):
    # A cave capture must leave the surface map untouched, and vice versa.
    from PIL import Image

    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)
    roompngs = tmp_path / "roompngs"
    roompngs.mkdir()
    Image.new("RGB", (10, 10), "gray").save(str(roompngs / "0_0_-1.png"))

    updater._doUpdateMapImage()
    updater.shutdown(wait=True)

    assert (tmp_path / "mapImage_z-1.png").is_file()
    assert not (tmp_path / "mapImage.png").exists()


def test_shutdown(resolve, override_dependency, test_config, tmp_path):
    updater, _ = _createUpdater(resolve, override_dependency, test_config, tmp_path)

    updater.shutdown(wait=True)
    # Should not raise
