# Use the production `entity.*` import root so prey class identities match the
# ones the Wolf's diet references (see test_rabbit for the rationale).
from entity.grass import Grass
from entity.living.chicken import Chicken
from entity.living.deer import Deer
from entity.living.rabbit import Rabbit
from entity.living.wolf import Wolf


def test_initialization():
    wolf = Wolf(0)

    assert wolf.name == "Wolf"
    assert wolf.getTickCreated() == 0
    assert wolf.getImagePath() == "assets/images/wolf.png"
    assert wolf.isSolid() == False


def test_can_eat_prey():
    wolf = Wolf(0)
    assert wolf.canEat(Chicken(0)) is True
    assert wolf.canEat(Rabbit(0)) is True
    assert wolf.canEat(Deer(0)) is True


def test_cannot_eat_grass():
    wolf = Wolf(0)
    assert wolf.canEat(Grass()) is False
