import os
from unittest.mock import MagicMock

import pytest

from appContainer import container
from bootstrap import createContainer
from codex.codexJsonReaderWriter import CodexJsonReaderWriter
from config.config import Config
from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
from lib.graphik.src.graphik import Graphik

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
    return config


@pytest.fixture
def test_graphik():
    graphik = MagicMock(spec=Graphik)
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (1280, 720)
    graphik.getGameDisplay.return_value = gameDisplay
    return graphik


@pytest.fixture
def test_di_container(test_config, test_graphik):
    createContainer(test_config)
    container.registerInstance(Graphik, test_graphik)
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
