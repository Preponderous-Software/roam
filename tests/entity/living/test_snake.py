# Use the production `entity.*` import root so prey class identities match the
# ones the Snake's diet references (see test_rabbit for the rationale).
from entity.grass import Grass
from entity.living.chicken import Chicken
from entity.living.rabbit import Rabbit
from entity.living.snake import Snake


def test_initialization():
    snake = Snake(0)

    assert snake.name == "Snake"
    assert snake.getTickCreated() == 0
    assert snake.getImagePath() == "assets/images/snake.png"
    assert snake.isSolid() == False


def test_can_eat_prey():
    snake = Snake(0)
    assert snake.canEat(Chicken(0)) is True
    assert snake.canEat(Rabbit(0)) is True


def test_cannot_eat_grass():
    snake = Snake(0)
    assert snake.canEat(Grass()) is False
