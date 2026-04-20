import pytest

from stats.stats import Stats


@pytest.fixture
def stats(resolve, test_config, tmp_path):
    test_config.pathToSaveDirectory = str(tmp_path)
    return resolve(Stats)


def test_initialization(stats):
    # call
    assert stats.getScore() == 0
    assert stats.getRoomsExplored() == 0
    assert stats.getFoodEaten() == 0
    assert stats.getNumberOfDeaths() == 0


def test_setScore(stats):
    # call
    stats.setScore(5)

    # check
    assert stats.getScore() == 5


def test_setRoomsExplored(stats):
    # call
    stats.setRoomsExplored(5)

    # check
    assert stats.getRoomsExplored() == 5


def test_setFoodEaten(stats):
    # call
    stats.setFoodEaten(5)

    # check
    assert stats.getFoodEaten() == 5


def test_setNumberOfDeaths(stats):
    # call
    stats.setNumberOfDeaths(5)

    # check
    assert stats.getNumberOfDeaths() == 5


def test_incrementScore(stats):
    # call
    stats.incrementScore()

    # check
    assert stats.getScore() == 1


def test_incrementRoomsExplored(stats):
    # call
    stats.incrementRoomsExplored()

    # check
    assert stats.getRoomsExplored() == 1


def test_incrementFoodEaten(stats):
    # call
    stats.incrementFoodEaten()

    # check
    assert stats.getFoodEaten() == 1


def test_incrementNumberOfDeaths(stats):
    # call
    stats.incrementNumberOfDeaths()

    # check
    assert stats.getNumberOfDeaths() == 1


def test_save(stats):
    stats.incrementScore()
    stats.incrementRoomsExplored()
    stats.incrementFoodEaten()
    stats.incrementNumberOfDeaths()

    # call
    stats.save()

    # check
    assert stats.getScore() == 1
    assert stats.getRoomsExplored() == 1
    assert stats.getFoodEaten() == 1
    assert stats.getNumberOfDeaths() == 1


def test_load(stats):
    stats.incrementScore()
    stats.incrementRoomsExplored()
    stats.incrementFoodEaten()
    stats.incrementNumberOfDeaths()

    # call
    stats.load()

    # check
    assert stats.getScore() == 1
    assert stats.getRoomsExplored() == 1
    assert stats.getFoodEaten() == 1
    assert stats.getNumberOfDeaths() == 1
