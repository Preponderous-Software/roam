import os
import sys

# Ensure src directory is in the Python path so repository/service/controller packages
# are importable. This needs to happen before any other imports.
_srcDir = os.path.join(os.path.dirname(__file__), "..", "src")
if _srcDir not in sys.path:
    sys.path.insert(0, _srcDir)

from unittest.mock import MagicMock

import pytest

from appContainer import container
from bootstrap import createContainer
from codex.codexJsonReaderWriter import CodexJsonReaderWriter
from config.config import Config
from inventory.inventoryJsonReaderWriter import InventoryJsonReaderWriter
from lib.graphik.src.graphik import Graphik

# Import repository/service/controller modules so @component decorators register them
import repositories.statsRepository  # noqa: F401
import repositories.codexRepository  # noqa: F401
import repositories.playerRepository  # noqa: F401
import repositories.worldRepository  # noqa: F401
import repositories.configRepository  # noqa: F401
import services.movementService  # noqa: F401
import services.inventoryService  # noqa: F401
import services.craftingService  # noqa: F401
import services.worldService  # noqa: F401
import services.entityService  # noqa: F401
import services.saveService  # noqa: F401
import controllers.playerController  # noqa: F401
import controllers.inventoryController  # noqa: F401
import controllers.worldController  # noqa: F401
import controllers.menuController  # noqa: F401

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
