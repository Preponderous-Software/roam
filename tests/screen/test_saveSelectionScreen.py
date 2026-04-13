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
    assert screen.sortMode == SaveSelectionScreen.SORT_BY_DATE
    assert screen.confirmingDelete is None


def test_getSaveDirectories_empty(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    saves = screen.getSaveDirectories()
    assert saves == []


def test_getSaveDirectories_nonexistent(tmp_path):
    nonexistentDir = tmp_path / "does_not_exist"
    assert not nonexistentDir.exists()

    screen = createSaveSelectionScreen(str(nonexistentDir))

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


def test_createNewGameWithName(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    screen.createNewGameWithName("save_1")
    assert screen.changeScreen == True
    assert screen.nextScreen == ScreenType.WORLD_SCREEN
    assert os.path.isdir(os.path.join(temp_saves_dir, "save_1"))
    assert screen.config.pathToSaveDirectory == os.path.join(temp_saves_dir, "save_1")


def test_createNewGameWithName_existing(temp_saves_dir):
    os.makedirs(os.path.join(temp_saves_dir, "save_1"))

    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.createNewGameWithName("save_1")

    assert screen.changeScreen == False


def test_generateSaveName_increments(temp_saves_dir):
    os.makedirs(os.path.join(temp_saves_dir, "save_1"))

    screen = createSaveSelectionScreen(temp_saves_dir)
    name = screen._generateSaveName()

    assert name == "save_2"


def test_generateSaveName_skips_non_directory(temp_saves_dir):
    with open(os.path.join(temp_saves_dir, "save_1"), "w") as f:
        f.write("not a directory")

    screen = createSaveSelectionScreen(temp_saves_dir)
    name = screen._generateSaveName()

    assert name == "save_2"


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


def test_handleKeyDownEvent_escape_cancels_delete(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.confirmingDelete = "some/path"

    screen.handleKeyDownEvent(pygame.K_ESCAPE)
    assert screen.confirmingDelete is None
    assert screen.changeScreen == False


def test_handleKeyDownEvent_scroll(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    assert screen.scrollOffset == 0
    screen.handleKeyDownEvent(pygame.K_DOWN)
    assert screen.scrollOffset == 0

    for i in range(5):
        os.makedirs(os.path.join(temp_saves_dir, "save_" + str(i + 1)))
    screen.refreshSaveCache()

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


def test_handleKeyDownEvent_scroll_clamped(temp_saves_dir):
    os.makedirs(os.path.join(temp_saves_dir, "save_1"))
    os.makedirs(os.path.join(temp_saves_dir, "save_2"))

    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.refreshSaveCache()

    for _ in range(10):
        screen.handleKeyDownEvent(pygame.K_DOWN)

    assert screen.scrollOffset == 1


def test_screenType_has_save_selection():
    assert hasattr(ScreenType, "SAVE_SELECTION_SCREEN")
    assert ScreenType.SAVE_SELECTION_SCREEN == "save_selection_screen"


def test_toggleSort(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    assert screen.sortMode == SaveSelectionScreen.SORT_BY_DATE
    screen.toggleSort()
    assert screen.sortMode == SaveSelectionScreen.SORT_BY_NAME
    screen.toggleSort()
    assert screen.sortMode == SaveSelectionScreen.SORT_BY_DATE


def test_sort_by_name(temp_saves_dir):
    os.makedirs(os.path.join(temp_saves_dir, "beta_save"))
    os.makedirs(os.path.join(temp_saves_dir, "alpha_save"))
    os.makedirs(os.path.join(temp_saves_dir, "gamma_save"))

    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.sortMode = SaveSelectionScreen.SORT_BY_NAME
    saves = screen.getSaveDirectories()

    names = [s["name"] for s in saves]
    assert names == ["alpha_save", "beta_save", "gamma_save"]


def test_deleteSave(temp_saves_dir):
    savePath = os.path.join(temp_saves_dir, "save_to_delete")
    os.makedirs(savePath)
    assert os.path.isdir(savePath)

    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.deleteSave(savePath)

    assert not os.path.exists(savePath)
    saves = screen.getSaveDirectories()
    assert len(saves) == 0


def test_deleteSave_adjusts_scroll(temp_saves_dir):
    for i in range(3):
        os.makedirs(os.path.join(temp_saves_dir, "save_" + str(i + 1)))

    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.scrollOffset = 2

    screen.deleteSave(os.path.join(temp_saves_dir, "save_3"))
    assert screen.scrollOffset <= 1


def test_requestDelete(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    assert screen.confirmingDelete is None
    screen._requestDelete("saves/my_save")
    assert screen.confirmingDelete == "saves/my_save"


def test_refreshSaveCache(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    saves = screen.getSaveDirectories()
    assert len(saves) == 0

    os.makedirs(os.path.join(temp_saves_dir, "new_save"))
    assert len(screen.getSaveDirectories()) == 0

    screen.refreshSaveCache()
    assert len(screen.getSaveDirectories()) == 1


def test_scrollUp_and_scrollDown(temp_saves_dir):
    for i in range(5):
        os.makedirs(os.path.join(temp_saves_dir, "save_" + str(i + 1)))

    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.refreshSaveCache()

    screen.scrollDown()
    assert screen.scrollOffset == 1
    screen.scrollDown()
    assert screen.scrollOffset == 2
    screen.scrollUp()
    assert screen.scrollOffset == 1
    screen.scrollUp()
    assert screen.scrollOffset == 0
    screen.scrollUp()
    assert screen.scrollOffset == 0


def test_startNamingNewSave(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    assert screen.namingNewSave == False
    screen.startNamingNewSave()
    assert screen.namingNewSave == True
    assert screen.newSaveNameInput == ""


def test_cancelNamingNewSave(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.namingNewSave = True
    screen.newSaveNameInput = "partial"

    screen.cancelNamingNewSave()
    assert screen.namingNewSave == False
    assert screen.newSaveNameInput == ""


def test_confirmNewSaveName_custom(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.namingNewSave = True
    screen.newSaveNameInput = "my_world"

    screen.confirmNewSaveName()
    assert screen.namingNewSave == False
    assert screen.changeScreen == True
    assert os.path.isdir(os.path.join(temp_saves_dir, "my_world"))
    assert screen.config.pathToSaveDirectory == os.path.join(temp_saves_dir, "my_world")


def test_confirmNewSaveName_empty_uses_generated(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.namingNewSave = True
    screen.newSaveNameInput = ""

    screen.confirmNewSaveName()
    assert screen.namingNewSave == False
    assert screen.changeScreen == True
    assert os.path.isdir(os.path.join(temp_saves_dir, "save_1"))


def test_handleKeyDownEvent_escape_cancels_naming(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.namingNewSave = True
    screen.newSaveNameInput = "test"

    screen.handleKeyDownEvent(pygame.K_ESCAPE)
    assert screen.namingNewSave == False
    assert screen.changeScreen == False


def test_handleKeyDownEvent_enter_confirms_naming(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.namingNewSave = True
    screen.newSaveNameInput = "named_save"

    screen.handleKeyDownEvent(pygame.K_RETURN)
    assert screen.namingNewSave == False
    assert screen.changeScreen == True
    assert os.path.isdir(os.path.join(temp_saves_dir, "named_save"))


def test_handleKeyDownEvent_backspace_in_naming(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.namingNewSave = True
    screen.newSaveNameInput = "abc"

    screen.handleKeyDownEvent(pygame.K_BACKSPACE)
    assert screen.newSaveNameInput == "ab"


def test_handleKeyDownEvent_keys_ignored_during_naming(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.namingNewSave = True

    screen.handleKeyDownEvent(pygame.K_DOWN)
    assert screen.scrollOffset == 0
    screen.handleKeyDownEvent(pygame.K_UP)
    assert screen.scrollOffset == 0


def test_createNewGameWithName_rejects_path_traversal(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    screen.createNewGameWithName("../escape")
    assert screen.changeScreen == False
    assert not os.path.exists(os.path.join(temp_saves_dir, "../escape"))


def test_createNewGameWithName_rejects_path_separator(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    screen.createNewGameWithName("sub/dir")
    assert screen.changeScreen == False


def test_createNewGameWithName_rejects_empty(temp_saves_dir):
    screen = createSaveSelectionScreen(temp_saves_dir)

    screen.createNewGameWithName("")
    assert screen.changeScreen == False


def test_deleteSave_rejects_outside_base(temp_saves_dir):
    outsidePath = os.path.join(temp_saves_dir, "..", "outside_save")
    os.makedirs(outsidePath, exist_ok=True)

    screen = createSaveSelectionScreen(temp_saves_dir)
    screen.deleteSave(outsidePath)

    assert os.path.exists(outsidePath)
    shutil.rmtree(outsidePath)
