import os
import shutil
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import pytest

from src.config.config import Config
from src.screen.saveSelectionScreen import SaveSelectionScreen
from src.screen.screenType import ScreenType
from src.lib.graphik.src.graphik import Graphik


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def temp_saves_dir():
    dirPath = tempfile.mkdtemp()
    yield dirPath
    shutil.rmtree(dirPath)


def createSaveSelectionScreen(savesDir):
    config = Config()
    gameDisplay = pygame.display.set_mode((800, 600))
    graphik = Graphik(gameDisplay)
    initializeWorldScreen = lambda: None
    screen = SaveSelectionScreen(graphik, config, initializeWorldScreen)
    screen.savesBaseDirectory = savesDir
    return screen


def test_initialization(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    assert screen.nextScreen == ScreenType.MAIN_MENU_SCREEN
    assert screen.changeScreen == False
    assert screen.scrollOffset == 0


def test_getSaveDirectories_empty(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    saves = screen.getSaveDirectories()
    assert saves == []


def test_getSaveDirectories_nonexistent():
    screen = createSaveSelectionScreen("/tmp/nonexistent_saves_dir_xyz")

    saves = screen.getSaveDirectories()
    assert saves == []


def test_getSaveDirectories_with_saves(temp_saves_dir):
    os.makedirs(os.path.join(temp_saves_dir, "save_1"))
    os.makedirs(os.path.join(temp_saves_dir, "save_2"))

    screen = createSaveSelectionScreen(temp_saves_dir)
    saves = screen.getSaveDirectories()

    assert len(saves) == 2
    names = [s["name"] for s in saves]
    assert "save_1" in names
    assert "save_2" in names


def test_getSaveDirectories_includes_lastPlayed(temp_saves_dir):
    os.makedirs(os.path.join(temp_saves_dir, "my_save"))

    screen = createSaveSelectionScreen(temp_saves_dir)
    saves = screen.getSaveDirectories()

    assert len(saves) == 1
    assert "lastPlayed" in saves[0]
    assert len(saves[0]["lastPlayed"]) > 0


def test_selectSave(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    screen.selectSave("saves/test_save")
    assert screen.config.pathToSaveDirectory == "saves/test_save"
    assert screen.nextScreen == ScreenType.WORLD_SCREEN
    assert screen.changeScreen == True


def test_createNewGame(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    screen.createNewGame()
    assert screen.changeScreen == True
    assert screen.nextScreen == ScreenType.WORLD_SCREEN
    assert os.path.isdir(os.path.join(temp_saves_dir, "save_1"))
    assert screen.config.pathToSaveDirectory == os.path.join(temp_saves_dir, "save_1")


def test_createNewGame_increments_number(temp_saves_dir):
    os.makedirs(os.path.join(temp_saves_dir, "save_1"))

    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.createNewGame()

    assert os.path.isdir(os.path.join(temp_saves_dir, "save_2"))
    assert screen.config.pathToSaveDirectory == os.path.join(temp_saves_dir, "save_2")


def test_switchToMainMenuScreen(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    screen.switchToMainMenuScreen()
    assert screen.nextScreen == ScreenType.MAIN_MENU_SCREEN
    assert screen.changeScreen == True


def test_handleKeyDownEvent_escape(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    screen.handleKeyDownEvent(pygame.K_ESCAPE)
    assert screen.nextScreen == ScreenType.MAIN_MENU_SCREEN
    assert screen.changeScreen == True


def test_handleKeyDownEvent_scroll(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    assert screen.scrollOffset == 0
    screen.handleKeyDownEvent(pygame.K_DOWN)
    assert screen.scrollOffset == 1
    screen.handleKeyDownEvent(pygame.K_DOWN)
    assert screen.scrollOffset == 2
    screen.handleKeyDownEvent(pygame.K_UP)
    assert screen.scrollOffset == 1
    screen.handleKeyDownEvent(pygame.K_UP)
    assert screen.scrollOffset == 0
    screen.handleKeyDownEvent(pygame.K_UP)
    assert screen.scrollOffset == 0


def test_screenType_has_save_selection():
    assert hasattr(ScreenType, "SAVE_SELECTION_SCREEN")
    assert ScreenType.SAVE_SELECTION_SCREEN == "save_selection_screen"
