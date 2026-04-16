from src.entity.food import Food


def test_initialization():
    food = Food("test", "myimagepath.png", 20)

    assert food.getName() == "test"
    assert food.getImagePath() == "myimagepath.png"
    assert food.getEnergy() == 20


def test_set_energy():
    food = Food("test", "myimagepath.png", 20)

    food.setEnergy(50)
    assert food.getEnergy() == 50

    food.setEnergy(0)
    assert food.getEnergy() == 0


def test_set_energy_clamps_negative():
    food = Food("test", "myimagepath.png", 20)

    food.setEnergy(-10)
    assert food.getEnergy() == 0
