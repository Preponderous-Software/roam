# Use the production `entity.*` import root so the Grass class identity matches
# the one the Deer's diet references (see test_rabbit for the rationale).
from entity.grass import Grass
from entity.living.deer import Deer


def test_initialization():
    deer = Deer(0)

    assert deer.name == "Deer"
    assert deer.getTickCreated() == 0
    assert deer.getImagePath() == "assets/images/deer.png"
    assert deer.isSolid() == False


def test_can_eat_grass():
    deer = Deer(0)
    assert deer.canEat(Grass()) is True


def test_cannot_eat_non_food():
    deer = Deer(0)
    assert deer.canEat("test") is False
