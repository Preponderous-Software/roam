import os
from unittest.mock import MagicMock

import pytest

from appContainer import container
from bootstrap import createContainer
from codex.codexJsonReaderWriter import CodexJsonReaderWriter
from config.config import Config
from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
from config.keyBindings import KeyBindings
from lib.graphik.src.graphik import Graphik
from rendering.renderer import Renderer
from rendering.pygameRenderer import PygameRenderer
from rendering.inputSource import InputSource
from rendering.pygameInputSource import PygameInputSource

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture
def test_config(tmp_path):
    config = MagicMock(spec=Config)
    config.pathToSaveDirectory = str(tmp_path)
    config.gridSize = 3
    config.worldBorder = 0
    config.debug = False
    config.dayNightCycleLengthTicks = 54000
    config.cropGrowthTicks = 1800
    config.ticksPerSecond = 30
    # Delegate to the real implementation so room-path construction reflects
    # the (possibly per-test overridden) pathToSaveDirectory.
    config.getRoomsDirectory = lambda: Config.getRoomsDirectory(config)
    config.getRoomFilePath = lambda x, y: Config.getRoomFilePath(config, x, y)
    return config


@pytest.fixture
def test_graphik():
    graphik = MagicMock(spec=Graphik)
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (1280, 720)
    graphik.getGameDisplay.return_value = gameDisplay
    return graphik


@pytest.fixture
def test_renderer():
    # PygameRenderer-spec mock for screens/HUD migrated to the Renderer
    # interface (epic #433). Defaults mirror the test_graphik display size so
    # layout math resolves; tests that need other dimensions override these.
    renderer = MagicMock(spec=PygameRenderer)
    renderer.getDisplaySize.return_value = (1280, 720)
    renderer.getDisplayWidth.return_value = 1280
    renderer.getDisplayHeight.return_value = 720
    renderer.getGameAreaRect.return_value = (280, 0, 720, 720)
    return renderer


@pytest.fixture
def test_input_source():
    # InputSource mock for screens migrated to the input seam (epic #433,
    # Phase 4). Defaults to no queued events and a quiescent mouse so a screen's
    # draw()/run() can be exercised headless; tests that drive specific input
    # override pollEvents / getMousePosition / getMouseButtons / isPressed.
    inputSource = MagicMock(spec=PygameInputSource)
    inputSource.pollEvents.return_value = []
    inputSource.getMousePosition.return_value = (0, 0)
    inputSource.getMouseButtons.return_value = (False, False, False)
    inputSource.isPressed.return_value = False
    return inputSource


@pytest.fixture
def test_di_container(test_config, test_graphik, test_renderer, test_input_source):
    createContainer(test_config)
    container.registerInstance(Graphik, test_graphik)
    container.registerInstance(Renderer, test_renderer)
    container.registerInstance(InputSource, test_input_source)
    container.register(
        InventoryJsonReaderWriter,
        lambda: InventoryJsonReaderWriter(container.resolve(Config)),
        lifetime="transient",
    )
    container.register(
        CodexJsonReaderWriter,
        lambda: CodexJsonReaderWriter(container.resolve(Config)),
        lifetime="transient",
    )
    container.register(KeyBindings, KeyBindings)

    previousRegistrations = {}

    def overrideDependency(dependencyType, instance):
        if dependencyType not in previousRegistrations:
            previousRegistrations[dependencyType] = container.getRegistration(
                dependencyType
            )
        container.registerInstance(dependencyType, instance)
        return instance

    yield container, overrideDependency

    for dependencyType, registration in previousRegistrations.items():
        container.restoreRegistration(dependencyType, registration)


@pytest.fixture(autouse=True)
def _initialize_test_di_container(test_di_container):
    return test_di_container


@pytest.fixture
def di_container(test_di_container):
    configuredContainer, _ = test_di_container
    return configuredContainer


@pytest.fixture
def resolve(di_container):
    return di_container.resolve


@pytest.fixture
def override_dependency(test_di_container):
    _, overrideDependency = test_di_container
    return overrideDependency
