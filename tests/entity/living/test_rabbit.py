# Use the production `entity.*` import root (not `src.entity.*`) so the Grass
# class identity matches the one the Rabbit's diet references — the two roots
# resolve to distinct class objects and `canEat` compares by type identity.
from entity.grass import Grass
from entity.living.rabbit import Rabbit


def test_initialization():
    rabbit = Rabbit(0)

    assert rabbit.name == "Rabbit"
    assert rabbit.getTickCreated() == 0
    assert rabbit.getImagePath() == "assets/images/rabbit.png"
    assert rabbit.isSolid() == False


def test_can_eat_grass():
    rabbit = Rabbit(0)
    assert rabbit.canEat(Grass()) is True


def test_cannot_eat_non_food():
    rabbit = Rabbit(0)
    assert rabbit.canEat("test") is False
